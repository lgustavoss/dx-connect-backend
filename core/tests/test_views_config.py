from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

from core.models import Config
from core.utils import get_or_create_config_with_defaults

Agent = get_user_model()


class ConfigViewTests(TestCase):
    """Testes para ConfigView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_config_get_authenticated(self):
        """Testa GET /api/v1/config/ com usuário autenticado"""
        response = self.client.get("/api/v1/config/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("company_data", response.data)
        self.assertIn("chat_settings", response.data)
        self.assertIn("email_settings", response.data)
        self.assertIn("appearance_settings", response.data)
        self.assertIn("whatsapp_settings", response.data)

    def test_config_get_unauthenticated(self):
        """Testa GET /api/v1/config/ sem autenticação"""
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/v1/config/")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_config_put_authenticated(self):
        """Testa PUT /api/v1/config/ com usuário autenticado"""
        data = {
            "company_data": {"nome": "Empresa Teste"},
            "chat_settings": {"max_messages_per_chat": 100},
            "email_settings": {"smtp_host": "smtp.gmail.com"},
            "appearance_settings": {"primary_color": "#007bff"},
            "whatsapp_settings": {"enabled": True}
        }
        
        response = self.client.put("/api/v1/config/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["company_data"]["nome"], "Empresa Teste")

    def test_config_put_invalid_data(self):
        """Testa PUT /api/v1/config/ com dados inválidos"""
        data = {"invalid": "data"}
        
        response = self.client.put("/api/v1/config/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CompanyConfigViewTests(TestCase):
    """Testes para CompanyConfigView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_company_config_get_authenticated(self):
        """Testa GET /api/v1/config/company/ com usuário autenticado"""
        response = self.client.get("/api/v1/config/company/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)

    def test_company_config_patch_without_permission(self):
        """Testa PATCH /api/v1/config/company/ sem permissão"""
        data = {"nome": "Nova Empresa"}
        
        response = self.client.patch("/api/v1/config/company/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_company_config_patch_with_permission(self):
        """Testa PATCH /api/v1/config/company/ com permissão"""
        # Adicionar permissão ao usuário
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_company")
        self.user.user_permissions.add(permission)
        
        data = {"nome": "Nova Empresa"}
        
        response = self.client.patch("/api/v1/config/company/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nome"], "Nova Empresa")

    def test_company_config_patch_invalid_data(self):
        """Testa PATCH /api/v1/config/company/ com dados inválidos"""
        # Adicionar permissão ao usuário
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_company")
        self.user.user_permissions.add(permission)
        
        data = {"invalid_field": "invalid_value"}
        
        response = self.client.patch("/api/v1/config/company/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ChatConfigViewTests(TestCase):
    """Testes para ChatConfigView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_chat_config_get_authenticated(self):
        """Testa GET /api/v1/config/chat/ com usuário autenticado"""
        response = self.client.get("/api/v1/config/chat/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)

    def test_chat_config_patch_without_permission(self):
        """Testa PATCH /api/v1/config/chat/ sem permissão"""
        data = {"max_messages_per_chat": 50}
        
        response = self.client.patch("/api/v1/config/chat/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_chat_config_patch_with_permission(self):
        """Testa PATCH /api/v1/config/chat/ com permissão"""
        # Adicionar permissão ao usuário
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_chat")
        self.user.user_permissions.add(permission)
        
        data = {"max_messages_per_chat": 50}
        
        response = self.client.patch("/api/v1/config/chat/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["max_messages_per_chat"], 50)


class EmailConfigViewTests(TestCase):
    """Testes para EmailConfigView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_email_config_get_authenticated(self):
        """Testa GET /api/v1/config/email/ com usuário autenticado"""
        response = self.client.get("/api/v1/config/email/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)

    def test_email_config_patch_without_permission(self):
        """Testa PATCH /api/v1/config/email/ sem permissão"""
        data = {"smtp_host": "smtp.gmail.com"}
        
        response = self.client.patch("/api/v1/config/email/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_email_config_patch_with_permission(self):
        """Testa PATCH /api/v1/config/email/ com permissão"""
        # Adicionar permissão ao usuário
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_email")
        self.user.user_permissions.add(permission)
        
        data = {"smtp_host": "smtp.gmail.com"}
        
        response = self.client.patch("/api/v1/config/email/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["smtp_host"], "smtp.gmail.com")

    def test_email_config_patch_masks_password(self):
        """Testa se PATCH mascara senha na resposta"""
        # Adicionar permissão ao usuário
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_email")
        self.user.user_permissions.add(permission)
        
        data = {"smtp_senha": "password123"}
        
        response = self.client.patch("/api/v1/config/email/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["smtp_senha"], "***")


class AppearanceConfigViewTests(TestCase):
    """Testes para AppearanceConfigView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_appearance_config_get_authenticated(self):
        """Testa GET /api/v1/config/appearance/ com usuário autenticado"""
        response = self.client.get("/api/v1/config/appearance/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)

    def test_appearance_config_patch_without_permission(self):
        """Testa PATCH /api/v1/config/appearance/ sem permissão"""
        data = {"primary_color": "#007bff"}
        
        response = self.client.patch("/api/v1/config/appearance/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_appearance_config_patch_with_permission(self):
        """Testa PATCH /api/v1/config/appearance/ com permissão"""
        # Adicionar permissão ao usuário
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_appearance")
        self.user.user_permissions.add(permission)
        
        data = {"primary_color": "#007bff"}
        
        response = self.client.patch("/api/v1/config/appearance/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["primary_color"], "#007bff")


class WhatsAppConfigViewTests(TestCase):
    """Testes para WhatsAppConfigView"""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_whatsapp_config_get_authenticated(self):
        """Testa GET /api/v1/config/whatsapp/ com usuário autenticado"""
        response = self.client.get("/api/v1/config/whatsapp/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)

    def test_whatsapp_config_patch_without_permission(self):
        """Testa PATCH /api/v1/config/whatsapp/ sem permissão"""
        data = {"enabled": True}
        
        response = self.client.patch("/api/v1/config/whatsapp/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_whatsapp_config_patch_with_permission(self):
        """Testa PATCH /api/v1/config/whatsapp/ com permissão"""
        # Adicionar permissão ao usuário
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_whatsapp")
        self.user.user_permissions.add(permission)
        
        data = {"enabled": True}
        
        response = self.client.patch("/api/v1/config/whatsapp/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["enabled"], True)

    def test_whatsapp_config_patch_masks_secrets(self):
        """Testa se PATCH mascara segredos na resposta"""
        # Adicionar permissão ao usuário
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_whatsapp")
        self.user.user_permissions.add(permission)
        
        data = {"session_data": "secret_data", "proxy_url": "secret_url"}
        
        response = self.client.patch("/api/v1/config/whatsapp/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["session_data"], "***")
        self.assertEqual(response.data["proxy_url"], "***")
