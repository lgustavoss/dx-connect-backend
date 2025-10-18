#!/usr/bin/env python3
"""
Script para testar eventos WebSocket diretamente
"""
import os
import sys
import django
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def test_websocket_event():
    """Testa envio de evento WebSocket"""
    channel_layer = get_channel_layer()
    
    if not channel_layer:
        print("❌ Channel layer não disponível")
        return
    
    print("✅ Channel layer disponível")
    
    # Evento de teste - formato correto para o consumer
    event_payload = {
        "type": "message_sent",
        "data": {
            "message_id": "test-123",
            "status": "queued",
            "to": "5561987651234",
            "timestamp": "2025-10-18T19:10:00Z",
            "error": None
        },
        "version": "v1"
    }
    
    # Enviar para usuário 9 (que está conectado)
    group_name = "user_9_whatsapp"
    print(f"📤 Enviando evento para grupo: {group_name}")
    print(f"📦 Payload: {event_payload}")
    
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {"type": "whatsapp.event", "event": event_payload}
        )
        print("✅ Evento enviado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar evento: {e}")

if __name__ == "__main__":
    test_websocket_event()
