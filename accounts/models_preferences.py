"""
Modelo de preferências de notificação para atendentes (Issue #39).
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class PreferenciasNotificacao(models.Model):
    """
    Preferências de notificação do atendente.
    
    Controla quando e como o atendente recebe alertas sonoros e visuais.
    """
    
    # Relacionamento
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='preferencias_notificacao',
        verbose_name=_("Usuário")
    )
    
    # Notificações sonoras
    som_nova_mensagem = models.BooleanField(
        default=True,
        verbose_name=_("Som - Nova Mensagem"),
        help_text=_("Tocar som ao receber nova mensagem")
    )
    
    som_novo_atendimento = models.BooleanField(
        default=True,
        verbose_name=_("Som - Novo Atendimento"),
        help_text=_("Tocar som ao receber novo atendimento")
    )
    
    som_transferencia = models.BooleanField(
        default=True,
        verbose_name=_("Som - Transferência"),
        help_text=_("Tocar som ao receber atendimento transferido")
    )
    
    # Notificações visuais (badge/desktop)
    desktop_nova_mensagem = models.BooleanField(
        default=True,
        verbose_name=_("Desktop - Nova Mensagem"),
        help_text=_("Mostrar notificação desktop para nova mensagem")
    )
    
    desktop_novo_atendimento = models.BooleanField(
        default=True,
        verbose_name=_("Desktop - Novo Atendimento")
    )
    
    desktop_transferencia = models.BooleanField(
        default=True,
        verbose_name=_("Desktop - Transferência")
    )
    
    # Badge/contador
    mostrar_badge_mensagens = models.BooleanField(
        default=True,
        verbose_name=_("Badge de Mensagens"),
        help_text=_("Mostrar contador de mensagens não lidas")
    )
    
    mostrar_badge_atendimentos = models.BooleanField(
        default=True,
        verbose_name=_("Badge de Atendimentos"),
        help_text=_("Mostrar contador de atendimentos pendentes")
    )
    
    # Modo não perturbe
    modo_nao_perturbe = models.BooleanField(
        default=False,
        verbose_name=_("Modo Não Perturbe"),
        help_text=_("Desabilita todas as notificações sonoras")
    )
    
    nao_perturbe_inicio = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Não Perturbe - Início"),
        help_text=_("Horário de início (ex: 22:00)")
    )
    
    nao_perturbe_fim = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Não Perturbe - Fim"),
        help_text=_("Horário de fim (ex: 08:00)")
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
        verbose_name = _("Preferências de Notificação")
        verbose_name_plural = _("Preferências de Notificação")
    
    def __str__(self) -> str:
        return f"Preferências de {self.usuario.username}"
    
    @property
    def esta_em_nao_perturbe(self) -> bool:
        """Verifica se está no horário de não perturbe"""
        if not self.modo_nao_perturbe or not self.nao_perturbe_inicio or not self.nao_perturbe_fim:
            return False
        
        from django.utils import timezone
        agora = timezone.localtime().time()
        
        # Se horário de fim é menor que início (ex: 22:00 às 08:00)
        if self.nao_perturbe_fim < self.nao_perturbe_inicio:
            return agora >= self.nao_perturbe_inicio or agora <= self.nao_perturbe_fim
        else:
            return self.nao_perturbe_inicio <= agora <= self.nao_perturbe_fim
    
    def deve_tocar_som(self, tipo_evento: str) -> bool:
        """
        Verifica se deve tocar som para um tipo de evento.
        
        Args:
            tipo_evento: 'nova_mensagem', 'novo_atendimento', 'transferencia'
        
        Returns:
            True se deve tocar som
        """
        if self.esta_em_nao_perturbe:
            return False
        
        mapeamento = {
            'nova_mensagem': self.som_nova_mensagem,
            'novo_atendimento': self.som_novo_atendimento,
            'transferencia': self.som_transferencia,
        }
        
        return mapeamento.get(tipo_evento, False)
    
    def deve_mostrar_desktop(self, tipo_evento: str) -> bool:
        """
        Verifica se deve mostrar notificação desktop.
        
        Args:
            tipo_evento: 'nova_mensagem', 'novo_atendimento', 'transferencia'
        
        Returns:
            True se deve mostrar
        """
        mapeamento = {
            'nova_mensagem': self.desktop_nova_mensagem,
            'novo_atendimento': self.desktop_novo_atendimento,
            'transferencia': self.desktop_transferencia,
        }
        
        return mapeamento.get(tipo_evento, False)

