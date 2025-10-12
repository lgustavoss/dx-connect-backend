from rest_framework import serializers
from .models_presence import AgentPresence, TypingIndicator


class AgentPresenceSerializer(serializers.ModelSerializer):
    agent_username = serializers.CharField(source='agent.username', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    tempo_no_status_atual = serializers.IntegerField(read_only=True)
    esta_inativo = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AgentPresence
        fields = [
            'id', 'agent', 'agent_username', 'status', 'status_message',
            'last_heartbeat', 'websocket_connected', 'is_available',
            'tempo_no_status_atual', 'esta_inativo', 'status_changed_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'last_heartbeat', 'status_changed_at', 'updated_at']


class TypingIndicatorSerializer(serializers.ModelSerializer):
    agent_username = serializers.CharField(source='agent.username', read_only=True)
    
    class Meta:
        model = TypingIndicator
        fields = [
            'id', 'agent', 'agent_username', 'chat_id', 'is_typing',
            'started_at', 'updated_at'
        ]
        read_only_fields = ['id', 'started_at', 'updated_at']

