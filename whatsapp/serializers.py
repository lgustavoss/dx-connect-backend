from rest_framework import serializers
from .models import WhatsAppSession, WhatsAppMessage


class WhatsAppSessionSerializer(serializers.ModelSerializer):
    """Serializer completo para WhatsAppSession"""
    uptime_seconds = serializers.IntegerField(read_only=True)
    is_connected = serializers.BooleanField(read_only=True)
    usuario_nome = serializers.CharField(source='usuario.username', read_only=True)
    
    class Meta:
        model = WhatsAppSession
        fields = [
            'id', 'usuario', 'usuario_nome', 'status', 'device_name',
            'phone_number', 'qr_code', 'created_at', 'updated_at',
            'connected_at', 'disconnected_at', 'total_messages_sent',
            'total_messages_received', 'last_message_at', 'last_error',
            'error_count', 'is_active', 'uptime_seconds', 'is_connected'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'connected_at',
            'disconnected_at', 'total_messages_sent', 'total_messages_received',
            'last_message_at', 'error_count', 'uptime_seconds', 'is_connected'
        ]


class WhatsAppSessionListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de sessões"""
    usuario_nome = serializers.CharField(source='usuario.username', read_only=True)
    is_connected = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = WhatsAppSession
        fields = [
            'id', 'usuario', 'usuario_nome', 'status', 'phone_number',
            'is_connected', 'total_messages_sent', 'total_messages_received',
            'last_message_at', 'updated_at'
        ]


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    """Serializer completo para WhatsAppMessage"""
    latency_to_sent_ms = serializers.IntegerField(read_only=True)
    latency_to_delivered_ms = serializers.IntegerField(read_only=True)
    latency_to_read_ms = serializers.IntegerField(read_only=True)
    total_latency_ms = serializers.IntegerField(read_only=True)
    is_latency_acceptable = serializers.BooleanField(read_only=True)
    usuario_nome = serializers.CharField(source='usuario.username', read_only=True)
    
    class Meta:
        model = WhatsAppMessage
        fields = [
            'id', 'session', 'usuario', 'usuario_nome', 'message_id',
            'client_message_id', 'direction', 'message_type', 'chat_id',
            'contact_number', 'contact_name', 'text_content', 'media_url',
            'media_mime_type', 'media_size', 'payload', 'status',
            'created_at', 'queued_at', 'sent_at', 'delivered_at', 'read_at',
            'error_message', 'is_from_me', 'latency_to_sent_ms',
            'latency_to_delivered_ms', 'latency_to_read_ms',
            'total_latency_ms', 'is_latency_acceptable'
        ]
        read_only_fields = [
            'id', 'created_at', 'queued_at', 'sent_at', 'delivered_at',
            'read_at', 'latency_to_sent_ms', 'latency_to_delivered_ms',
            'latency_to_read_ms', 'total_latency_ms', 'is_latency_acceptable'
        ]


class WhatsAppMessageListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de mensagens"""
    total_latency_ms = serializers.IntegerField(read_only=True)
    is_latency_acceptable = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = WhatsAppMessage
        fields = [
            'id', 'message_id', 'direction', 'message_type', 'contact_number',
            'text_content', 'status', 'created_at', 'total_latency_ms',
            'is_latency_acceptable'
        ]


class WhatsAppSendMessageSerializer(serializers.Serializer):
    """Serializer para envio de mensagens"""
    to = serializers.CharField(
        max_length=20,
        help_text="Número do destinatário (formato internacional)"
    )
    type = serializers.ChoiceField(
        choices=['text', 'image', 'audio', 'video', 'document'],
        default='text',
        help_text="Tipo da mensagem"
    )
    text = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Conteúdo de texto (obrigatório para type=text)"
    )
    media_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="URL da mídia (para imagens, áudios, etc)"
    )
    client_message_id = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        help_text="ID personalizado para rastreamento"
    )
    
    def validate(self, data):
        """Validação customizada"""
        message_type = data.get('type', 'text')
        
        if message_type == 'text' and not data.get('text'):
            raise serializers.ValidationError({
                'text': 'Campo obrigatório para mensagens de texto'
            })
        
        if message_type in ['image', 'audio', 'video', 'document'] and not data.get('media_url'):
            raise serializers.ValidationError({
                'media_url': f'Campo obrigatório para mensagens do tipo {message_type}'
            })
        
        return data


class WhatsAppSessionStatusSerializer(serializers.Serializer):
    """Serializer para status da sessão"""
    status = serializers.ChoiceField(
        choices=WhatsAppSession.STATUS_CHOICES
    )
    connected_at = serializers.DateTimeField(required=False, allow_null=True)
    uptime_seconds = serializers.IntegerField(required=False, allow_null=True)
    total_messages_sent = serializers.IntegerField(required=False)
    total_messages_received = serializers.IntegerField(required=False)

