from __future__ import annotations

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class WhatsAppSession(models.Model):
    """
    Modelo para gerenciar sessões do WhatsApp Web.
    
    Uma sessão representa uma conexão ativa do WhatsApp Web e seu ciclo de vida:
    - disconnected: Sessão não iniciada ou desconectada
    - connecting: Tentando estabelecer conexão
    - qrcode: Aguardando leitura do QR Code
    - authenticated: QR Code lido, autenticando
    - ready: Sessão ativa e pronta para enviar/receber mensagens
    - error: Erro na sessão
    """
    
    STATUS_CHOICES = [
        ('disconnected', 'Desconectado'),
        ('connecting', 'Conectando'),
        ('qrcode', 'Aguardando QR Code'),
        ('authenticated', 'Autenticado'),
        ('ready', 'Pronto'),
        ('error', 'Erro'),
    ]
    
    # Relacionamentos
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='whatsapp_sessions',
        verbose_name=_("Usuário"),
        help_text=_("Usuário responsável pela sessão")
    )
    
    # Status e metadados
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='disconnected',
        verbose_name=_("Status"),
        db_index=True
    )
    
    device_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Nome do Dispositivo"),
        help_text=_("Nome do dispositivo conectado")
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Número de Telefone"),
        help_text=_("Número do WhatsApp conectado")
    )
    
    # QR Code (se disponível)
    qr_code = models.TextField(
        blank=True,
        verbose_name=_("QR Code"),
        help_text=_("QR Code em base64 para autenticação")
    )
    
    # Dados de sessão criptografados (opcional)
    session_data = models.TextField(
        blank=True,
        verbose_name=_("Dados de Sessão"),
        help_text=_("Dados criptografados da sessão para reconexão")
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Criado em")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Atualizado em"),
        db_index=True
    )
    
    connected_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Conectado em"),
        help_text=_("Data e hora da última conexão bem-sucedida")
    )
    
    disconnected_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Desconectado em"),
        help_text=_("Data e hora da última desconexão")
    )
    
    # Métricas
    total_messages_sent = models.IntegerField(
        default=0,
        verbose_name=_("Total de Mensagens Enviadas")
    )
    
    total_messages_received = models.IntegerField(
        default=0,
        verbose_name=_("Total de Mensagens Recebidas")
    )
    
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Última Mensagem em"),
        help_text=_("Data e hora da última mensagem enviada ou recebida")
    )
    
    # Error tracking
    last_error = models.TextField(
        blank=True,
        verbose_name=_("Último Erro"),
        help_text=_("Descrição do último erro ocorrido")
    )
    
    error_count = models.IntegerField(
        default=0,
        verbose_name=_("Contagem de Erros"),
        help_text=_("Número de erros desde a última conexão")
    )
    
    # Flags
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Ativo"),
        db_index=True
    )
    
    class Meta:
        verbose_name = _("Sessão WhatsApp")
        verbose_name_plural = _("Sessões WhatsApp")
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['usuario', 'status']),
            models.Index(fields=['status', 'is_active']),
        ]
    
    def __str__(self) -> str:
        return f"WhatsApp Session - {self.usuario.username} ({self.get_status_display()})"
    
    @property
    def is_connected(self) -> bool:
        """Verifica se a sessão está conectada e pronta"""
        return self.status == 'ready' and self.is_active
    
    @property
    def uptime_seconds(self) -> int | None:
        """Retorna o tempo de atividade em segundos desde a última conexão"""
        if not self.connected_at or self.status != 'ready':
            return None
        return int((timezone.now() - self.connected_at).total_seconds())
    
    def mark_as_connected(self) -> None:
        """Marca a sessão como conectada"""
        self.status = 'ready'
        self.connected_at = timezone.now()
        self.error_count = 0
        self.last_error = ''
        self.save(update_fields=['status', 'connected_at', 'error_count', 'last_error', 'updated_at'])
    
    def mark_as_disconnected(self) -> None:
        """Marca a sessão como desconectada"""
        self.status = 'disconnected'
        self.disconnected_at = timezone.now()
        self.save(update_fields=['status', 'disconnected_at', 'updated_at'])
    
    def mark_as_error(self, error_message: str) -> None:
        """Marca a sessão com erro"""
        self.status = 'error'
        self.last_error = error_message
        self.error_count += 1
        self.save(update_fields=['status', 'last_error', 'error_count', 'updated_at'])
    
    def increment_sent_messages(self) -> None:
        """Incrementa contador de mensagens enviadas"""
        self.total_messages_sent += 1
        self.last_message_at = timezone.now()
        self.save(update_fields=['total_messages_sent', 'last_message_at', 'updated_at'])
    
    def increment_received_messages(self) -> None:
        """Incrementa contador de mensagens recebidas"""
        self.total_messages_received += 1
        self.last_message_at = timezone.now()
        self.save(update_fields=['total_messages_received', 'last_message_at', 'updated_at'])


