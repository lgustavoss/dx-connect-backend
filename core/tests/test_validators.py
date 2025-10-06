from django.core.exceptions import ValidationError
from django.test import TestCase
from unittest.mock import patch

from core.validators import (
    validate_company_data,
    validate_chat_settings,
    validate_email_settings,
    validate_whatsapp_settings,
    _require_keys,
)


class ValidatorsTests(TestCase):
    """Testes para core/validators.py"""

    def test_require_keys_missing_required_field(self):
        """Testa _require_keys com campo obrigatório ausente"""
        data = {"field1": "value1"}
        required = {"field1": True, "field2": True}
        
        with self.assertRaises(ValidationError) as cm:
            _require_keys(data, required)
        
        self.assertIn("field2", str(cm.exception))

    def test_require_keys_missing_required_field_with_path(self):
        """Testa _require_keys com campo obrigatório ausente e path"""
        data = {"field1": "value1"}
        required = {"field1": True, "field2": True}
        
        with self.assertRaises(ValidationError) as cm:
            _require_keys(data, required, "prefix.")
        
        self.assertIn("prefix.field2", str(cm.exception))

    def test_require_keys_optional_field_missing(self):
        """Testa _require_keys com campo opcional ausente (não deve falhar)"""
        data = {"field1": "value1"}
        required = {"field1": True, "field2": False}
        
        # Não deve levantar exceção
        _require_keys(data, required)

    def test_require_keys_all_fields_present(self):
        """Testa _require_keys com todos os campos presentes"""
        data = {"field1": "value1", "field2": "value2"}
        required = {"field1": True, "field2": True}
        
        # Não deve levantar exceção
        _require_keys(data, required)

    def test_validate_company_data_not_dict(self):
        """Testa validate_company_data com dados que não são dict"""
        with self.assertRaises(ValidationError) as cm:
            validate_company_data("not a dict")
        
        self.assertIn("Deve ser um objeto", str(cm.exception))

    def test_validate_company_data_missing_required_fields(self):
        """Testa validate_company_data com campos obrigatórios ausentes"""
        data = {"razao_social": "Empresa Teste"}
        
        with self.assertRaises(ValidationError) as cm:
            validate_company_data(data)
        
        # Deve conter erros para campos obrigatórios ausentes
        self.assertIn("nome_fantasia", str(cm.exception))

    @patch('core.validators.validate_cnpj')
    def test_validate_company_data_invalid_cnpj(self, mock_validate_cnpj):
        """Testa validate_company_data com CNPJ inválido"""
        mock_validate_cnpj.side_effect = ValidationError("CNPJ inválido")
        data = {
            "razao_social": "Empresa Teste",
            "nome_fantasia": "Fantasia",
            "cnpj": "12345678901234",
            "inscricao_estadual": "123456789",
            "regime_tributario": "1",
            "telefone": "11999999999",
            "email": "test@example.com",
            "endereco": {
                "cep": "12345678",
                "logradouro": "Rua Teste",
                "numero": "123",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "uf": "SP"
            }
        }
        
        with self.assertRaises(ValidationError) as cm:
            validate_company_data(data)
        
        self.assertIn("CNPJ inválido", str(cm.exception))

    @patch('core.validators.validate_cnpj')
    def test_validate_company_data_invalid_regime_tributario(self, mock_validate_cnpj):
        """Testa validate_company_data com regime tributário inválido"""
        data = {
            "razao_social": "Empresa Teste",
            "nome_fantasia": "Fantasia",
            "cnpj": "12345678901234",
            "inscricao_estadual": "123456789",
            "regime_tributario": "4",  # Inválido
            "telefone": "11999999999",
            "email": "test@example.com",
            "endereco": {
                "cep": "12345678",
                "logradouro": "Rua Teste",
                "numero": "123",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "uf": "SP"
            }
        }
        
        with self.assertRaises(ValidationError) as cm:
            validate_company_data(data)
        
        self.assertIn("Valor inválido", str(cm.exception))

    @patch('core.validators.validate_cnpj')
    def test_validate_company_data_invalid_email(self, mock_validate_cnpj):
        """Testa validate_company_data com email inválido"""
        data = {
            "razao_social": "Empresa Teste",
            "nome_fantasia": "Fantasia",
            "cnpj": "12345678901234",
            "inscricao_estadual": "123456789",
            "regime_tributario": "1",
            "telefone": "11999999999",
            "email": "invalid-email",  # Inválido
            "endereco": {
                "cep": "12345678",
                "logradouro": "Rua Teste",
                "numero": "123",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "uf": "SP"
            }
        }
        
        with self.assertRaises(ValidationError) as cm:
            validate_company_data(data)
        
        self.assertIn("email", str(cm.exception))

    @patch('core.validators.validate_cnpj')
    def test_validate_company_data_invalid_cep(self, mock_validate_cnpj):
        """Testa validate_company_data com CEP inválido"""
        data = {
            "razao_social": "Empresa Teste",
            "nome_fantasia": "Fantasia",
            "cnpj": "12345678901234",
            "inscricao_estadual": "123456789",
            "regime_tributario": "1",
            "telefone": "11999999999",
            "email": "test@example.com",
            "endereco": {
                "cep": "12345",  # Inválido (menos de 8 dígitos)
                "logradouro": "Rua Teste",
                "numero": "123",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "uf": "SP"
            }
        }
        
        with self.assertRaises(ValidationError) as cm:
            validate_company_data(data)
        
        self.assertIn("CEP deve conter 8 dígitos", str(cm.exception))

    @patch('core.validators.validate_cnpj')
    @patch('core.validators.validate_uf')
    def test_validate_company_data_invalid_uf(self, mock_validate_uf, mock_validate_cnpj):
        """Testa validate_company_data com UF inválida"""
        mock_validate_uf.side_effect = ValidationError("UF inválida")
        data = {
            "razao_social": "Empresa Teste",
            "nome_fantasia": "Fantasia",
            "cnpj": "12345678901234",
            "inscricao_estadual": "123456789",
            "regime_tributario": "1",
            "telefone": "11999999999",
            "email": "test@example.com",
            "endereco": {
                "cep": "12345678",
                "logradouro": "Rua Teste",
                "numero": "123",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "uf": "XX"  # Inválida
            }
        }
        
        with self.assertRaises(ValidationError) as cm:
            validate_company_data(data)
        
        self.assertIn("UF inválida", str(cm.exception))

    @patch('core.validators.validate_cnpj')
    @patch('core.validators.validate_uf')
    def test_validate_company_data_valid(self, mock_validate_uf, mock_validate_cnpj):
        """Testa validate_company_data com dados válidos"""
        data = {
            "razao_social": "Empresa Teste",
            "nome_fantasia": "Fantasia",
            "cnpj": "12345678901234",
            "inscricao_estadual": "123456789",
            "regime_tributario": "1",
            "telefone": "11999999999",
            "email": "test@example.com",
            "endereco": {
                "cep": "12345678",
                "logradouro": "Rua Teste",
                "numero": "123",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "uf": "SP"
            }
        }
        
        # Não deve levantar exceção
        validate_company_data(data)

    def test_validate_chat_settings_not_dict(self):
        """Testa validate_chat_settings com dados que não são dict"""
        with self.assertRaises(ValidationError) as cm:
            validate_chat_settings("not a dict")
        
        self.assertIn("Deve ser um objeto", str(cm.exception))

    def test_validate_chat_settings_missing_required_fields(self):
        """Testa validate_chat_settings com campos obrigatórios ausentes"""
        data = {"mensagem_saudacao": "Olá"}
        
        with self.assertRaises(ValidationError) as cm:
            validate_chat_settings(data)
        
        # Deve conter erros para campos obrigatórios ausentes
        self.assertIn("mensagem_fora_expediente", str(cm.exception))

    def test_validate_chat_settings_valid(self):
        """Testa validate_chat_settings com dados válidos"""
        data = {
            "mensagem_saudacao": "Olá",
            "mensagem_fora_expediente": "Fora do expediente",
            "mensagem_encerramento": "Até logo",
            "mensagem_inatividade": "Inativo",
            "timeout_inatividade_minutos": 30,
            "limite_chats_simultaneos": 5,
            "horario_funcionamento": "9h às 18h"
        }
        
        # Não deve levantar exceção
        validate_chat_settings(data)

    def test_validate_email_settings_not_dict(self):
        """Testa validate_email_settings com dados que não são dict"""
        with self.assertRaises(ValidationError) as cm:
            validate_email_settings("not a dict")
        
        self.assertIn("Deve ser um objeto", str(cm.exception))

    def test_validate_email_settings_missing_required_fields(self):
        """Testa validate_email_settings com campos obrigatórios ausentes"""
        data = {"smtp_host": "smtp.gmail.com"}
        
        with self.assertRaises(ValidationError) as cm:
            validate_email_settings(data)
        
        # Deve conter erros para campos obrigatórios ausentes
        self.assertIn("smtp_port", str(cm.exception))

    def test_validate_email_settings_invalid_email_from(self):
        """Testa validate_email_settings com email_from inválido"""
        data = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_usuario": "user",
            "smtp_senha": "pass",
            "smtp_ssl": True,
            "email_from": "invalid-email"  # Inválido
        }
        
        with self.assertRaises(ValidationError) as cm:
            validate_email_settings(data)
        
        # O erro vem do EmailValidator, não do campo específico
        self.assertIn("Insira um endereço de email válido", str(cm.exception))

    def test_validate_email_settings_empty_email_from(self):
        """Testa validate_email_settings com email_from vazio (deve passar)"""
        data = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_usuario": "user",
            "smtp_senha": "pass",
            "smtp_ssl": True,
            "email_from": ""  # Vazio, deve passar
        }
        
        # Não deve levantar exceção
        validate_email_settings(data)

    def test_validate_email_settings_valid(self):
        """Testa validate_email_settings com dados válidos"""
        data = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_usuario": "user",
            "smtp_senha": "pass",
            "smtp_ssl": True,
            "email_from": "test@example.com"
        }
        
        # Não deve levantar exceção
        validate_email_settings(data)

    def test_validate_whatsapp_settings_not_dict(self):
        """Testa validate_whatsapp_settings com dados que não são dict"""
        with self.assertRaises(ValidationError) as cm:
            validate_whatsapp_settings("not a dict")
        
        self.assertIn("Deve ser um objeto", str(cm.exception))

    def test_validate_whatsapp_settings_missing_required_fields(self):
        """Testa validate_whatsapp_settings com campos obrigatórios ausentes"""
        data = {"enabled": True}
        
        with self.assertRaises(ValidationError) as cm:
            validate_whatsapp_settings(data)
        
        # Deve conter erros para campos obrigatórios ausentes
        self.assertIn("device_name", str(cm.exception))

    def test_validate_whatsapp_settings_negative_reconnect_backoff(self):
        """Testa validate_whatsapp_settings com reconnect_backoff_seconds negativo"""
        data = {
            "enabled": True,
            "device_name": "Test Device",
            "stealth_mode": False,
            "human_delays": True,
            "reconnect_backoff_seconds": -1  # Negativo
        }
        
        with self.assertRaises(ValidationError) as cm:
            validate_whatsapp_settings(data)
        
        self.assertIn("Deve ser >= 0", str(cm.exception))

    def test_validate_whatsapp_settings_valid(self):
        """Testa validate_whatsapp_settings com dados válidos"""
        data = {
            "enabled": True,
            "device_name": "Test Device",
            "stealth_mode": False,
            "human_delays": True,
            "reconnect_backoff_seconds": 30,
            "session_data": "encrypted_data",
            "proxy_url": "http://proxy.example.com"
        }
        
        # Não deve levantar exceção
        validate_whatsapp_settings(data)

    def test_validate_whatsapp_settings_without_optional_fields(self):
        """Testa validate_whatsapp_settings sem campos opcionais"""
        data = {
            "enabled": True,
            "device_name": "Test Device",
            "stealth_mode": False,
            "human_delays": True,
            "reconnect_backoff_seconds": 30
        }
        
        # Não deve levantar exceção
        validate_whatsapp_settings(data)

    def test_validate_company_data_with_optional_fields(self):
        """Testa validate_company_data com campos opcionais"""
        data = {
            "razao_social": "Empresa Teste",
            "nome_fantasia": "Fantasia",
            "cnpj": "12345678901234",
            "inscricao_estadual": "123456789",
            "inscricao_municipal": "123456",  # Opcional
            "regime_tributario": "1",
            "cnae_principal": "1234567",  # Opcional
            "telefone": "11999999999",
            "email": "test@example.com",
            "site": "https://example.com",  # Opcional
            "endereco": {
                "cep": "12345678",
                "logradouro": "Rua Teste",
                "numero": "123",
                "complemento": "Sala 1",  # Opcional
                "bairro": "Centro",
                "cidade": "São Paulo",
                "uf": "SP"
            }
        }
        
        with patch('core.validators.validate_cnpj'), \
             patch('core.validators.validate_uf'):
            # Não deve levantar exceção
            validate_company_data(data)
