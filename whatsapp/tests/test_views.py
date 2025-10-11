"""
Testes para as views do app WhatsApp.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch, AsyncMock

from whatsapp.models import WhatsAppSession, WhatsAppMessage

User = get_user_model()


class WhatsAppSessionViewSetTests(APITestCase):
    """Testes para WhatsAppSessionViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.session = WhatsAppSession.objects.create(
            usuario=self.user,
            status='disconnected'
        )
    
    def test_list_sessions(self):
        """Testa listagem de sessões"""
        url = reverse('whatsapp-session-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_retrieve_session(self):
        """Testa detalhamento de sessão"""
        url = reverse('whatsapp-session-detail', args=[self.session.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.session.id)
        self.assertEqual(response.data['status'], 'disconnected')
    
    @patch('whatsapp.views.get_whatsapp_session_service')
    def test_start_session(self, mock_service):
        """Testa início de sessão"""
        mock_service_instance = mock_service.return_value
        mock_service_instance.start_session = AsyncMock(return_value={
            'session_id': self.session.id,
            'status': 'connecting',
            'message': 'Sessão iniciada com sucesso'
        })
        
        url = reverse('whatsapp-session-start-session')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('session_id', response.data)
    
    @patch('whatsapp.views.get_whatsapp_session_service')
    def test_stop_session(self, mock_service):
        """Testa parada de sessão"""
        mock_service_instance = mock_service.return_value
        mock_service_instance.stop_session = AsyncMock()
        
        url = reverse('whatsapp-session-stop-session')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    @patch('whatsapp.views.get_whatsapp_session_service')
    def test_session_status(self, mock_service):
        """Testa consulta de status"""
        mock_service_instance = mock_service.return_value
        mock_service_instance.get_session_status = AsyncMock(return_value={
            'session_id': self.session.id,
            'status': 'ready',
            'is_connected': True
        })
        
        url = reverse('whatsapp-session-session-status')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
    
    def test_session_metrics(self):
        """Testa métricas da sessão"""
        # Criar algumas mensagens
        WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.user,
            message_id='msg_1',
            direction='outbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999'
        )
        
        url = reverse('whatsapp-session-session-metrics', args=[self.session.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_messages', response.data)
        self.assertEqual(response.data['total_messages'], 1)
    
    def test_filter_by_status(self):
        """Testa filtro por status"""
        # Criar outra sessão com status diferente
        WhatsAppSession.objects.create(
            usuario=self.user,
            status='ready'
        )
        
        url = reverse('whatsapp-session-list') + '?status=ready'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'ready')
    
    def test_unauthorized_access(self):
        """Testa acesso não autorizado"""
        self.client.force_authenticate(user=None)
        
        url = reverse('whatsapp-session-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WhatsAppMessageViewSetTests(APITestCase):
    """Testes para WhatsAppMessageViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.session = WhatsAppSession.objects.create(
            usuario=self.user,
            status='ready'
        )
        
        self.message = WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.user,
            message_id='msg_123',
            direction='outbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999',
            text_content='Hello'
        )
    
    def test_list_messages(self):
        """Testa listagem de mensagens"""
        url = reverse('whatsapp-message-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_retrieve_message(self):
        """Testa detalhamento de mensagem"""
        url = reverse('whatsapp-message-detail', args=[self.message.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message_id'], 'msg_123')
    
    def test_filter_by_direction(self):
        """Testa filtro por direção"""
        # Criar mensagem recebida
        WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.user,
            message_id='msg_456',
            direction='inbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999'
        )
        
        url = reverse('whatsapp-message-list') + '?direction=inbound'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['direction'], 'inbound')
    
    def test_latency_stats(self):
        """Testa estatísticas de latência"""
        url = reverse('whatsapp-message-latency-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_messages', response.data)
        self.assertIn('latency_acceptable_rate', response.data)
    
    def test_high_latency_messages(self):
        """Testa listagem de mensagens com alta latência"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Criar mensagem com alta latência
        now = timezone.now()
        WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.user,
            message_id='msg_slow',
            direction='outbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999',
            queued_at=now,
            sent_at=now + timedelta(milliseconds=6000)  # 6s
        )
        
        url = reverse('whatsapp-message-high-latency-messages')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Deve retornar pelo menos 1 mensagem com alta latência
        self.assertGreaterEqual(len(response.data), 1)


class WhatsAppSendMessageViewTests(APITestCase):
    """Testes para WhatsAppSendMessageView"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.session = WhatsAppSession.objects.create(
            usuario=self.user,
            status='ready'
        )
    
    @patch('whatsapp.views.get_whatsapp_session_service')
    def test_send_text_message(self, mock_service):
        """Testa envio de mensagem de texto"""
        mock_service_instance = mock_service.return_value
        mock_service_instance.send_message = AsyncMock(return_value={
            'message_id': 'msg_789',
            'database_id': 1,
            'status': 'queued'
        })
        
        url = reverse('whatsapp-send')
        data = {
            'to': '5511999999999',
            'type': 'text',
            'text': 'Hello, World!'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('message_id', response.data)
    
    def test_send_message_validation_error(self):
        """Testa validação de envio de mensagem"""
        url = reverse('whatsapp-send')
        data = {
            'type': 'text',
            # Falta o campo 'to'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_send_message_text_required(self):
        """Testa validação de texto obrigatório"""
        url = reverse('whatsapp-send')
        data = {
            'to': '5511999999999',
            'type': 'text',
            # Falta o campo 'text'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('text', response.data)
    
    @patch('whatsapp.views.get_whatsapp_session_service')
    def test_send_message_session_not_ready(self, mock_service):
        """Testa envio quando sessão não está pronta"""
        mock_service_instance = mock_service.return_value
        mock_service_instance.send_message = AsyncMock(
            side_effect=RuntimeError("Sessão não está pronta para enviar mensagens")
        )
        
        url = reverse('whatsapp-send')
        data = {
            'to': '5511999999999',
            'type': 'text',
            'text': 'Hello'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_423_LOCKED)

