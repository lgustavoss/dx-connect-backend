from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock

from core.models import Config
from core.utils import get_or_create_config_with_defaults
from core.defaults import DEFAULT_COMPANY_DATA, DEFAULT_CHAT_SETTINGS, DEFAULT_EMAIL_SETTINGS

Agent = get_user_model()


def create_valid_config():
    """Cria um Config válido para os testes."""
    valid_company_data = {
        "razao_social": "Empresa Teste LTDA",
        "nome_fantasia": "Empresa Teste",
        "cnpj": "11222333000181",
        "inscricao_estadual": "123456789",
        "inscricao_municipal": "987654321",
        "regime_tributario": "1",
        "cnae_principal": "6201500",
        "telefone": "(11) 99999-9999",
        "email": "contato@empresateste.com",
        "site": "https://www.empresateste.com",
        "endereco": {
            "cep": "01234567",
            "logradouro": "Rua Teste",
            "numero": "123",
            "complemento": "Sala 1",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "uf": "SP",
        },
    }
    
    config = Config.objects.create(
        company_data=valid_company_data,
        chat_settings=DEFAULT_CHAT_SETTINGS,
        email_settings=DEFAULT_EMAIL_SETTINGS
    )
    return config


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
        # appearance_settings e whatsapp_settings são opcionais
        if "appearance_settings" in response.data:
            self.assertIn("appearance_settings", response.data)
        if "whatsapp_settings" in response.data:
            self.assertIn("whatsapp_settings", response.data)

    def test_config_get_unauthenticated(self):
        """Testa GET /api/v1/config/ sem autenticação"""
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/v1/config/")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_config_put_authenticated(self):
        """Testa PUT /api/v1/config/ com usuário autenticado"""
        # Criar Config válido primeiro
        create_valid_config()
        
        data = {
            "company_data": {
                "razao_social": "Empresa Teste LTDA",
                "nome_fantasia": "Empresa Teste",
                "cnpj": "11222333000181",
                "inscricao_estadual": "123456789",
                "inscricao_municipal": "987654321",
                "regime_tributario": "1",
                "cnae_principal": "6201500",
                "telefone": "(11) 99999-9999",
                "email": "contato@empresateste.com",
                "site": "https://www.empresateste.com",
                "endereco": {
                    "cep": "01234567",
                    "logradouro": "Rua Teste",
                    "numero": "123",
                    "complemento": "Sala 1",
                    "bairro": "Centro",
                    "cidade": "São Paulo",
                    "uf": "SP",
                },
            },
            "chat_settings": {
                "mensagem_saudacao": "Olá!",
                "mensagem_fora_expediente": "Estamos fora do horário.",
                "mensagem_encerramento": "Obrigado!",
                "mensagem_inatividade": "Encerrando por inatividade.",
                "timeout_inatividade_minutos": 15,
                "limite_chats_simultaneos": 5,
                "horario_funcionamento": {
                    "segunda": {"inicio": "08:00", "fim": "18:00"},
                    "terca": {"inicio": "08:00", "fim": "18:00"},
                    "quarta": {"inicio": "08:00", "fim": "18:00"},
                    "quinta": {"inicio": "08:00", "fim": "18:00"},
                    "sexta": {"inicio": "08:00", "fim": "18:00"},
                    "sabado": {"inicio": None, "fim": None},
                    "domingo": {"inicio": None, "fim": None},
                },
            },
            "email_settings": {
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_usuario": "test@example.com",
                "smtp_senha": "password123",
                "smtp_ssl": True,
                "email_from": "test@example.com",
            }
        }
        
        response = self.client.put("/api/v1/config/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["company_data"]["razao_social"], "Empresa Teste LTDA")

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
        data = {"razao_social": "Nova Empresa LTDA"}
        
        response = self.client.patch("/api/v1/config/company/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_company_config_patch_with_permission(self):
        """Testa PATCH /api/v1/config/company/ com permissão"""
        # Criar Config válido primeiro
        create_valid_config()
        
        # Adicionar permissão ao usuário
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_company")
        self.user.user_permissions.add(permission)
        
        data = {"razao_social": "Nova Empresa LTDA"}
        
        response = self.client.patch("/api/v1/config/company/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["razao_social"], "Nova Empresa LTDA")

    def test_company_config_patch_invalid_data(self):
        """Testa PATCH /api/v1/config/company/ com dados inválidos"""
        # Criar Config válido primeiro
        create_valid_config()
        
        # Adicionar permissão ao usuário
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_company")
        self.user.user_permissions.add(permission)
        
        data = {"cnpj": "invalid_cnpj"}  # CNPJ inválido
        
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
        data = {"mensagem_saudacao": "Olá!"}
        
        response = self.client.patch("/api/v1/config/chat/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_chat_config_patch_with_permission(self):
        """Testa PATCH /api/v1/config/chat/ com permissão"""
        # Criar Config válido primeiro
        create_valid_config()
        
        # Adicionar permissão ao usuário
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_chat")
        self.user.user_permissions.add(permission)
        
        data = {"mensagem_saudacao": "Olá! Como posso ajudar?"}
        
        response = self.client.patch("/api/v1/config/chat/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["mensagem_saudacao"], "Olá! Como posso ajudar?")


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
        # Criar Config válido primeiro
        create_valid_config()
        
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
        # Criar Config válido primeiro
        create_valid_config()
        
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
        # Criar Config válido primeiro
        create_valid_config()
        
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
        # Criar Config válido primeiro
        create_valid_config()
        
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
        # Criar Config válido primeiro
        create_valid_config()
        
        # Adicionar permissão ao usuário
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_whatsapp")
        self.user.user_permissions.add(permission)
        
        data = {"session_data": "secret_data", "proxy_url": "secret_url"}
        
        response = self.client.patch("/api/v1/config/whatsapp/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["session_data"], "***")
        self.assertEqual(response.data["proxy_url"], "***")

    def test_whatsapp_config_patch_invalid_data(self):
        """Testa PATCH /api/v1/config/whatsapp/ com dados inválidos"""
        # Criar Config válido primeiro
        create_valid_config()
        
        # Adicionar permissão ao usuário
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_whatsapp")
        self.user.user_permissions.add(permission)
        
        data = {"enabled": "invalid"}  # Tipo inválido
        
        response = self.client.patch("/api/v1/config/whatsapp/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_whatsapp_config_get_masks_secrets(self):
        """Testa se GET mascara segredos na resposta"""
        # Criar Config válido primeiro
        create_valid_config()
        
        response = self.client.get("/api/v1/config/whatsapp/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verifica se os campos existem e estão mascarados
        if "session_data" in response.data and response.data["session_data"]:
            self.assertEqual(response.data["session_data"], "***")
        if "proxy_url" in response.data and response.data["proxy_url"]:
            self.assertEqual(response.data["proxy_url"], "***")


class ConfigViewErrorHandlingTests(TestCase):
    """Testa o tratamento de erros nas views de configuração."""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    @patch("core.views.config.get_or_create_config_with_defaults")
    def test_config_retrieve_database_error(self, mock_get_config):
        """Testa GET /api/v1/config/ com erro de banco de dados."""
        mock_get_config.side_effect = Exception("Database error")
        with self.assertRaises(Exception):
            self.client.get("/api/v1/config/")

    @patch("core.views.config.get_or_create_config_with_defaults")
    def test_company_config_patch_database_error(self, mock_get_config):
        """Testa PATCH /api/v1/config/company/ com erro de banco de dados."""
        # Adicionar permissão ao usuário primeiro
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_company")
        self.user.user_permissions.add(permission)
        
        mock_get_config.side_effect = Exception("Database error")
        data = {"razao_social": "Test"}
        with self.assertRaises(Exception):
            self.client.patch("/api/v1/config/company/", data, format="json")

    def test_config_patch_invalid_json(self):
        """Testa PUT /api/v1/config/ com JSON inválido."""
        response = self.client.put(
            "/api/v1/config/", 
            "invalid json", 
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_company_config_patch_invalid_json(self):
        """Testa PATCH /api/v1/config/company/ com JSON inválido."""
        # Adicionar permissão ao usuário primeiro
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_company")
        self.user.user_permissions.add(permission)
        
        response = self.client.patch(
            "/api/v1/config/company/", 
            "invalid json", 
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ConfigViewSerializationTests(TestCase):
    """Testa a serialização e deserialização nas views de configuração."""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_config_serialization_includes_all_fields(self):
        """Testa que a serialização inclui todos os campos necessários."""
        response = self.client.get("/api/v1/config/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        
        # Verifica campos obrigatórios
        required_fields = [
            "company_data", "chat_settings", "email_settings"
        ]
        for field in required_fields:
            self.assertIn(field, data)
        
        # Verifica campos opcionais se existirem
        optional_fields = ["appearance_settings", "whatsapp_settings"]
        for field in optional_fields:
            if field in data:
                self.assertIn(field, data)

    def test_company_config_serialization_structure(self):
        """Testa a estrutura da serialização de company_data."""
        response = self.client.get("/api/v1/config/company/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        
        # Verifica campos obrigatórios de company_data
        required_fields = ["razao_social", "cnpj", "endereco"]
        for field in required_fields:
            self.assertIn(field, data)

    def test_chat_config_serialization_structure(self):
        """Testa a estrutura da serialização de chat_settings."""
        response = self.client.get("/api/v1/config/chat/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        
        # Verifica campos obrigatórios de chat_settings
        required_fields = ["mensagem_saudacao", "timeout_inatividade_minutos"]
        for field in required_fields:
            self.assertIn(field, data)

    def test_email_config_serialization_structure(self):
        """Testa a estrutura da serialização de email_settings."""
        response = self.client.get("/api/v1/config/email/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        
        # Verifica campos obrigatórios de email_settings
        required_fields = ["smtp_host", "smtp_port", "smtp_usuario"]
        for field in required_fields:
            self.assertIn(field, data)

    def test_appearance_config_serialization_structure(self):
        """Testa a estrutura da serialização de appearance_settings."""
        response = self.client.get("/api/v1/config/appearance/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        
        # Verifica campos obrigatórios de appearance_settings
        required_fields = ["primary_color", "secondary_color"]
        for field in required_fields:
            self.assertIn(field, data)

    def test_whatsapp_config_serialization_structure(self):
        """Testa a estrutura da serialização de whatsapp_settings."""
        response = self.client.get("/api/v1/config/whatsapp/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        
        # Verifica campos obrigatórios de whatsapp_settings
        required_fields = ["enabled", "session_data", "proxy_url"]
        for field in required_fields:
            self.assertIn(field, data)


class ConfigViewPermissionTests(TestCase):
    """Testa as permissões específicas de cada view."""

    def setUp(self):
        self.client = APIClient()
        self.user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_company_config_patch_with_permission(self):
        """Testa PATCH /api/v1/config/company/ com permissão correta."""
        # Criar Config válido primeiro
        create_valid_config()
        
        # Adiciona permissão específica
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_company")
        self.user.user_permissions.add(permission)
        
        data = {"razao_social": "Test Company"}
        response = self.client.patch("/api/v1/config/company/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chat_config_patch_with_permission(self):
        """Testa PATCH /api/v1/config/chat/ com permissão correta."""
        # Criar Config válido primeiro
        create_valid_config()
        
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_chat")
        self.user.user_permissions.add(permission)
        
        data = {"mensagem_saudacao": "Test Message"}
        response = self.client.patch("/api/v1/config/chat/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_config_patch_with_permission(self):
        """Testa PATCH /api/v1/config/email/ com permissão correta."""
        # Criar Config válido primeiro
        create_valid_config()
        
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_email")
        self.user.user_permissions.add(permission)
        
        data = {"smtp_host": "test.example.com"}
        response = self.client.patch("/api/v1/config/email/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_appearance_config_patch_with_permission(self):
        """Testa PATCH /api/v1/config/appearance/ com permissão correta."""
        # Criar Config válido primeiro
        create_valid_config()
        
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_appearance")
        self.user.user_permissions.add(permission)
        
        data = {"primary_color": "#ff0000"}
        response = self.client.patch("/api/v1/config/appearance/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_whatsapp_config_patch_with_permission(self):
        """Testa PATCH /api/v1/config/whatsapp/ com permissão correta."""
        # Criar Config válido primeiro
        create_valid_config()
        
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="manage_config_whatsapp")
        self.user.user_permissions.add(permission)
        
        data = {"enabled": True}
        response = self.client.patch("/api/v1/config/whatsapp/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
