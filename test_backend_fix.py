#!/usr/bin/env python3
"""
Teste das correções do backend
"""
import requests
import json

def test_backend_fixes():
    # Obter token
    from rest_framework_simplejwt.tokens import RefreshToken
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.get(username='admin')
    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)

    print(f'Token: {token}')

    # Testar endpoint HTTP inject-incoming com flags do agente
    url = 'http://localhost:8000/api/v1/whatsapp/inject-incoming/'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        'chat_id': '5561999888888',
        'from': 'agent_system',
        'payload': {
            'type': 'text',
            'text': 'Teste de mensagem do agente corrigida',
            'contact_name': 'Agente Teste',
            'sender_type': 'agent',
            'is_from_agent': True,
            'is_from_me': True
        }
    }

    print("📤 Enviando mensagem do agente...")
    response = requests.post(url, headers=headers, json=data)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'✅ Mensagem criada: ID {data["database_id"]}')
        print(f'is_from_me: {data["data"]["is_from_me"]}')
        print(f'contact_number: {data["data"]["contact_number"]}')
        
        # Testar API de mensagens
        print("\n📥 Testando API de mensagens...")
        messages_url = f'http://localhost:8000/api/v1/chats/5561999888888/messages/'
        response = requests.get(messages_url, headers=headers)
        print(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'Total de mensagens: {data.get("total", 0)}')
            if data.get('results'):
                msg = data['results'][0]
                print(f'Primeira mensagem:')
                print(f'  ID: {msg.get("id")}')
                print(f'  is_from_me: {msg.get("is_from_me")}')
                print(f'  is_from_agent: {msg.get("is_from_agent")}')
                print(f'  contact_number: {msg.get("contact_number")}')
                print(f'  text_content: {msg.get("text_content")}')
                
                # Verificar se as correções funcionaram
                if msg.get("is_from_me") and msg.get("is_from_agent"):
                    print("✅ SUCESSO: Flags de identificação do agente funcionando!")
                else:
                    print("❌ ERRO: Flags de identificação não funcionando")
            else:
                print("❌ ERRO: Nenhuma mensagem retornada")
        else:
            print(f"❌ ERRO: {response.text}")
    else:
        print(f"❌ ERRO: {response.text}")

if __name__ == "__main__":
    test_backend_fixes()
