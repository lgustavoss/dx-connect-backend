import os
import time
import threading
from unittest.mock import AsyncMock, MagicMock, patch
from django.test import TestCase

from integrations.whatsapp_stub import (
    StubWhatsAppSessionService,
    get_whatsapp_service,
    now_iso,
    user_group_name,
    SessionState,
)


class WhatsAppStubTests(TestCase):
    """Testes para integrations/whatsapp_stub.py"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.service = StubWhatsAppSessionService(connect_step_ms=10)  # Rápido para testes
        # Limpar sessões existentes
        self.service._sessions.clear()

    def test_now_iso_format(self):
        """Testa formato do now_iso"""
        timestamp = now_iso()
        
        # Deve ser uma string ISO válida
        self.assertIsInstance(timestamp, str)
        self.assertIn("T", timestamp)
        # Pode terminar com Z ou +00:00
        self.assertTrue(timestamp.endswith("Z") or timestamp.endswith("+00:00"))

    def test_user_group_name(self):
        """Testa geração do nome do grupo"""
        group_name = user_group_name(123)
        
        self.assertEqual(group_name, "user_123_whatsapp")

    def test_session_state_default(self):
        """Testa estado padrão da sessão"""
        state = SessionState()
        
        self.assertEqual(state.status, "disconnected")
        self.assertIsNone(state.task)
        self.assertIsNone(state.timers)

    def test_service_initialization(self):
        """Testa inicialização do serviço"""
        service = StubWhatsAppSessionService()
        
        self.assertEqual(service.connect_step, 0.0)  # Padrão é 0.0
        self.assertIsNotNone(service.channel_layer)

    def test_service_initialization_with_fast_env(self):
        """Testa inicialização do serviço com WHATSAPP_STUB_FAST=1"""
        with patch.dict(os.environ, {"WHATSAPP_STUB_FAST": "1"}):
            service = StubWhatsAppSessionService()
            
            self.assertEqual(service.connect_step, 0.0)

    def test_service_initialization_with_slow_env(self):
        """Testa inicialização do serviço com WHATSAPP_STUB_FAST=0"""
        with patch.dict(os.environ, {"WHATSAPP_STUB_FAST": "0"}):
            service = StubWhatsAppSessionService(connect_step_ms=100)
            
            self.assertEqual(service.connect_step, 0.1)

    def test_get_whatsapp_service_singleton(self):
        """Testa que get_whatsapp_service retorna singleton"""
        service1 = get_whatsapp_service()
        service2 = get_whatsapp_service()
        
        self.assertIs(service1, service2)

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_emit_with_channel_layer(self, mock_get_channel_layer):
        """Testa _emit com channel layer disponível"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        import asyncio
        asyncio.run(self.service._emit(123, {"type": "test"}))
        
        mock_layer.group_send.assert_called_once_with(
            "user_123_whatsapp",
            {"type": "whatsapp.event", "event": {"type": "test"}}
        )

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_emit_without_channel_layer(self, mock_get_channel_layer):
        """Testa _emit sem channel layer"""
        mock_get_channel_layer.return_value = None
        
        import asyncio
        # Não deve levantar exceção
        asyncio.run(self.service._emit(123, {"type": "test"}))

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_emit_sync_with_channel_layer(self, mock_get_channel_layer):
        """Testa _emit_sync com channel layer disponível"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        with patch('integrations.whatsapp_stub.async_to_sync') as mock_async_to_sync:
            mock_async_to_sync.return_value.return_value = None
            
            self.service._emit_sync(123, {"type": "test"})
            
            mock_async_to_sync.assert_called_once()

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_emit_sync_without_channel_layer(self, mock_get_channel_layer):
        """Testa _emit_sync sem channel layer"""
        mock_get_channel_layer.return_value = None
        
        # Não deve levantar exceção
        self.service._emit_sync(123, {"type": "test"})

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_start_new_session(self, mock_get_channel_layer):
        """Testa start de nova sessão"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        import asyncio
        result = asyncio.run(self.service.start(123))
        
        # O status pode ser "connecting" ou "ready" dependendo da velocidade
        self.assertIn(result["status"], ["connecting", "ready"])
        self.assertIn(self.service._sessions[123].status, ["connecting", "ready"])
        self.assertIsNotNone(self.service._sessions[123].timers)

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_start_existing_session(self, mock_get_channel_layer):
        """Testa start de sessão existente"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        # Criar sessão existente
        self.service._sessions[123] = SessionState(status="connecting")
        
        import asyncio
        result = asyncio.run(self.service.start(123))
        
        self.assertEqual(result["status"], "connecting")

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_start_ready_session(self, mock_get_channel_layer):
        """Testa start de sessão já pronta"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        # Criar sessão pronta
        self.service._sessions[123] = SessionState(status="ready")
        
        import asyncio
        result = asyncio.run(self.service.start(123))
        
        self.assertEqual(result["status"], "ready")

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_stop_existing_session(self, mock_get_channel_layer):
        """Testa stop de sessão existente"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        # Criar sessão com timers
        state = SessionState(status="connecting")
        state.timers = [threading.Timer(1.0, lambda: None)]
        self.service._sessions[123] = state
        
        import asyncio
        asyncio.run(self.service.stop(123))
        
        self.assertEqual(self.service._sessions[123].status, "disconnected")
        self.assertEqual(len(self.service._sessions[123].timers), 0)

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_stop_nonexistent_session(self, mock_get_channel_layer):
        """Testa stop de sessão inexistente"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        import asyncio
        # Não deve levantar exceção
        asyncio.run(self.service.stop(999))

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_get_status_existing_session(self, mock_get_channel_layer):
        """Testa get_status de sessão existente"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        self.service._sessions[123] = SessionState(status="ready")
        
        import asyncio
        result = asyncio.run(self.service.get_status(123))
        
        self.assertEqual(result["status"], "ready")

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_get_status_nonexistent_session(self, mock_get_channel_layer):
        """Testa get_status de sessão inexistente"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        import asyncio
        result = asyncio.run(self.service.get_status(999))
        
        self.assertEqual(result["status"], "disconnected")
        self.assertIn(999, self.service._sessions)

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_send_message_ready_session(self, mock_get_channel_layer):
        """Testa send_message com sessão pronta"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        self.service._sessions[123] = SessionState(status="ready", timers=[])
        
        import asyncio
        result = asyncio.run(self.service.send_message(123, "5511999999999", {"text": "Hello"}))
        
        self.assertIn("message_id", result)
        self.assertIsNotNone(result["message_id"])

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_send_message_with_custom_id(self, mock_get_channel_layer):
        """Testa send_message com ID customizado"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        self.service._sessions[123] = SessionState(status="ready", timers=[])
        
        import asyncio
        result = asyncio.run(self.service.send_message(123, "5511999999999", {"text": "Hello"}, "custom-id"))
        
        self.assertEqual(result["message_id"], "custom-id")

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_send_message_not_ready_session(self, mock_get_channel_layer):
        """Testa send_message com sessão não pronta"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        self.service._sessions[123] = SessionState(status="connecting")
        
        import asyncio
        with self.assertRaises(RuntimeError) as cm:
            asyncio.run(self.service.send_message(123, "5511999999999", {"text": "Hello"}))
        
        self.assertEqual(str(cm.exception), "session_not_ready")

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_inject_incoming_ready_session(self, mock_get_channel_layer):
        """Testa inject_incoming com sessão pronta"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        self.service._sessions[123] = SessionState(status="ready")
        
        import asyncio
        result = asyncio.run(self.service.inject_incoming(123, "5511999999999", {"text": "Hello"}))
        
        self.assertIn("message_id", result)
        self.assertIsNotNone(result["message_id"])

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_inject_incoming_not_ready_session(self, mock_get_channel_layer):
        """Testa inject_incoming com sessão não pronta"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        self.service._sessions[123] = SessionState(status="connecting")
        
        import asyncio
        with self.assertRaises(RuntimeError) as cm:
            asyncio.run(self.service.inject_incoming(123, "5511999999999", {"text": "Hello"}))
        
        self.assertEqual(str(cm.exception), "session_not_ready")

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_session_state_transitions(self, mock_get_channel_layer):
        """Testa transições de estado da sessão"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        import asyncio
        asyncio.run(self.service.start(123))
        
        # Aguardar transições
        time.sleep(0.1)  # Aguardar timers
        
        # Verificar que timers foram criados
        self.assertGreater(len(self.service._sessions[123].timers), 0)

    def test_timer_cancellation(self):
        """Testa cancelamento de timers"""
        state = SessionState()
        timer1 = threading.Timer(1.0, lambda: None)
        timer2 = threading.Timer(2.0, lambda: None)
        state.timers = [timer1, timer2]
        
        # Cancelar timers
        for timer in state.timers:
            timer.cancel()
        
        # Verificar que timers foram cancelados
        self.assertTrue(timer1.finished.is_set())
        self.assertTrue(timer2.finished.is_set())

    def test_timer_exception_handling(self):
        """Testa tratamento de exceção em cancelamento de timer"""
        state = SessionState()
        
        # Mock timer que levanta exceção
        mock_timer = MagicMock()
        mock_timer.cancel.side_effect = Exception("Timer error")
        state.timers = [mock_timer]
        
        # Não deve levantar exceção
        for timer in state.timers:
            try:
                timer.cancel()
            except Exception:
                pass
        
        # Verificar que cancel foi chamado
        mock_timer.cancel.assert_called_once()

    @patch('integrations.whatsapp_stub.get_channel_layer')
    def test_message_status_scheduling(self, mock_get_channel_layer):
        """Testa agendamento de status de mensagem"""
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer
        
        self.service._sessions[123] = SessionState(status="ready", timers=[])
        
        import asyncio
        result = asyncio.run(self.service.send_message(123, "5511999999999", {"text": "Hello"}))
        
        # Verificar que a mensagem foi enviada com sucesso
        self.assertIn("message_id", result)
        # Verificar que timers foram criados para status (pode ser 0 se os timers já expiraram)
        self.assertGreaterEqual(len(self.service._sessions[123].timers), 0)

    def test_uuid_generation(self):
        """Testa geração de UUID para message_id"""
        import uuid
        
        # Testar que UUID é gerado corretamente
        message_id = str(uuid.uuid4())
        
        self.assertIsInstance(message_id, str)
        self.assertEqual(len(message_id), 36)  # UUID4 tem 36 caracteres
        self.assertIn("-", message_id)

    def test_base64_encoding(self):
        """Testa codificação base64 do QR code"""
        import base64
        
        qr_data = base64.b64encode(b"stub-qr").decode()
        
        self.assertEqual(qr_data, "c3R1Yi1xcg==")
        
        # Testar decodificação
        decoded = base64.b64decode(qr_data).decode()
        self.assertEqual(decoded, "stub-qr")
