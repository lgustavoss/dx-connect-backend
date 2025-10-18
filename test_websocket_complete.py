#!/usr/bin/env python3
"""
Script completo para testar eventos WebSocket
"""
import os
import sys
import django
import time
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def test_websocket_events():
    """Testa todos os tipos de eventos WebSocket"""
    channel_layer = get_channel_layer()
    
    if not channel_layer:
        print("❌ Channel layer não disponível")
        return
    
    print("✅ Channel layer disponível")
    
    # Teste 1: Evento message_sent
    print("\n🧪 Teste 1: Evento message_sent")
    event_sent = {
        "type": "message_sent",
        "data": {
            "message_id": "test-sent-123",
            "status": "queued",
            "to": "5561987651234",
            "timestamp": "2025-10-18T19:15:00Z",
            "error": None
        },
        "version": "v1"
    }
    
    print(f"📤 Enviando message_sent para grupo geral...")
    async_to_sync(channel_layer.group_send)(
        "whatsapp_messages",
        {"type": "whatsapp.event", "event": event_sent}
    )
    print("✅ Evento message_sent enviado!")
    
    time.sleep(1)
    
    # Teste 2: Evento message_status_update
    print("\n🧪 Teste 2: Evento message_status_update")
    event_status = {
        "type": "message_status_update",
        "data": {
            "message_id": "test-sent-123",
            "status": "delivered",
            "to": "5561987651234",
            "timestamp": "2025-10-18T19:15:30Z",
            "error": None
        },
        "version": "v1"
    }
    
    print(f"📤 Enviando message_status_update para grupo geral...")
    async_to_sync(channel_layer.group_send)(
        "whatsapp_messages",
        {"type": "whatsapp.event", "event": event_status}
    )
    print("✅ Evento message_status_update enviado!")
    
    time.sleep(1)
    
    # Teste 3: Evento para usuário específico
    print("\n🧪 Teste 3: Evento para usuário específico")
    event_user = {
        "type": "message_sent",
        "data": {
            "message_id": "test-user-456",
            "status": "sent",
            "to": "5561987651234",
            "timestamp": "2025-10-18T19:16:00Z",
            "error": None
        },
        "version": "v1"
    }
    
    print(f"📤 Enviando evento para usuário 9...")
    async_to_sync(channel_layer.group_send)(
        "user_9_whatsapp",
        {"type": "whatsapp.event", "event": event_user}
    )
    print("✅ Evento para usuário específico enviado!")
    
    print("\n🎉 Todos os testes de eventos WebSocket concluídos!")
    print("📋 Verifique os logs do web container para confirmar recebimento dos eventos")

if __name__ == "__main__":
    test_websocket_events()
