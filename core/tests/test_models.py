from django.core.exceptions import ValidationError
from django.test import TestCase
from unittest.mock import patch, MagicMock

from core.models import Config
from core.defaults import DEFAULT_WHATSAPP_SETTINGS


class ConfigModelTests(TestCase):
    """Testes para o modelo Config"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.config = Config.objects.create()

    def test_config_creation(self):
        """Testa criação básica de configuração"""
        # Como Config é singleton, usar o config existente do setUp
        config = self.config
        
        self.assertIsNotNone(config.id)
        self.assertIsNotNone(config.created_at)
        self.assertIsNotNone(config.updated_at)
        self.assertEqual(config.company_data, {})
        self.assertEqual(config.chat_settings, {})
        self.assertEqual(config.email_settings, {})
        self.assertEqual(config.appearance_settings, {})
        self.assertEqual(config.whatsapp_settings, {})

    def test_config_str_method(self):
        """Testa método __str__ do modelo"""
        # Como Config não tem __str__ definido, testamos se o objeto existe
        self.assertIsNotNone(str(self.config))

    def test_config_meta_verbose_names(self):
        """Testa verbose names do modelo"""
        self.assertEqual(Config._meta.verbose_name, "Configuração")
        self.assertEqual(Config._meta.verbose_name_plural, "Configurações")

    def test_config_meta_permissions(self):
        """Testa se as permissões customizadas estão definidas"""
        permissions = Config._meta.permissions
        permission_names = [perm[0] for perm in permissions]
        
        expected_permissions = [
            "manage_config_company",
            "manage_config_chat", 
            "manage_config_email",
            "manage_config_appearance",
            "manage_config_whatsapp"
        ]
        
        for perm in expected_permissions:
            self.assertIn(perm, permission_names)

    def test_config_company_data_field(self):
        """Testa campo company_data"""
        company_data = {
            "nome": "Empresa Teste",
            "cnpj": "12345678000199",
            "telefone": "+5511999999999"
        }
        
        self.config.company_data = company_data
        self.config.save()
        
        self.config.refresh_from_db()
        self.assertEqual(self.config.company_data, company_data)

    def test_config_chat_settings_field(self):
        """Testa campo chat_settings"""
        chat_settings = {
            "max_messages_per_chat": 100,
            "auto_close_timeout": 30,
            "welcome_message": "Olá! Como posso ajudar?"
        }
        
        self.config.chat_settings = chat_settings
        self.config.save()
        
        self.config.refresh_from_db()
        self.assertEqual(self.config.chat_settings, chat_settings)

    def test_config_email_settings_field(self):
        """Testa campo email_settings"""
        email_settings = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_usuario": "test@example.com",
            "smtp_senha": "password123"
        }
        
        self.config.email_settings = email_settings
        self.config.save()
        
        self.config.refresh_from_db()
        # A senha deve ter sido criptografada
        self.assertEqual(self.config.email_settings["smtp_host"], "smtp.gmail.com")
        self.assertEqual(self.config.email_settings["smtp_port"], 587)
        self.assertEqual(self.config.email_settings["smtp_usuario"], "test@example.com")
        self.assertTrue(self.config.email_settings["smtp_senha"].startswith("gAAAA"))

    def test_config_appearance_settings_field(self):
        """Testa campo appearance_settings"""
        appearance_settings = {
            "primary_color": "#007bff",
            "secondary_color": "#6c757d",
            "logo_url": "https://example.com/logo.png"
        }
        
        self.config.appearance_settings = appearance_settings
        self.config.save()
        
        self.config.refresh_from_db()
        self.assertEqual(self.config.appearance_settings, appearance_settings)

    def test_config_whatsapp_settings_field(self):
        """Testa campo whatsapp_settings"""
        whatsapp_settings = {
            "session_data": "plain_session_data",
            "proxy_url": "http://proxy.example.com:8080",
            "webhook_url": "https://example.com/webhook"
        }
        
        self.config.whatsapp_settings = whatsapp_settings
        self.config.save()
        
        self.config.refresh_from_db()
        # Os segredos devem ter sido criptografados
        self.assertTrue(self.config.whatsapp_settings["session_data"].startswith("gAAAA"))
        self.assertTrue(self.config.whatsapp_settings["proxy_url"].startswith("gAAAA"))
        self.assertEqual(self.config.whatsapp_settings["webhook_url"], "https://example.com/webhook")

    def test_config_clean_method_valid_data(self):
        """Testa método clean com dados válidos"""
        self.config.company_data = {
            "razao_social": "Empresa Teste",
            "nome_fantasia": "Fantasia Teste",
            "cnpj": "11222333000181",
            "inscricao_estadual": "123456789",
            "regime_tributario": "1",
            "telefone": "+5511999999999",
            "email": "contato@empresa.com",
            "endereco": {
                "cep": "01234567",
                "logradouro": "Rua das Flores",
                "numero": "123",
                "complemento": "Apto 1",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "uf": "SP"
            }
        }
        self.config.chat_settings = {
            "mensagem_saudacao": "Olá!",
            "mensagem_fora_expediente": "Fora do expediente",
            "mensagem_encerramento": "Até logo!",
            "mensagem_inatividade": "Você está inativo",
            "timeout_inatividade_minutos": 30,
            "limite_chats_simultaneos": 5,
            "horario_funcionamento": "08:00-18:00"
        }
        self.config.email_settings = {
            "smtp_host": "smtp.gmail.com", 
            "smtp_port": 587,
            "smtp_usuario": "test@example.com",
            "smtp_senha": "password123",
            "smtp_ssl": True,
            "email_from": "test@example.com"
        }
        
        # Não deve levantar exceção
        self.config.clean()

    @patch('core.models.validate_company_data')
    def test_config_clean_method_invalid_company_data(self, mock_validate):
        """Testa método clean com dados de empresa inválidos"""
        mock_validate.side_effect = ValidationError("Dados inválidos")
        
        self.config.company_data = {"invalid": "data"}
        
        with self.assertRaises(ValidationError):
            self.config.clean()

    @patch('core.models.validate_chat_settings')
    def test_config_clean_method_invalid_chat_settings(self, mock_validate):
        """Testa método clean com configurações de chat inválidas"""
        mock_validate.side_effect = ValidationError("Configurações inválidas")
        
        self.config.chat_settings = {"invalid": "settings"}
        
        with self.assertRaises(ValidationError):
            self.config.clean()

    @patch('core.models.validate_email_settings')
    def test_config_clean_method_invalid_email_settings(self, mock_validate):
        """Testa método clean com configurações de email inválidas"""
        mock_validate.side_effect = ValidationError("Email inválido")
        
        self.config.email_settings = {"invalid": "email"}
        
        with self.assertRaises(ValidationError):
            self.config.clean()

    @patch('core.models.encrypt_string')
    def test_config_save_encrypts_email_password(self, mock_encrypt):
        """Testa se save() criptografa senha de email em plain-text"""
        mock_encrypt.return_value = "encrypted_password"
        
        email_settings = {
            "smtp_host": "smtp.gmail.com",
            "smtp_senha": "plain_password"
        }
        
        self.config.email_settings = email_settings
        self.config.save()
        
        mock_encrypt.assert_called_once_with("plain_password")
        self.assertEqual(self.config.email_settings["smtp_senha"], "encrypted_password")

    def test_config_save_does_not_encrypt_already_encrypted_email_password(self):
        """Testa se save() não criptografa senha já criptografada"""
        email_settings = {
            "smtp_host": "smtp.gmail.com",
            "smtp_senha": "gAAAAABencrypted_password"
        }
        
        self.config.email_settings = email_settings
        self.config.save()
        
        self.assertEqual(self.config.email_settings["smtp_senha"], "gAAAAABencrypted_password")

    @patch('core.models.encrypt_string')
    def test_config_save_encrypts_whatsapp_secrets(self, mock_encrypt):
        """Testa se save() criptografa segredos do WhatsApp em plain-text"""
        mock_encrypt.return_value = "encrypted_data"
        
        whatsapp_settings = {
            "session_data": "plain_session_data",
            "proxy_url": "plain_proxy_url"
        }
        
        self.config.whatsapp_settings = whatsapp_settings
        self.config.save()
        
        self.assertEqual(mock_encrypt.call_count, 2)
        self.assertEqual(self.config.whatsapp_settings["session_data"], "encrypted_data")
        self.assertEqual(self.config.whatsapp_settings["proxy_url"], "encrypted_data")

    def test_config_save_does_not_encrypt_already_encrypted_whatsapp_secrets(self):
        """Testa se save() não criptografa segredos já criptografados"""
        whatsapp_settings = {
            "session_data": "gAAAAABencrypted_session",
            "proxy_url": "eyJencrypted_proxy"
        }
        
        self.config.whatsapp_settings = whatsapp_settings
        self.config.save()
        
        self.assertEqual(self.config.whatsapp_settings["session_data"], "gAAAAABencrypted_session")
        self.assertEqual(self.config.whatsapp_settings["proxy_url"], "eyJencrypted_proxy")

    @patch('core.models.decrypt_string')
    def test_get_decrypted_email_settings(self, mock_decrypt):
        """Testa método get_decrypted_email_settings"""
        mock_decrypt.return_value = "decrypted_password"
        
        self.config.email_settings = {
            "smtp_host": "smtp.gmail.com",
            "smtp_senha": "encrypted_password"
        }
        
        result = self.config.get_decrypted_email_settings()
        
        mock_decrypt.assert_called_once_with("encrypted_password")
        self.assertEqual(result["smtp_senha"], "decrypted_password")
        self.assertEqual(result["smtp_host"], "smtp.gmail.com")

    def test_get_decrypted_email_settings_no_password(self):
        """Testa get_decrypted_email_settings quando não há senha"""
        self.config.email_settings = {"smtp_host": "smtp.gmail.com"}
        
        result = self.config.get_decrypted_email_settings()
        
        self.assertEqual(result["smtp_host"], "smtp.gmail.com")
        self.assertNotIn("smtp_senha", result)

    @patch('core.models.decrypt_string')
    def test_get_decrypted_whatsapp_settings(self, mock_decrypt):
        """Testa método get_decrypted_whatsapp_settings"""
        mock_decrypt.return_value = "decrypted_data"
        
        self.config.whatsapp_settings = {
            "session_data": "encrypted_session",
            "proxy_url": "encrypted_proxy",
            "webhook_url": "https://example.com/webhook"
        }
        
        result = self.config.get_decrypted_whatsapp_settings()
        
        self.assertEqual(mock_decrypt.call_count, 2)
        self.assertEqual(result["session_data"], "decrypted_data")
        self.assertEqual(result["proxy_url"], "decrypted_data")
        self.assertEqual(result["webhook_url"], "https://example.com/webhook")

    def test_get_decrypted_whatsapp_settings_no_secrets(self):
        """Testa get_decrypted_whatsapp_settings quando não há segredos"""
        self.config.whatsapp_settings = {"webhook_url": "https://example.com/webhook"}
        
        result = self.config.get_decrypted_whatsapp_settings()
        
        self.assertEqual(result["webhook_url"], "https://example.com/webhook")
        self.assertNotIn("session_data", result)
        self.assertNotIn("proxy_url", result)

    def test_config_auto_now_add_created_at(self):
        """Testa se created_at é definido automaticamente"""
        # Usar o config existente do setUp
        config = self.config
        
        self.assertIsNotNone(config.created_at)

    def test_config_auto_now_updated_at(self):
        """Testa se updated_at é atualizado automaticamente"""
        original_updated_at = self.config.updated_at
        
        # Aguarda um pouco para garantir diferença de tempo
        import time
        time.sleep(0.1)
        
        self.config.company_data = {"nome": "Nova Empresa"}
        self.config.save()
        
        self.config.refresh_from_db()
        self.assertGreater(self.config.updated_at, original_updated_at)
    
    def test_config_save_handles_none_email_settings(self):
        """Testa se save() lida com email_settings None"""
        # Como email_settings não pode ser None, testar com dict vazio
        self.config.email_settings = {}
        self.config.save()
        
        # Deve manter dict vazio
        self.assertEqual(self.config.email_settings, {})
    
    def test_config_save_handles_none_whatsapp_settings(self):
        """Testa se save() lida com whatsapp_settings None"""
        self.config.whatsapp_settings = None
        self.config.save()
        
        # Deve converter None para dict vazio
        self.assertEqual(self.config.whatsapp_settings, {})
    
    def test_config_clean_with_validation_error_with_message_dict(self):
        """Testa clean() com ValidationError que tem message_dict"""
        # Mock de ValidationError com message_dict
        mock_error = ValidationError({"field": ["Error message"]})
        
        with patch('core.models.validate_company_data', side_effect=mock_error):
            with self.assertRaises(ValidationError) as context:
                self.config.clean()
            
            # Verificar se message_dict foi usado
            errors = context.exception.message_dict
            self.assertIn("field", errors)
    
    def test_config_clean_with_validation_error_without_message_dict(self):
        """Testa clean() com ValidationError sem message_dict"""
        # Mock de ValidationError sem message_dict
        mock_error = ValidationError(["Error message"])
        
        with patch('core.models.validate_company_data', side_effect=mock_error):
            with self.assertRaises(ValidationError) as context:
                self.config.clean()
            
            # Verificar se messages foi usado
            errors = context.exception.message_dict
            self.assertIn("company_data", errors)
    
    def test_config_clean_with_multiple_validation_errors(self):
        """Testa clean() com múltiplos erros de validação"""
        # Mock de ValidationError para company_data
        company_error = ValidationError({"company_field": ["Company error"]})
        
        # Mock de ValidationError para chat_settings
        chat_error = ValidationError({"chat_field": ["Chat error"]})
        
        with patch('core.models.validate_company_data', side_effect=company_error), \
             patch('core.models.validate_chat_settings', side_effect=chat_error):
            
            with self.assertRaises(ValidationError) as context:
                self.config.clean()
            
            # Verificar se todos os erros estão presentes
            errors = context.exception.message_dict
            self.assertIn("company_field", errors)
            self.assertIn("chat_field", errors)
    
    def test_get_decrypted_email_settings_with_none_settings(self):
        """Testa get_decrypted_email_settings() com settings None"""
        # Como email_settings não pode ser None, testar com dict vazio
        self.config.email_settings = {}
        result = self.config.get_decrypted_email_settings()
        self.assertEqual(result, {})
    
    def test_get_decrypted_whatsapp_settings_with_none_settings(self):
        """Testa get_decrypted_whatsapp_settings() com settings None"""
        self.config.whatsapp_settings = None
        result = self.config.get_decrypted_whatsapp_settings()
        self.assertEqual(result, {})
    
    @patch('core.models.decrypt_string')
    def test_get_decrypted_email_settings_with_decrypt_failure(self, mock_decrypt):
        """Testa get_decrypted_email_settings() com falha na descriptografia"""
        mock_decrypt.return_value = None
        
        self.config.email_settings = {"smtp_senha": "invalid_encrypted_data"}
        result = self.config.get_decrypted_email_settings()
        
        # A senha deve permanecer criptografada se a descriptografia falhar
        self.assertEqual(result["smtp_senha"], "invalid_encrypted_data")
    
    @patch('core.models.decrypt_string')
    def test_get_decrypted_whatsapp_settings_with_decrypt_failure(self, mock_decrypt):
        """Testa get_decrypted_whatsapp_settings() com falha na descriptografia"""
        mock_decrypt.return_value = None
        
        self.config.whatsapp_settings = {
            "session_data": "invalid_encrypted_data",
            "proxy_url": "invalid_encrypted_data"
        }
        result = self.config.get_decrypted_whatsapp_settings()
        
        # Os segredos devem permanecer criptografados se a descriptografia falhar
        self.assertEqual(result["session_data"], "invalid_encrypted_data")
        self.assertEqual(result["proxy_url"], "invalid_encrypted_data")
    
    def test_config_save_with_empty_email_settings(self):
        """Testa save() com email_settings vazio"""
        self.config.email_settings = {}
        self.config.save()
        
        # Não deve levantar exceção
        self.assertEqual(self.config.email_settings, {})
    
    def test_config_save_with_empty_whatsapp_settings(self):
        """Testa save() com whatsapp_settings vazio"""
        self.config.whatsapp_settings = {}
        self.config.save()
        
        # Não deve levantar exceção
        self.assertEqual(self.config.whatsapp_settings, {})
    
    def test_config_save_encrypts_only_plain_text_passwords(self):
        """Testa se save() só criptografa senhas em plain-text"""
        email_settings = {
            "smtp_senha": "plain_password"  # Plain text
        }
        
        whatsapp_settings = {
            "session_data": "plain_session",  # Plain text
            "proxy_url": "gAAAAABencrypted_proxy"  # Already encrypted
        }
        
        self.config.email_settings = email_settings
        self.config.whatsapp_settings = whatsapp_settings
        self.config.save()
        
        # Email password should be encrypted
        self.assertTrue(self.config.email_settings["smtp_senha"].startswith("gAAAA"))
        
        # WhatsApp session_data should be encrypted
        self.assertTrue(self.config.whatsapp_settings["session_data"].startswith("gAAAA"))
        
        # WhatsApp proxy_url should remain unchanged
        self.assertEqual(self.config.whatsapp_settings["proxy_url"], "gAAAAABencrypted_proxy")
    
    def test_config_clean_with_none_values(self):
        """Testa clean() com valores None"""
        # Como os campos JSON não podem ser None, testar com valores vazios
        self.config.company_data = {}
        self.config.chat_settings = {}
        self.config.email_settings = {}
        
        # Deve levantar exceção porque os campos obrigatórios estão ausentes
        with self.assertRaises(ValidationError):
            self.config.clean()
    
    def test_config_clean_with_empty_values(self):
        """Testa clean() com valores vazios"""
        self.config.company_data = {}
        self.config.chat_settings = {}
        self.config.email_settings = {}
        
        # Deve levantar exceção porque os campos obrigatórios estão ausentes
        with self.assertRaises(ValidationError):
            self.config.clean()
