"""
Serializers para preferências de notificação (Issue #39).
"""
from rest_framework import serializers
from .models_preferences import PreferenciasNotificacao


class PreferenciasNotificacaoSerializer(serializers.ModelSerializer):
    """Serializer para preferências de notificação"""
    esta_em_nao_perturbe = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PreferenciasNotificacao
        fields = [
            'id', 'usuario', 'som_nova_mensagem', 'som_novo_atendimento',
            'som_transferencia', 'desktop_nova_mensagem', 'desktop_novo_atendimento',
            'desktop_transferencia', 'mostrar_badge_mensagens', 'mostrar_badge_atendimentos',
            'modo_nao_perturbe', 'nao_perturbe_inicio', 'nao_perturbe_fim',
            'esta_em_nao_perturbe', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'usuario', 'criado_em', 'atualizado_em']

