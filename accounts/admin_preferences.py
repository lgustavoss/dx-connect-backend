from django.contrib import admin
from .models_preferences import PreferenciasNotificacao


@admin.register(PreferenciasNotificacao)
class PreferenciasNotificacaoAdmin(admin.ModelAdmin):
    list_display = [
        'usuario', 'som_nova_mensagem', 'som_novo_atendimento',
        'desktop_nova_mensagem', 'modo_nao_perturbe', 'atualizado_em'
    ]
    list_filter = ['modo_nao_perturbe', 'som_nova_mensagem', 'desktop_nova_mensagem']
    search_fields = ['usuario__username', 'usuario__email']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Usuário', {
            'fields': ('usuario',)
        }),
        ('Notificações Sonoras', {
            'fields': ('som_nova_mensagem', 'som_novo_atendimento', 'som_transferencia')
        }),
        ('Notificações Desktop', {
            'fields': ('desktop_nova_mensagem', 'desktop_novo_atendimento', 'desktop_transferencia')
        }),
        ('Badges', {
            'fields': ('mostrar_badge_mensagens', 'mostrar_badge_atendimentos')
        }),
        ('Modo Não Perturbe', {
            'fields': ('modo_nao_perturbe', 'nao_perturbe_inicio', 'nao_perturbe_fim'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em')
        }),
    )

