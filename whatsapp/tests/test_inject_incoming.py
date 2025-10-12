"""
Testes para injeção de mensagens de teste (Issue #83).
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from whatsapp.models import WhatsAppSession, WhatsAppMessage

User = get_user_model()


class InjectIncomingMessageTests(TestCase):
    """Testes para o endpoint de injeção de mensagens"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Criar sessão WhatsApp
        self.session = WhatsAppSession.objects.create(
            usuario=self.user,
            status='ready',
            is_active=True,
            device_name='Test Device'
        )
        
        self.url = '/api/v1/whatsapp/inject-incoming/'
    
    def test_inject_text_message_success(self):
        """Testa injeção de mensagem de texto com sucesso"""
        payload = {
            'from': '5511999999999',
            'payload': {
                'type': 'text',
                'text': 'Olá, preciso de ajuda!',
                'contact_name': 'João Silva'
            }
        }
        
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('message_id', response.data)
        self.assertIn('database_id', response.data)
        self.assertEqual(response.data['message'], 'Mensagem de teste injetada com sucesso')
        
        # Verificar que a mensagem foi criada no banco
        self.assertTrue(
            WhatsAppMessage.objects.filter(
                contact_number='5511999999999',
                text_content='Olá, preciso de ajuda!',
                direction='inbound'
            ).exists()
        )
    
    def test_inject_message_without_from(self):
        """Testa erro quando 'from' não é fornecido"""
        payload = {
            'payload': {
                'type': 'text',
                'text': 'Teste'
            }
        }
        
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('from', response.data['error'].lower())
    
    def test_inject_message_without_payload(self):
        """Testa erro quando 'payload' não é fornecido"""
        payload = {
            'from': '5511999999999'
        }
        
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('payload', response.data['error'].lower())
    
    def test_inject_message_invalid_type(self):
        """Testa erro com tipo de mensagem inválido"""
        payload = {
            'from': '5511999999999',
            'payload': {
                'type': 'invalid_type',
                'text': 'Teste'
            }
        }
        
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('inválido', response.data['error'].lower())
    
    def test_inject_text_message_without_text(self):
        """Testa erro quando mensagem de texto não tem conteúdo"""
        payload = {
            'from': '5511999999999',
            'payload': {
                'type': 'text'
            }
        }
        
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('text', response.data['error'].lower())
    
    def test_inject_message_with_chat_id(self):
        """Testa injeção com chat_id customizado"""
        payload = {
            'from': '5511999999999',
            'chat_id': '5511888888888-group',
            'payload': {
                'type': 'text',
                'text': 'Mensagem de grupo',
                'contact_name': 'Maria'
            }
        }
        
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar chat_id correto
        message = WhatsAppMessage.objects.get(message_id=response.data['message_id'])
        self.assertEqual(message.chat_id, '5511888888888-group')
    
    def test_inject_message_without_session(self):
        """Testa erro quando usuário não tem sessão"""
        # Deletar sessão
        self.session.delete()
        
        payload = {
            'from': '5511999999999',
            'payload': {
                'type': 'text',
                'text': 'Teste'
            }
        }
        
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertIn('sessão', response.data['error'].lower())
    
    def test_inject_message_unauthenticated(self):
        """Testa que endpoint requer autenticação"""
        self.client.force_authenticate(user=None)
        
        payload = {
            'from': '5511999999999',
            'payload': {
                'type': 'text',
                'text': 'Teste'
            }
        }
        
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_inject_image_message(self):
        """Testa injeção de mensagem com imagem"""
        payload = {
            'from': '5511999999999',
            'payload': {
                'type': 'image',
                'media_url': 'https://example.com/image.jpg',
                'text': 'Veja essa imagem',
                'contact_name': 'Pedro'
            }
        }
        
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar dados da mensagem
        message = WhatsAppMessage.objects.get(message_id=response.data['message_id'])
        self.assertEqual(message.message_type, 'image')
        self.assertEqual(message.media_url, 'https://example.com/image.jpg')
        self.assertEqual(message.text_content, 'Veja essa imagem')
    
    def test_inject_multiple_messages_same_contact(self):
        """Testa injeção de múltiplas mensagens do mesmo contato"""
        contact = '5511999999999'
        
        for i in range(3):
            payload = {
                'from': contact,
                'payload': {
                    'type': 'text',
                    'text': f'Mensagem {i+1}',
                    'contact_name': 'Cliente Teste'
                }
            }
            
            response = self.client.post(self.url, payload, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que todas foram criadas
        messages = WhatsAppMessage.objects.filter(
            contact_number=contact,
            direction='inbound'
        )
        self.assertEqual(messages.count(), 3)
    
    def test_inject_message_creates_delivered_status(self):
        """Testa que mensagem injetada já vem com status delivered"""
        payload = {
            'from': '5511999999999',
            'payload': {
                'type': 'text',
                'text': 'Teste status'
            }
        }
        
        response = self.client.post(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        message = WhatsAppMessage.objects.get(message_id=response.data['message_id'])
        self.assertEqual(message.status, 'delivered')
        self.assertIsNotNone(message.delivered_at)

