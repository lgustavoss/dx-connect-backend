"""
Serializers para API de Chats (Issue #85).

Agrupa mensagens e atendimentos em conversas únicas por chat_id.
"""
from rest_framework import serializers
from django.db.models import Q, Max, Count
from django.utils import timezone

from atendimento.models import Atendimento
from whatsapp.models import WhatsAppMessage
from clientes.models import Cliente


class ChatListSerializer(serializers.Serializer):
    """
    Serializer para listagem de chats com informações resumidas.
    
    Agrega dados de Atendimento + última mensagem.
    """
    # Identificação
    chat_id = serializers.CharField()
    numero_whatsapp = serializers.CharField()
    
    # Cliente
    cliente_id = serializers.IntegerField(allow_null=True)
    cliente_nome = serializers.CharField(allow_null=True)
    cliente_email = serializers.CharField(allow_null=True)
    
    # Atendimento atual
    atendimento_id = serializers.IntegerField(allow_null=True)
    status = serializers.CharField()
    prioridade = serializers.CharField()
    
    # Atendente
    atendente_id = serializers.IntegerField(allow_null=True)
    atendente_nome = serializers.CharField(allow_null=True)
    
    # Departamento
    departamento_id = serializers.IntegerField(allow_null=True)
    departamento_nome = serializers.CharField(allow_null=True)
    
    # Última mensagem
    ultima_mensagem_texto = serializers.CharField(allow_null=True)
    ultima_mensagem_em = serializers.DateTimeField(allow_null=True)
    ultima_mensagem_tipo = serializers.CharField(allow_null=True)
    ultima_mensagem_direcao = serializers.CharField(allow_null=True)
    
    # Contadores
    total_mensagens = serializers.IntegerField(default=0)
    mensagens_nao_lidas = serializers.IntegerField(default=0)
    
    # Timestamps
    criado_em = serializers.DateTimeField(allow_null=True)
    atualizado_em = serializers.DateTimeField(allow_null=True)


class ChatDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detalhado de um chat (baseado no Atendimento).
    """
    # Cliente
    cliente_nome = serializers.CharField(source='cliente.razao_social', read_only=True)
    cliente_email = serializers.CharField(source='cliente.email_principal', read_only=True)
    cliente_telefone = serializers.CharField(source='cliente.telefone_principal', read_only=True)
    
    # Atendente
    atendente_nome = serializers.CharField(source='atendente.display_name', read_only=True, allow_null=True)
    atendente_username = serializers.CharField(source='atendente.username', read_only=True, allow_null=True)
    
    # Departamento
    departamento_nome = serializers.CharField(source='departamento.nome', read_only=True)
    departamento_cor = serializers.CharField(source='departamento.cor', read_only=True)
    
    # Métricas calculadas
    duracao_minutos = serializers.SerializerMethodField()
    tempo_primeira_resposta_minutos = serializers.SerializerMethodField()
    
    # Contadores de mensagens
    total_mensagens = serializers.SerializerMethodField()
    mensagens_nao_lidas = serializers.SerializerMethodField()
    
    class Meta:
        model = Atendimento
        fields = [
            'id', 'chat_id', 'numero_whatsapp',
            'status', 'prioridade',
            # Cliente
            'cliente', 'cliente_nome', 'cliente_email', 'cliente_telefone',
            # Atendente
            'atendente', 'atendente_nome', 'atendente_username',
            # Departamento
            'departamento', 'departamento_nome', 'departamento_cor',
            # Métricas
            'duracao_minutos', 'tempo_primeira_resposta_minutos',
            'total_mensagens_cliente', 'total_mensagens_atendente',
            'total_mensagens', 'mensagens_nao_lidas',
            # Avaliação
            'avaliacao', 'comentario_avaliacao',
            # Observações
            'observacoes',
            # Timestamps
            'criado_em', 'iniciado_em', 'primeira_resposta_em',
            'finalizado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']
    
    def get_duracao_minutos(self, obj):
        """Calcula duração do atendimento em minutos"""
        if obj.finalizado_em:
            delta = obj.finalizado_em - obj.criado_em
        else:
            delta = timezone.now() - obj.criado_em
        return int(delta.total_seconds() / 60)
    
    def get_tempo_primeira_resposta_minutos(self, obj):
        """Retorna tempo de primeira resposta em minutos"""
        if obj.tempo_primeira_resposta_segundos:
            return int(obj.tempo_primeira_resposta_segundos / 60)
        return None
    
    def get_total_mensagens(self, obj):
        """Total de mensagens do chat atual"""
        return WhatsAppMessage.objects.filter(
            chat_id=obj.chat_id,
            created_at__gte=obj.criado_em
        ).count()
    
    def get_mensagens_nao_lidas(self, obj):
        """
        Conta mensagens não lidas (recebidas após última mensagem do atendente).
        """
        ultima_msg_atendente = WhatsAppMessage.objects.filter(
            chat_id=obj.chat_id,
            direction='outbound',
            created_at__gte=obj.criado_em
        ).aggregate(Max('created_at'))['created_at__max']
        
        if not ultima_msg_atendente:
            # Se atendente nunca respondeu, conta todas as mensagens do cliente
            return WhatsAppMessage.objects.filter(
                chat_id=obj.chat_id,
                direction='inbound',
                created_at__gte=obj.criado_em
            ).count()
        
        # Conta mensagens do cliente após última resposta do atendente
        return WhatsAppMessage.objects.filter(
            chat_id=obj.chat_id,
            direction='inbound',
            created_at__gt=ultima_msg_atendente
        ).count()


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Serializer para mensagens de um chat específico.
    """
    # Informações do remetente
    from_name = serializers.SerializerMethodField()
    is_from_agent = serializers.SerializerMethodField()
    
    # Latência
    latency_ms = serializers.IntegerField(source='total_latency_ms', read_only=True)
    is_latency_ok = serializers.BooleanField(source='is_latency_acceptable', read_only=True)
    
    class Meta:
        model = WhatsAppMessage
        fields = [
            'id', 'message_id', 'direction', 'message_type',
            'chat_id', 'contact_number', 'contact_name',
            'text_content', 'media_url', 'media_mime_type',
            'status', 'is_from_me',
            'from_name', 'is_from_agent',
            'latency_ms', 'is_latency_ok',
            'created_at', 'queued_at', 'sent_at', 'delivered_at', 'read_at'
        ]
        read_only_fields = fields
    
    def get_from_name(self, obj):
        """Retorna nome do remetente"""
        if obj.direction == 'outbound':
            # Mensagem enviada pelo atendente
            if obj.usuario:
                return obj.usuario.display_name or obj.usuario.username
            return 'Sistema'
        else:
            # Mensagem recebida do cliente
            return obj.contact_name or obj.contact_number
    
    def get_is_from_agent(self, obj):
        """Indica se mensagem é do atendente"""
        # Mensagem é do agente se:
        # 1. Direction é outbound (enviada pelo agente)
        # 2. Direction é inbound mas is_from_me é True (agente simulando cliente)
        # 3. Contact_number é 'agent_system' (identificador especial)
        return (
            obj.direction == 'outbound' or 
            obj.is_from_me or 
            obj.contact_number == 'agent_system' or
            (obj.payload and obj.payload.get('sender_type') == 'agent')
        )


class AceitarChatSerializer(serializers.Serializer):
    """Serializer para ação de aceitar um chat"""
    atendente_id = serializers.IntegerField(required=False, help_text="ID do atendente (opcional, usa o usuário atual se não fornecido)")
    observacoes = serializers.CharField(required=False, allow_blank=True, help_text="Observações iniciais")


class TransferirChatSerializer(serializers.Serializer):
    """Serializer para transferência de chat"""
    atendente_destino_id = serializers.IntegerField(required=True, help_text="ID do atendente de destino")
    departamento_destino_id = serializers.IntegerField(required=False, help_text="ID do departamento de destino (opcional)")
    motivo = serializers.CharField(required=True, help_text="Motivo da transferência")


class EncerrarChatSerializer(serializers.Serializer):
    """Serializer para encerramento de chat"""
    observacoes = serializers.CharField(required=False, allow_blank=True, help_text="Observações finais")
    solicitar_avaliacao = serializers.BooleanField(default=True, help_text="Enviar solicitação de avaliação ao cliente")

