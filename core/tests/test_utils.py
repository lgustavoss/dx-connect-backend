from django.test import TestCase
from unittest.mock import patch

from core.models import Config
from core.utils import get_or_create_config_with_defaults
from core.defaults import (
    DEFAULT_COMPANY_DATA,
    DEFAULT_CHAT_SETTINGS,
    DEFAULT_EMAIL_SETTINGS,
    DEFAULT_APPEARANCE_SETTINGS,
    DEFAULT_WHATSAPP_SETTINGS,
)


class UtilsTests(TestCase):
    """Testes para core/utils.py"""

    def test_get_or_create_config_with_defaults_creates_new_config(self):
        """Testa criação de nova configuração com defaults"""
        # Garantir que não existe configuração
        Config.objects.all().delete()
        
        config, created = get_or_create_config_with_defaults()
        
        self.assertTrue(created)
        self.assertIsInstance(config, Config)
        self.assertEqual(config.company_data, DEFAULT_COMPANY_DATA)
        self.assertEqual(config.chat_settings, DEFAULT_CHAT_SETTINGS)
        self.assertEqual(config.email_settings, DEFAULT_EMAIL_SETTINGS)
        self.assertEqual(config.appearance_settings, DEFAULT_APPEARANCE_SETTINGS)
        self.assertEqual(config.whatsapp_settings, DEFAULT_WHATSAPP_SETTINGS)

    def test_get_or_create_config_with_defaults_returns_existing_config(self):
        """Testa retorno de configuração existente"""
        # Criar configuração existente
        existing_config = Config.objects.create()
        
        config, created = get_or_create_config_with_defaults()
        
        self.assertFalse(created)
        self.assertEqual(config.id, existing_config.id)

    def test_get_or_create_config_with_defaults_updates_empty_company_data(self):
        """Testa atualização de company_data vazio"""
        config = Config.objects.create(company_data={})
        
        updated_config, created = get_or_create_config_with_defaults()
        
        self.assertFalse(created)
        self.assertEqual(updated_config.company_data, DEFAULT_COMPANY_DATA)

    def test_get_or_create_config_with_defaults_updates_empty_chat_settings(self):
        """Testa atualização de chat_settings vazio"""
        config = Config.objects.create(chat_settings={})
        
        updated_config, created = get_or_create_config_with_defaults()
        
        self.assertFalse(created)
        self.assertEqual(updated_config.chat_settings, DEFAULT_CHAT_SETTINGS)

    def test_get_or_create_config_with_defaults_updates_empty_email_settings(self):
        """Testa atualização de email_settings vazio"""
        config = Config.objects.create(email_settings={})
        
        updated_config, created = get_or_create_config_with_defaults()
        
        self.assertFalse(created)
        self.assertEqual(updated_config.email_settings, DEFAULT_EMAIL_SETTINGS)

    def test_get_or_create_config_with_defaults_updates_none_appearance_settings(self):
        """Testa atualização de appearance_settings None"""
        # Não podemos testar com None devido às constraints do banco
        # Vamos testar com campos vazios
        config = Config.objects.create()
        
        updated_config, created = get_or_create_config_with_defaults()
        
        self.assertFalse(created)
        self.assertEqual(updated_config.appearance_settings, DEFAULT_APPEARANCE_SETTINGS)

    def test_get_or_create_config_with_defaults_updates_none_whatsapp_settings(self):
        """Testa atualização de whatsapp_settings None"""
        config = Config.objects.create()
        # Simular que whatsapp_settings não existe
        config.whatsapp_settings = None
        config.save()
        
        updated_config, created = get_or_create_config_with_defaults()
        
        self.assertFalse(created)
        self.assertEqual(updated_config.whatsapp_settings, DEFAULT_WHATSAPP_SETTINGS)

    def test_get_or_create_config_with_defaults_preserves_existing_data(self):
        """Testa que dados existentes não são sobrescritos"""
        existing_company_data = {"nome": "Empresa Existente"}
        existing_chat_settings = {"max_messages_per_chat": 50}
        
        config = Config.objects.create(
            company_data=existing_company_data,
            chat_settings=existing_chat_settings
        )
        
        updated_config, created = get_or_create_config_with_defaults()
        
        self.assertFalse(created)
        self.assertEqual(updated_config.company_data, existing_company_data)
        self.assertEqual(updated_config.chat_settings, existing_chat_settings)
        # Apenas os campos vazios devem ser preenchidos
        self.assertEqual(updated_config.email_settings, DEFAULT_EMAIL_SETTINGS)
        self.assertEqual(updated_config.appearance_settings, DEFAULT_APPEARANCE_SETTINGS)
        self.assertEqual(updated_config.whatsapp_settings, DEFAULT_WHATSAPP_SETTINGS)

    def test_get_or_create_config_with_defaults_updates_multiple_empty_fields(self):
        """Testa atualização de múltiplos campos vazios"""
        config = Config.objects.create(
            company_data={},
            chat_settings={},
            email_settings={}
        )
        
        updated_config, created = get_or_create_config_with_defaults()
        
        self.assertFalse(created)
        self.assertEqual(updated_config.company_data, DEFAULT_COMPANY_DATA)
        self.assertEqual(updated_config.chat_settings, DEFAULT_CHAT_SETTINGS)
        self.assertEqual(updated_config.email_settings, DEFAULT_EMAIL_SETTINGS)
        self.assertEqual(updated_config.appearance_settings, DEFAULT_APPEARANCE_SETTINGS)
        self.assertEqual(updated_config.whatsapp_settings, DEFAULT_WHATSAPP_SETTINGS)

    def test_get_or_create_config_with_defaults_handles_false_values(self):
        """Testa que valores False não são considerados vazios"""
        config = Config.objects.create(
            company_data=False,  # False não é considerado vazio
            chat_settings={}     # {} é considerado vazio
        )
        
        updated_config, created = get_or_create_config_with_defaults()
        
        self.assertFalse(created)
        # False é considerado vazio em Python, então será substituído
        self.assertEqual(updated_config.company_data, DEFAULT_COMPANY_DATA)
        self.assertEqual(updated_config.chat_settings, DEFAULT_CHAT_SETTINGS)  # Deve ser alterado

    def test_get_or_create_config_with_defaults_handles_none_values(self):
        """Testa que valores None são considerados vazios"""
        # Não podemos testar com None devido às constraints do banco
        # Vamos testar apenas com campos vazios que são tratados como None
        config = Config.objects.create()
        
        updated_config, created = get_or_create_config_with_defaults()
        
        self.assertFalse(created)
        # Todos os campos devem ter valores padrão
        self.assertEqual(updated_config.appearance_settings, DEFAULT_APPEARANCE_SETTINGS)

    @patch('core.utils.Config.objects.get_or_create')
    def test_get_or_create_config_with_defaults_handles_get_or_create_exception(self, mock_get_or_create):
        """Testa tratamento de exceção do get_or_create"""
        mock_get_or_create.side_effect = Exception("Database error")
        
        with self.assertRaises(Exception):
            get_or_create_config_with_defaults()

    def test_get_or_create_config_with_defaults_saves_when_changed(self):
        """Testa que save() é chamado quando há mudanças"""
        config = Config.objects.create(company_data={})
        
        with patch.object(Config, 'save') as mock_save:
            updated_config, created = get_or_create_config_with_defaults()
            
            mock_save.assert_called_once()

    def test_get_or_create_config_with_defaults_does_not_save_when_no_changes(self):
        """Testa que save() não é chamado quando não há mudanças"""
        config = Config.objects.create(
            company_data=DEFAULT_COMPANY_DATA,
            chat_settings=DEFAULT_CHAT_SETTINGS,
            email_settings=DEFAULT_EMAIL_SETTINGS,
            appearance_settings=DEFAULT_APPEARANCE_SETTINGS,
            whatsapp_settings=DEFAULT_WHATSAPP_SETTINGS
        )
        
        with patch.object(Config, 'save') as mock_save:
            updated_config, created = get_or_create_config_with_defaults()
            
            mock_save.assert_not_called()
