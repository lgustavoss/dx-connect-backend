from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

Agent = get_user_model()


class WhatsAppSessionStartViewTests(TestCase):
    """Testes para WhatsAppSessionStartView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        # Adicionar permissão para gerenciar WhatsApp
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_whatsapp")
        self.user.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user)

    @patch('core.views.whatsapp.get_whatsapp_service')
    def test_whatsapp_session_start_post_authenticated_with_permission(self, mock_get_service):
        """Testa POST /api/v1/whatsapp/session/start com usuário autenticado e permissão"""
        # Mock do serviço
        mock_service = MagicMock()
        mock_service.start.return_value = {"status": "connecting", "message": "Iniciando sessão"}
        mock_get_service.return_value = mock_service
        
        response = self.client.post("/api/v1/whatsapp/session/start")
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["status"], "connecting")
        mock_service.start.assert_called_once()

    def test_whatsapp_session_start_post_without_permission(self):
        """Testa POST /api/v1/whatsapp/session/start sem permissão"""
        # Remover permissão
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_whatsapp")
        self.user.user_permissions.remove(permission)
        
        response = self.client.post("/api/v1/whatsapp/session/start")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_whatsapp_session_start_post_unauthenticated(self):
        """Testa POST /api/v1/whatsapp/session/start sem autenticação"""
        self.client.force_authenticate(user=None)
        
        response = self.client.post("/api/v1/whatsapp/session/start")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WhatsAppSessionStopViewTests(TestCase):
    """Testes para WhatsAppSessionStopView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        # Adicionar permissão para gerenciar WhatsApp
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_whatsapp")
        self.user.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user)

    @patch('core.views.whatsapp.get_whatsapp_service')
    def test_whatsapp_session_stop_delete_authenticated_with_permission(self, mock_get_service):
        """Testa DELETE /api/v1/whatsapp/session com usuário autenticado e permissão"""
        # Mock do serviço
        mock_service = MagicMock()
        mock_service.stop.return_value = None
        mock_get_service.return_value = mock_service
        
        response = self.client.delete("/api/v1/whatsapp/session")
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_service.stop.assert_called_once()

    def test_whatsapp_session_stop_delete_without_permission(self):
        """Testa DELETE /api/v1/whatsapp/session sem permissão"""
        # Remover permissão
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_whatsapp")
        self.user.user_permissions.remove(permission)
        
        response = self.client.delete("/api/v1/whatsapp/session")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_whatsapp_session_stop_delete_unauthenticated(self):
        """Testa DELETE /api/v1/whatsapp/session sem autenticação"""
        self.client.force_authenticate(user=None)
        
        response = self.client.delete("/api/v1/whatsapp/session")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WhatsAppSessionStatusViewTests(TestCase):
    """Testes para WhatsAppSessionStatusView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    @patch('core.views.whatsapp.get_whatsapp_service')
    def test_whatsapp_session_status_get_authenticated(self, mock_get_service):
        """Testa GET /api/v1/whatsapp/session/status com usuário autenticado"""
        # Mock do serviço
        mock_service = MagicMock()
        mock_service.get_status.return_value = {"status": "ready", "message": "Sessão ativa"}
        mock_get_service.return_value = mock_service
        
        response = self.client.get("/api/v1/whatsapp/session/status")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ready")
        mock_service.get_status.assert_called_once()

    def test_whatsapp_session_status_get_unauthenticated(self):
        """Testa GET /api/v1/whatsapp/session/status sem autenticação"""
        self.client.force_authenticate(user=None)
        
        response = self.client.get("/api/v1/whatsapp/session/status")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WhatsAppSendMessageViewTests(TestCase):
    """Testes para WhatsAppSendMessageView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        # Adicionar permissão para gerenciar WhatsApp
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_whatsapp")
        self.user.user_permissions.add(permission)
        self.client.force_authenticate(user=self.user)

    @patch('core.views.whatsapp.get_whatsapp_service')
    def test_whatsapp_send_message_post_authenticated_with_permission(self, mock_get_service):
        """Testa POST /api/v1/whatsapp/messages com usuário autenticado e permissão"""
        # Mock do serviço
        mock_service = MagicMock()
        mock_service.send_message.return_value = {
            "message_id": "msg_123",
            "status": "sent",
            "to": "+5511999999999"
        }
        mock_get_service.return_value = mock_service
        
        data = {
            "to": "+5511999999999",
            "type": "text",
            "text": "Olá, como posso ajudar?"
        }
        
        response = self.client.post("/api/v1/whatsapp/messages", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["message_id"], "msg_123")
        mock_service.send_message.assert_called_once()

    def test_whatsapp_send_message_post_missing_to_field(self):
        """Testa POST /api/v1/whatsapp/messages sem campo 'to'"""
        data = {
            "type": "text",
            "text": "Olá, como posso ajudar?"
        }
        
        response = self.client.post("/api/v1/whatsapp/messages", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Campo 'to' é obrigatório", response.data["detail"])

    def test_whatsapp_send_message_post_invalid_to_field(self):
        """Testa POST /api/v1/whatsapp/messages com campo 'to' inválido"""
        data = {
            "to": 123,  # Deve ser string
            "type": "text",
            "text": "Olá, como posso ajudar?"
        }
        
        response = self.client.post("/api/v1/whatsapp/messages", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Campo 'to' é obrigatório", response.data["detail"])

    def test_whatsapp_send_message_post_invalid_type(self):
        """Testa POST /api/v1/whatsapp/messages com tipo inválido"""
        data = {
            "to": "+5511999999999",
            "type": "invalid_type",
            "text": "Olá, como posso ajudar?"
        }
        
        response = self.client.post("/api/v1/whatsapp/messages", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Campo 'type' inválido", response.data["detail"])

    def test_whatsapp_send_message_post_missing_text_for_text_type(self):
        """Testa POST /api/v1/whatsapp/messages sem campo 'text' para tipo 'text'"""
        data = {
            "to": "+5511999999999",
            "type": "text"
        }
        
        response = self.client.post("/api/v1/whatsapp/messages", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Campo 'text' é obrigatório", response.data["detail"])

    @patch('core.views.whatsapp.get_whatsapp_service')
    def test_whatsapp_send_message_post_session_not_ready(self, mock_get_service):
        """Testa POST /api/v1/whatsapp/messages quando sessão não está pronta"""
        # Mock do serviço para levantar RuntimeError
        mock_service = MagicMock()
        mock_service.send_message.side_effect = RuntimeError("Sessão não está pronta")
        mock_get_service.return_value = mock_service
        
        data = {
            "to": "+5511999999999",
            "type": "text",
            "text": "Olá, como posso ajudar?"
        }
        
        response = self.client.post("/api/v1/whatsapp/messages", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_423_LOCKED)
        self.assertIn("Sessão não está pronta", response.data["detail"])

    def test_whatsapp_send_message_post_without_permission(self):
        """Testa POST /api/v1/whatsapp/messages sem permissão"""
        # Remover permissão
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_whatsapp")
        self.user.user_permissions.remove(permission)
        
        data = {
            "to": "+5511999999999",
            "type": "text",
            "text": "Olá, como posso ajudar?"
        }
        
        response = self.client.post("/api/v1/whatsapp/messages", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_whatsapp_send_message_post_unauthenticated(self):
        """Testa POST /api/v1/whatsapp/messages sem autenticação"""
        self.client.force_authenticate(user=None)
        
        data = {
            "to": "+5511999999999",
            "type": "text",
            "text": "Olá, como posso ajudar?"
        }
        
        response = self.client.post("/api/v1/whatsapp/messages", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('core.views.whatsapp.get_whatsapp_service')
    def test_whatsapp_send_message_post_with_client_message_id(self, mock_get_service):
        """Testa POST /api/v1/whatsapp/messages com client_message_id"""
        # Mock do serviço
        mock_service = MagicMock()
        mock_service.send_message.return_value = {
            "message_id": "msg_123",
            "status": "sent",
            "to": "+5511999999999"
        }
        mock_get_service.return_value = mock_service
        
        data = {
            "to": "+5511999999999",
            "type": "text",
            "text": "Olá, como posso ajudar?",
            "client_message_id": "client_msg_456"
        }
        
        response = self.client.post("/api/v1/whatsapp/messages", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        # Verificar se o client_message_id foi passado para o serviço
        mock_service.send_message.assert_called_once()
        call_args = mock_service.send_message.call_args
        self.assertEqual(call_args[0][3], "client_msg_456")  # client_message_id é o 4º argumento
