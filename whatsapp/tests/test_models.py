"""
Testes para os modelos WhatsAppSession e WhatsAppMessage.
"""
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from whatsapp.models import WhatsAppSession, WhatsAppMessage

User = get_user_model()


class WhatsAppSessionModelTests(TestCase):
    """Testes para o modelo WhatsAppSession"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_session(self):
        """Testa criação de sessão"""
        session = WhatsAppSession.objects.create(
            usuario=self.user,
            status='disconnected',
            device_name='Test Device'
        )
        
        self.assertEqual(session.usuario, self.user)
        self.assertEqual(session.status, 'disconnected')
        self.assertEqual(session.device_name, 'Test Device')
        self.assertTrue(session.is_active)
        self.assertEqual(session.total_messages_sent, 0)
        self.assertEqual(session.total_messages_received, 0)
    
    def test_session_str(self):
        """Testa representação string da sessão"""
        session = WhatsAppSession.objects.create(
            usuario=self.user,
            status='ready'
        )
        
        expected = f"WhatsApp Session - {self.user.username} (Pronto)"
        self.assertEqual(str(session), expected)
    
    def test_is_connected_property(self):
        """Testa propriedade is_connected"""
        session = WhatsAppSession.objects.create(
            usuario=self.user,
            status='disconnected'
        )
        
        self.assertFalse(session.is_connected)
        
        session.status = 'ready'
        session.save()
        
        self.assertTrue(session.is_connected)
    
    def test_uptime_seconds(self):
        """Testa cálculo de uptime"""
        session = WhatsAppSession.objects.create(
            usuario=self.user,
            status='ready',
            connected_at=timezone.now() - timedelta(minutes=5)
        )
        
        uptime = session.uptime_seconds
        self.assertIsNotNone(uptime)
        self.assertGreater(uptime, 299)  # ~5 minutos
        self.assertLess(uptime, 301)
    
    def test_mark_as_connected(self):
        """Testa método mark_as_connected"""
        session = WhatsAppSession.objects.create(
            usuario=self.user,
            status='connecting',
            error_count=5,
            last_error='Some error'
        )
        
        session.mark_as_connected()
        
        self.assertEqual(session.status, 'ready')
        self.assertIsNotNone(session.connected_at)
        self.assertEqual(session.error_count, 0)
        self.assertEqual(session.last_error, '')
    
    def test_mark_as_disconnected(self):
        """Testa método mark_as_disconnected"""
        session = WhatsAppSession.objects.create(
            usuario=self.user,
            status='ready'
        )
        
        session.mark_as_disconnected()
        
        self.assertEqual(session.status, 'disconnected')
        self.assertIsNotNone(session.disconnected_at)
    
    def test_mark_as_error(self):
        """Testa método mark_as_error"""
        session = WhatsAppSession.objects.create(
            usuario=self.user,
            status='ready',
            error_count=0
        )
        
        error_msg = "Connection timeout"
        session.mark_as_error(error_msg)
        
        self.assertEqual(session.status, 'error')
        self.assertEqual(session.last_error, error_msg)
        self.assertEqual(session.error_count, 1)
    
    def test_increment_sent_messages(self):
        """Testa incremento de mensagens enviadas"""
        session = WhatsAppSession.objects.create(
            usuario=self.user,
            total_messages_sent=0
        )
        
        session.increment_sent_messages()
        
        self.assertEqual(session.total_messages_sent, 1)
        self.assertIsNotNone(session.last_message_at)
    
    def test_increment_received_messages(self):
        """Testa incremento de mensagens recebidas"""
        session = WhatsAppSession.objects.create(
            usuario=self.user,
            total_messages_received=0
        )
        
        session.increment_received_messages()
        
        self.assertEqual(session.total_messages_received, 1)
        self.assertIsNotNone(session.last_message_at)


class WhatsAppMessageModelTests(TestCase):
    """Testes para o modelo WhatsAppMessage"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.session = WhatsAppSession.objects.create(
            usuario=self.user,
            status='ready'
        )
    
    def test_create_message(self):
        """Testa criação de mensagem"""
        message = WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.user,
            message_id='msg_123',
            direction='outbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999',
            text_content='Hello, World!'
        )
        
        self.assertEqual(message.session, self.session)
        self.assertEqual(message.usuario, self.user)
        self.assertEqual(message.message_id, 'msg_123')
        self.assertEqual(message.direction, 'outbound')
        self.assertEqual(message.message_type, 'text')
        self.assertEqual(message.text_content, 'Hello, World!')
        self.assertEqual(message.status, 'queued')
    
    def test_message_str(self):
        """Testa representação string da mensagem"""
        message = WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.user,
            message_id='msg_123',
            direction='inbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999'
        )
        
        expected = "Recebida de 5511999999999 - text (Na Fila)"
        self.assertEqual(str(message), expected)
    
    def test_latency_to_sent_ms(self):
        """Testa cálculo de latência até envio"""
        now = timezone.now()
        message = WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.user,
            message_id='msg_123',
            direction='outbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999',
            queued_at=now,
            sent_at=now + timedelta(milliseconds=100)
        )
        
        latency = message.latency_to_sent_ms
        self.assertIsNotNone(latency)
        self.assertGreaterEqual(latency, 99)  # Tolerância para timing
        self.assertLess(latency, 110)
    
    def test_latency_to_delivered_ms(self):
        """Testa cálculo de latência até entrega"""
        now = timezone.now()
        message = WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.user,
            message_id='msg_123',
            direction='outbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999',
            queued_at=now,
            delivered_at=now + timedelta(milliseconds=500)
        )
        
        latency = message.latency_to_delivered_ms
        self.assertIsNotNone(latency)
        self.assertGreaterEqual(latency, 499)  # Tolerância para timing
        self.assertLess(latency, 510)
    
    def test_is_latency_acceptable_ok(self):
        """Testa verificação de latência aceitável (OK)"""
        now = timezone.now()
        message = WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.user,
            message_id='msg_123',
            direction='outbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999',
            queued_at=now,
            sent_at=now + timedelta(milliseconds=2000)  # 2s
        )
        
        self.assertTrue(message.is_latency_acceptable)
    
    def test_is_latency_acceptable_high(self):
        """Testa verificação de latência aceitável (ALTA)"""
        now = timezone.now()
        message = WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.user,
            message_id='msg_123',
            direction='outbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999',
            queued_at=now,
            sent_at=now + timedelta(milliseconds=6000)  # 6s > 5s
        )
        
        self.assertFalse(message.is_latency_acceptable)
    
    def test_mark_as_sent(self):
        """Testa método mark_as_sent"""
        message = WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.user,
            message_id='msg_123',
            direction='outbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999'
        )
        
        message.mark_as_sent()
        
        self.assertEqual(message.status, 'sent')
        self.assertIsNotNone(message.sent_at)
    
    def test_mark_as_delivered(self):
        """Testa método mark_as_delivered"""
        message = WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.user,
            message_id='msg_123',
            direction='outbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999'
        )
        
        message.mark_as_delivered()
        
        self.assertEqual(message.status, 'delivered')
        self.assertIsNotNone(message.delivered_at)
    
    def test_mark_as_read(self):
        """Testa método mark_as_read"""
        message = WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.user,
            message_id='msg_123',
            direction='outbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999'
        )
        
        message.mark_as_read()
        
        self.assertEqual(message.status, 'read')
        self.assertIsNotNone(message.read_at)
    
    def test_mark_as_error(self):
        """Testa método mark_as_error"""
        message = WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.user,
            message_id='msg_123',
            direction='outbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999'
        )
        
        error_msg = "Failed to send"
        message.mark_as_error(error_msg)
        
        self.assertEqual(message.status, 'error')
        self.assertEqual(message.error_message, error_msg)

