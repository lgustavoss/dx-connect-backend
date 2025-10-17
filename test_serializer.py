#!/usr/bin/env python3
"""
Teste do serializer de mensagens
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from chats.serializers import ChatMessageSerializer
from whatsapp.models import WhatsAppMessage

# Buscar mensagem do agente
msg = WhatsAppMessage.objects.filter(contact_number='agent_system', is_from_me=True).first()
if msg:
    print(f'Mensagem encontrada: ID {msg.id}')
    print(f'is_from_me: {msg.is_from_me}')
    print(f'contact_number: {msg.contact_number}')
    
    # Testar serializer
    serializer = ChatMessageSerializer(msg)
    data = serializer.data
    print(f'Serializer is_from_me: {data.get("is_from_me")}')
    print(f'Serializer is_from_agent: {data.get("is_from_agent")}')
    print(f'Serializer from_name: {data.get("from_name")}')
    
    if data.get('is_from_me') and data.get('is_from_agent'):
        print('✅ SUCESSO: Serializer funcionando corretamente!')
    else:
        print('❌ ERRO: Serializer não está funcionando')
else:
    print('Nenhuma mensagem do agente encontrada')
