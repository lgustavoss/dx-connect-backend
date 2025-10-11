"""
Testes de integração para o sistema WhatsApp.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync

from whatsapp.models import WhatsAppSession, WhatsAppMessage
from whatsapp.service import WhatsAppSessionService

User = get_user_model()


class WhatsAppIntegrationTests(TestCase):
    """Testes de integração end-to-end"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.service = WhatsAppSessionService()
    
    def test_full_session_lifecycle(self):
        """Testa ciclo de vida completo de uma sessão"""
        # 1. Iniciar sessão
        result = async_to_sync(self.service.start_session)(self.user.id)
        
        self.assertIn('session_id', result)
        self.assertIn('status', result)
        
        # Verifica que sessão foi criada no banco
        session = WhatsAppSession.objects.get(id=result['session_id'])
        self.assertEqual(session.usuario, self.user)
        
        # 2. Obter status
        status_result = async_to_sync(self.service.get_session_status)(self.user.id)
        
        self.assertEqual(status_result['session_id'], session.id)
        
        # 3. Parar sessão
        async_to_sync(self.service.stop_session)(self.user.id)
        
        # Verifica que sessão foi marcada como disconnected
        session.refresh_from_db()
        self.assertEqual(session.status, 'disconnected')
    
    def test_send_and_track_message(self):
        """Testa envio e rastreamento de mensagem"""
        # Criar sessão pronta e iniciar stub
        session = WhatsAppSession.objects.create(
            usuario=self.user,
            status='ready'
        )
        
        # Iniciar sessão no stub para permitir envio
        async_to_sync(self.service.stub_service.start)(self.user.id)
        
        # Enviar mensagem
        payload = {
            'type': 'text',
            'text': 'Hello Integration Test'
        }
        
        result = async_to_sync(self.service.send_message)(
            user_id=self.user.id,
            to='5511999999999',
            payload=payload
        )
        
        self.assertIn('message_id', result)
        self.assertIn('database_id', result)
        
        # Verifica que mensagem foi criada no banco
        message = WhatsAppMessage.objects.get(id=result['database_id'])
        self.assertEqual(message.session, session)
        self.assertEqual(message.direction, 'outbound')
        self.assertEqual(message.text_content, 'Hello Integration Test')
        self.assertEqual(message.status, 'queued')
        
        # Atualizar status da mensagem
        updated_message = async_to_sync(self.service.update_message_status)(
            message.message_id, 'sent'
        )
        
        # Verificar que a mensagem foi atualizada
        self.assertIsNotNone(updated_message)
        message.refresh_from_db()
        self.assertEqual(message.status, 'sent')
        self.assertIsNotNone(message.sent_at)
        
        # Verificar contadores da sessão
        session.refresh_from_db()
        self.assertEqual(session.total_messages_sent, 1)
    
    def test_receive_message(self):
        """Testa recebimento de mensagem"""
        # Criar sessão pronta
        session = WhatsAppSession.objects.create(
            usuario=self.user,
            status='ready'
        )
        
        # Receber mensagem
        payload = {
            'type': 'text',
            'text': 'Hello from client',
            'contact_name': 'John Doe'
        }
        
        message = async_to_sync(self.service.handle_incoming_message)(
            user_id=self.user.id,
            from_number='5511988888888',
            chat_id='5511988888888',
            payload=payload
        )
        
        self.assertEqual(message.session, session)
        self.assertEqual(message.direction, 'inbound')
        self.assertEqual(message.contact_number, '5511988888888')
        self.assertEqual(message.text_content, 'Hello from client')
        self.assertEqual(message.contact_name, 'John Doe')
        
        # Verificar contadores da sessão
        session.refresh_from_db()
        self.assertEqual(session.total_messages_received, 1)
    
    def test_latency_tracking(self):
        """Testa rastreamento de latência"""
        from django.utils import timezone
        from datetime import timedelta
        
        session = WhatsAppSession.objects.create(
            usuario=self.user,
            status='ready'
        )
        
        # Criar mensagem com latência controlada
        now = timezone.now()
        message = WhatsAppMessage.objects.create(
            session=session,
            usuario=self.user,
            message_id='msg_latency_test',
            direction='outbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999',
            queued_at=now,
            sent_at=now + timedelta(milliseconds=2000)  # 2s
        )
        
        # Verificar latência
        latency_ms = message.latency_to_sent_ms
        self.assertIsNotNone(latency_ms)
        self.assertGreaterEqual(latency_ms, 1999)  # Tolerância para timing
        self.assertLess(latency_ms, 2100)
        
        # Verificar que está dentro do limite aceitável (< 5s)
        self.assertTrue(message.is_latency_acceptable)
        
        # Criar mensagem com latência alta
        high_latency_message = WhatsAppMessage.objects.create(
            session=session,
            usuario=self.user,
            message_id='msg_high_latency',
            direction='outbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999',
            queued_at=now,
            sent_at=now + timedelta(milliseconds=7000)  # 7s
        )
        
        # Verificar que está fora do limite aceitável
        self.assertFalse(high_latency_message.is_latency_acceptable)

