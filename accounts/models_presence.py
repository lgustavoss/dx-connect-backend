"""
Modelo de presença de atendentes (Issue #51).

Controla status online/offline/ocupado e indicadores de digitação.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta


class AgentPresence(models.Model):
    """
    Controle de presença e status dos atendentes.
    
    Estados:
    - online: Disponível para atender
    - offline: Desconectado
    - busy: Ocupado (não receber novos atendimentos)
    - away: Ausente temporariamente
    """
    
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('busy', 'Ocupado'),
        ('away', 'Ausente'),
    ]
    
    # Relacionamento
    agent = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='presence',
        verbose_name=_("Agente")
    )
    
    # Status
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='offline',
        verbose_name=_("Status"),
        db_index=True
    )
    
    # Mensagem de status personalizada
    status_message = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Mensagem de Status"),
        help_text=_("Ex: 'Em reunião até 15h'")
    )
    
    # Heartbeat (para detectar desconexão)
    last_heartbeat = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Último Heartbeat"),
        db_index=True
    )
    
    # Sessão WebSocket
    websocket_connected = models.BooleanField(
        default=False,
        verbose_name=_("WebSocket Conectado")
    )
    
    # Timestamps
    status_changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Status Alterado em"),
        db_index=True
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Criado em")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Atualizado em")
    )
    
    class Meta:
        verbose_name = _("Presença de Agente")
        verbose_name_plural = _("Presenças de Agentes")
    
    def __str__(self) -> str:
        return f"{self.agent.username} - {self.get_status_display()}"
    
    @property
    def is_available(self) -> bool:
        """Verifica se está disponível para novos atendimentos"""
        return self.status == 'online' and self.websocket_connected
    
    @property
    def tempo_no_status_atual(self) -> int:
        """Retorna tempo no status atual em minutos"""
        delta = timezone.now() - self.status_changed_at
        return int(delta.total_seconds() / 60)
    
    @property
    def esta_inativo(self) -> bool:
        """Verifica se está inativo (sem heartbeat há mais de 2 minutos)"""
        if not self.last_heartbeat:
            return True
        
        timeout = timezone.now() - timedelta(minutes=2)
        return self.last_heartbeat < timeout
    
    def set_status(self, new_status: str, message: str = ''):
        """Altera status e registra timestamp"""
        if new_status != self.status:
            self.status = new_status
            self.status_changed_at = timezone.now()
        
        if message:
            self.status_message = message
        
        self.save(update_fields=['status', 'status_message', 'status_changed_at', 'updated_at'])
    
    def heartbeat(self):
        """Atualiza heartbeat (mantém sessão ativa)"""
        self.last_heartbeat = timezone.now()
        
        # Se estava offline, marca como online
        if self.status == 'offline' and self.websocket_connected:
            self.set_status('online')
        else:
            self.save(update_fields=['last_heartbeat', 'updated_at'])
    
    def mark_as_offline(self):
        """Marca como offline"""
        self.status = 'offline'
        self.websocket_connected = False
        self.status_changed_at = timezone.now()
        self.save(update_fields=['status', 'websocket_connected', 'status_changed_at', 'updated_at'])


class TypingIndicator(models.Model):
    """
    Indicador de digitação em tempo real.
    
    Registra quando um atendente está digitando em um chat.
    """
    
    # Relacionamentos
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='typing_indicators',
        verbose_name=_("Agente")
    )
    
    chat_id = models.CharField(
        max_length=100,
        verbose_name=_("ID do Chat"),
        db_index=True
    )
    
    # Estado
    is_typing = models.BooleanField(
        default=False,
        verbose_name=_("Está Digitando")
    )
    
    # Timestamps
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Começou a Digitar em")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Atualizado em")
    )
    
    class Meta:
        verbose_name = _("Indicador de Digitação")
        verbose_name_plural = _("Indicadores de Digitação")
        unique_together = [['agent', 'chat_id']]
        indexes = [
            models.Index(fields=['chat_id', 'is_typing']),
        ]
    
    def __str__(self) -> str:
        status = "digitando" if self.is_typing else "parou de digitar"
        return f"{self.agent.username} {status} em {self.chat_id}"
    
    @property
    def esta_digitando_ha_muito_tempo(self) -> bool:
        """Verifica se está digitando há mais de 30 segundos (possível travamento)"""
        if not self.is_typing:
            return False
        
        timeout = timezone.now() - timedelta(seconds=30)
        return self.updated_at < timeout

