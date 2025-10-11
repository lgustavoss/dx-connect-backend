"""
Modelos para sistema de filas de atendimento (Issue #37).

Gerencia departamentos, filas e distribuição automática de atendimentos.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q


class Departamento(models.Model):
    """
    Departamento para organização de filas de atendimento.
    
    Exemplos: Vendas, Suporte, Financeiro, RH, etc.
    """
    
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Nome"),
        help_text=_("Nome do departamento")
    )
    
    descricao = models.TextField(
        blank=True,
        verbose_name=_("Descrição")
    )
    
    cor = models.CharField(
        max_length=7,
        default='#3B82F6',
        verbose_name=_("Cor"),
        help_text=_("Cor no formato hexadecimal (ex: #3B82F6)")
    )
    
    # Atendentes do departamento
    atendentes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='departamentos',
        blank=True,
        verbose_name=_("Atendentes")
    )
    
    # Configurações
    max_atendimentos_simultaneos = models.IntegerField(
        default=5,
        verbose_name=_("Máximo de Atendimentos Simultâneos"),
        help_text=_("Número máximo de atendimentos que cada atendente pode ter ao mesmo tempo")
    )
    
    tempo_resposta_esperado_minutos = models.IntegerField(
        default=15,
        verbose_name=_("Tempo de Resposta Esperado (minutos)"),
        help_text=_("SLA de tempo de resposta")
    )
    
    # Flags
    ativo = models.BooleanField(
        default=True,
        verbose_name=_("Ativo"),
        db_index=True
    )
    
    # Timestamps
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Criado em")
    )
    
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Atualizado em")
    )
    
    class Meta:
        verbose_name = _("Departamento")
        verbose_name_plural = _("Departamentos")
        ordering = ['nome']
    
    def __str__(self) -> str:
        return self.nome
    
    def get_atendentes_disponiveis(self):
        """Retorna atendentes disponíveis (online e com capacidade)"""
        from django.db.models import Count
        
        return self.atendentes.filter(
            is_active=True
        ).annotate(
            atendimentos_ativos=Count(
                'atendimentos_atendente',
                filter=Q(atendimentos_atendente__status__in=['aguardando', 'em_atendimento'])
            )
        ).filter(
            atendimentos_ativos__lt=self.max_atendimentos_simultaneos
        )


class FilaAtendimento(models.Model):
    """
    Fila de espera para atendimento.
    
    Cada entrada representa um cliente aguardando atendimento.
    """
    
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    # Identificação
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.CASCADE,
        related_name='fila',
        verbose_name=_("Departamento")
    )
    
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='filas_atendimento',
        verbose_name=_("Cliente")
    )
    
    # Contexto da conversa
    chat_id = models.CharField(
        max_length=100,
        verbose_name=_("ID do Chat"),
        help_text=_("ID do chat no WhatsApp"),
        db_index=True
    )
    
    numero_whatsapp = models.CharField(
        max_length=20,
        verbose_name=_("Número WhatsApp")
    )
    
    mensagem_inicial = models.TextField(
        blank=True,
        verbose_name=_("Mensagem Inicial"),
        help_text=_("Primeira mensagem que gerou o atendimento")
    )
    
    # Prioridade
    prioridade = models.CharField(
        max_length=10,
        choices=PRIORIDADE_CHOICES,
        default='normal',
        verbose_name=_("Prioridade"),
        db_index=True
    )
    
    # Timestamps
    entrou_na_fila_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Entrou na Fila em"),
        db_index=True
    )
    
    atribuido_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Atribuído em")
    )
    
    class Meta:
        verbose_name = _("Fila de Atendimento")
        verbose_name_plural = _("Filas de Atendimento")
        ordering = ['-prioridade', 'entrou_na_fila_em']  # Prioridade desc, FIFO asc
        indexes = [
            models.Index(fields=['departamento', 'atribuido_em']),
            models.Index(fields=['prioridade', 'entrou_na_fila_em']),
        ]
    
    def __str__(self) -> str:
        return f"Fila {self.departamento.nome} - {self.cliente.razao_social}"
    
    @property
    def tempo_espera_minutos(self) -> int:
        """Calcula tempo de espera na fila em minutos"""
        if self.atribuido_em:
            delta = self.atribuido_em - self.entrou_na_fila_em
        else:
            delta = timezone.now() - self.entrou_na_fila_em
        
        return int(delta.total_seconds() / 60)
    
    @property
    def esta_atrasado(self) -> bool:
        """Verifica se ultrapassou o SLA do departamento"""
        return self.tempo_espera_minutos > self.departamento.tempo_resposta_esperado_minutos


class Atendimento(models.Model):
    """
    Atendimento ativo entre atendente e cliente.
    
    Representa um chat em andamento.
    """
    
    STATUS_CHOICES = [
        ('aguardando', 'Aguardando Atendente'),
        ('em_atendimento', 'Em Atendimento'),
        ('pausado', 'Pausado'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
    ]
    
    # Relacionamentos
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.CASCADE,
        related_name='atendimentos',
        verbose_name=_("Departamento")
    )
    
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='atendimentos',
        verbose_name=_("Cliente")
    )
    
    atendente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='atendimentos_atendente',
        verbose_name=_("Atendente")
    )
    
    # Contexto
    chat_id = models.CharField(
        max_length=100,
        verbose_name=_("ID do Chat"),
        db_index=True
    )
    
    numero_whatsapp = models.CharField(
        max_length=20,
        verbose_name=_("Número WhatsApp")
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='aguardando',
        verbose_name=_("Status"),
        db_index=True
    )
    
    prioridade = models.CharField(
        max_length=10,
        choices=FilaAtendimento.PRIORIDADE_CHOICES,
        default='normal',
        verbose_name=_("Prioridade")
    )
    
    # Métricas
    tempo_primeira_resposta_segundos = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Tempo de Primeira Resposta (segundos)")
    )
    
    tempo_total_atendimento_segundos = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Tempo Total de Atendimento (segundos)")
    )
    
    total_mensagens_cliente = models.IntegerField(
        default=0,
        verbose_name=_("Total de Mensagens do Cliente")
    )
    
    total_mensagens_atendente = models.IntegerField(
        default=0,
        verbose_name=_("Total de Mensagens do Atendente")
    )
    
    # Avaliação (opcional)
    avaliacao = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Avaliação"),
        help_text=_("Nota de 1 a 5")
    )
    
    comentario_avaliacao = models.TextField(
        blank=True,
        verbose_name=_("Comentário da Avaliação")
    )
    
    # Observações
    observacoes = models.TextField(
        blank=True,
        verbose_name=_("Observações Internas"),
        help_text=_("Notas do atendente sobre o atendimento")
    )
    
    # Timestamps
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Criado em"),
        db_index=True
    )
    
    iniciado_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Iniciado em")
    )
    
    primeira_resposta_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Primeira Resposta em")
    )
    
    finalizado_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Finalizado em")
    )
    
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Atualizado em")
    )
    
    class Meta:
        verbose_name = _("Atendimento")
        verbose_name_plural = _("Atendimentos")
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['status', 'criado_em']),
            models.Index(fields=['atendente', 'status']),
            models.Index(fields=['departamento', 'status']),
            models.Index(fields=['chat_id']),
        ]
    
    def __str__(self) -> str:
        atendente_nome = self.atendente.username if self.atendente else "Não atribuído"
        return f"Atendimento #{self.id} - {self.cliente.razao_social} ({atendente_nome})"
    
    @property
    def tempo_espera_minutos(self) -> int:
        """Tempo de espera até ser atribuído"""
        if not self.iniciado_em:
            delta = timezone.now() - self.criado_em
        else:
            delta = self.iniciado_em - self.criado_em
        return int(delta.total_seconds() / 60)
    
    @property
    def duracao_minutos(self) -> int:
        """Duração total do atendimento em minutos"""
        if not self.iniciado_em:
            return 0
        
        end_time = self.finalizado_em or timezone.now()
        delta = end_time - self.iniciado_em
        return int(delta.total_seconds() / 60)
    
    @property
    def esta_ativo(self) -> bool:
        """Verifica se atendimento está ativo"""
        return self.status in ['aguardando', 'em_atendimento', 'pausado']
    
    def atribuir_atendente(self, atendente):
        """Atribui atendente e marca como iniciado"""
        self.atendente = atendente
        self.status = 'em_atendimento'
        self.iniciado_em = timezone.now()
        self.save(update_fields=['atendente', 'status', 'iniciado_em', 'atualizado_em'])
    
    def marcar_primeira_resposta(self):
        """Marca timestamp da primeira resposta do atendente"""
        if not self.primeira_resposta_em:
            self.primeira_resposta_em = timezone.now()
            if self.iniciado_em:
                delta = self.primeira_resposta_em - self.iniciado_em
                self.tempo_primeira_resposta_segundos = int(delta.total_seconds())
            self.save(update_fields=['primeira_resposta_em', 'tempo_primeira_resposta_segundos', 'atualizado_em'])
    
    def finalizar(self, observacoes: str = ''):
        """Finaliza o atendimento"""
        self.status = 'finalizado'
        self.finalizado_em = timezone.now()
        if observacoes:
            self.observacoes = observacoes
        
        # Calcula tempo total
        if self.iniciado_em:
            delta = self.finalizado_em - self.iniciado_em
            self.tempo_total_atendimento_segundos = int(delta.total_seconds())
        
        self.save(update_fields=['status', 'finalizado_em', 'observacoes', 'tempo_total_atendimento_segundos', 'atualizado_em'])
    
    def cancelar(self, motivo: str = ''):
        """Cancela o atendimento"""
        self.status = 'cancelado'
        self.finalizado_em = timezone.now()
        self.observacoes = f"Cancelado: {motivo}"
        self.save(update_fields=['status', 'finalizado_em', 'observacoes', 'atualizado_em'])
    
    def incrementar_mensagens_cliente(self):
        """Incrementa contador de mensagens do cliente"""
        self.total_mensagens_cliente += 1
        self.save(update_fields=['total_mensagens_cliente', 'atualizado_em'])
    
    def incrementar_mensagens_atendente(self):
        """Incrementa contador de mensagens do atendente"""
        self.total_mensagens_atendente += 1
        
        # Marca primeira resposta se ainda não foi marcada
        if not self.primeira_resposta_em:
            self.marcar_primeira_resposta()
        else:
            self.save(update_fields=['total_mensagens_atendente', 'atualizado_em'])