class WhatsAppMessage(models.Model):
    """
    Modelo para armazenar mensagens enviadas e recebidas via WhatsApp.
    
    Armazena histórico completo de mensagens com métricas de latência.
    """
    
    DIRECTION_CHOICES = [
        ('inbound', 'Recebida'),
        ('outbound', 'Enviada'),
    ]
    
    STATUS_CHOICES = [
        ('queued', 'Na Fila'),
        ('sent', 'Enviada'),
        ('delivered', 'Entregue'),
        ('read', 'Lida'),
        ('failed', 'Falhou'),
        ('error', 'Erro'),
    ]
    
    TYPE_CHOICES = [
        ('text', 'Texto'),
        ('image', 'Imagem'),
        ('audio', 'Áudio'),
        ('video', 'Vídeo'),
        ('document', 'Documento'),
        ('location', 'Localização'),
        ('contact', 'Contato'),
        ('sticker', 'Sticker'),
    ]
    
    # Relacionamentos
    session = models.ForeignKey(
        WhatsAppSession,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_("Sessão"),
        db_index=True
    )
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='whatsapp_messages',
        verbose_name=_("Usuário"),
        help_text=_("Usuário responsável pela mensagem")
    )
    
    # Identificadores
    message_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("ID da Mensagem"),
        help_text=_("ID único da mensagem no WhatsApp"),
        db_index=True
    )
    
    client_message_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("ID do Cliente"),
        help_text=_("ID gerado pelo cliente para rastreamento")
    )
    
    # Direção e tipo
    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        verbose_name=_("Direção"),
        db_index=True
    )
    
    message_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='text',
        verbose_name=_("Tipo de Mensagem")
    )
    
    # Contato
    chat_id = models.CharField(
        max_length=100,
        verbose_name=_("ID do Chat"),
        help_text=_("ID do chat/conversa no WhatsApp"),
        db_index=True
    )
    
    contact_number = models.CharField(
        max_length=20,
        verbose_name=_("Número do Contato"),
        help_text=_("Número de telefone do remetente/destinatário")
    )
    
    contact_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Nome do Contato"),
        help_text=_("Nome salvo do contato")
    )
    
    # Conteúdo
    text_content = models.TextField(
        blank=True,
        verbose_name=_("Conteúdo de Texto")
    )
    
    media_url = models.URLField(
        blank=True,
        max_length=500,
        verbose_name=_("URL da Mídia")
    )
    
    media_mime_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Tipo MIME da Mídia")
    )
    
    media_size = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Tamanho da Mídia (bytes)")
    )
    
    # Payload completo (para dados adicionais)
    payload = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Payload Completo"),
        help_text=_("Dados completos da mensagem em formato JSON")
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='queued',
        verbose_name=_("Status"),
        db_index=True
    )
    
    # Timestamps para métricas de latência
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Criado em"),
        db_index=True
    )
    
    queued_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Na Fila em")
    )
    
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Enviado em")
    )
    
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Entregue em")
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Lido em")
    )
    
    # Erro
    error_message = models.TextField(
        blank=True,
        verbose_name=_("Mensagem de Erro")
    )
    
    # Flags
    is_from_me = models.BooleanField(
        default=False,
        verbose_name=_("De Mim"),
        help_text=_("Indica se a mensagem foi enviada pelo usuário autenticado")
    )
    
    class Meta:
        verbose_name = _("Mensagem WhatsApp")
        verbose_name_plural = _("Mensagens WhatsApp")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['chat_id', 'created_at']),
            models.Index(fields=['direction', 'status']),
            models.Index(fields=['usuario', 'created_at']),
        ]
    
    def __str__(self) -> str:
        direction_str = "Recebida de" if self.direction == 'inbound' else "Enviada para"
        return f"{direction_str} {self.contact_number} - {self.message_type} ({self.get_status_display()})"
    
    @property
    def latency_to_sent_ms(self) -> int | None:
        """Latência desde criação até envio (em milissegundos)"""
        if not self.sent_at:
            return None
        delta = self.sent_at - self.queued_at
        return int(delta.total_seconds() * 1000)
    
    @property
    def latency_to_delivered_ms(self) -> int | None:
        """Latência desde criação até entrega (em milissegundos)"""
        if not self.delivered_at:
            return None
        delta = self.delivered_at - self.queued_at
        return int(delta.total_seconds() * 1000)
    
    @property
    def latency_to_read_ms(self) -> int | None:
        """Latência desde criação até leitura (em milissegundos)"""
        if not self.read_at:
            return None
        delta = self.read_at - self.queued_at
        return int(delta.total_seconds() * 1000)
    
    @property
    def total_latency_ms(self) -> int | None:
        """Latência total (da criação até o status mais recente) em milissegundos"""
        latest_timestamp = self.read_at or self.delivered_at or self.sent_at
        if not latest_timestamp:
            return None
        delta = latest_timestamp - self.queued_at
        return int(delta.total_seconds() * 1000)
    
    @property
    def is_latency_acceptable(self) -> bool:
        """Verifica se a latência está dentro do limite de 5 segundos (5000ms)"""
        if self.direction == 'inbound':
            # Para mensagens recebidas, considera a latência desde a criação
            latency = self.total_latency_ms
        else:
            # Para mensagens enviadas, considera a latência até envio
            latency = self.latency_to_sent_ms
        
        if latency is None:
            return True  # Se não tem latência calculada, considera aceitável
        
        return latency < 5000  # < 5 segundos
    
    def mark_as_sent(self) -> None:
        """Marca mensagem como enviada"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_as_delivered(self) -> None:
        """Marca mensagem como entregue"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])
    
    def mark_as_read(self) -> None:
        """Marca mensagem como lida"""
        self.status = 'read'
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at'])
    
    def mark_as_error(self, error_msg: str) -> None:
        """Marca mensagem com erro"""
        self.status = 'error'
        self.error_message = error_msg
        self.save(update_fields=['status', 'error_message'])

