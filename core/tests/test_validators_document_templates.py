"""
Testes unitários para validators de templates de documentos.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError

from core.validators import validate_document_templates


class ValidateDocumentTemplatesTests(TestCase):
    """Testes para validate_document_templates."""
    
    def test_validate_document_templates_valid_data(self):
        """Testa validação com dados válidos."""
        valid_data = {
            "contrato_padrao": {
                "nome": "Contrato Padrão",
                "tipo": "contrato",
                "conteudo": "CONTRATO\nCONTRATANTE: {{cliente_nome}}\nCONTRATADA: {{empresa_nome}}"
            },
            "boleto_padrao": {
                "nome": "Boleto Padrão",
                "tipo": "boleto",
                "conteudo": "BOLETO\nCliente: {{cliente_nome}}\nEmpresa: {{empresa_nome}}"
            }
        }
        
        # Não deve levantar exceção
        try:
            validate_document_templates(valid_data)
        except ValidationError:
            self.fail("validate_document_templates levantou ValidationError com dados válidos")
    
    def test_validate_document_templates_invalid_type(self):
        """Testa validação com tipo de dados inválido."""
        invalid_data = "string_instead_of_dict"
        
        with self.assertRaises(ValidationError) as context:
            validate_document_templates(invalid_data)
        
        self.assertIn('document_templates', str(context.exception))
        self.assertIn('Deve ser um objeto', str(context.exception))
    
    def test_validate_document_templates_template_not_dict(self):
        """Testa validação quando template não é um dicionário."""
        invalid_data = {
            "contrato_padrao": "string_instead_of_dict"
        }
        
        with self.assertRaises(ValidationError) as context:
            validate_document_templates(invalid_data)
        
        self.assertIn('document_templates.contrato_padrao', str(context.exception))
        self.assertIn('Template deve ser um objeto', str(context.exception))
    
    def test_validate_document_templates_missing_required_fields(self):
        """Testa validação quando campos obrigatórios estão ausentes."""
        invalid_data = {
            "contrato_padrao": {
                "nome": "Contrato Padrão"
                # Faltam 'tipo' e 'conteudo'
            }
        }
        
        with self.assertRaises(ValidationError) as context:
            validate_document_templates(invalid_data)
        
        error_message = str(context.exception)
        self.assertIn('document_templates.contrato_padrao.tipo', error_message)
        self.assertIn('Campo obrigatório ausente', error_message)
    
    def test_validate_document_templates_invalid_tipo(self):
        """Testa validação com tipo inválido."""
        invalid_data = {
            "contrato_padrao": {
                "nome": "Contrato Padrão",
                "tipo": "tipo_inexistente",
                "conteudo": "CONTRATO\n{{cliente_nome}}\n{{empresa_nome}}"
            }
        }
        
        with self.assertRaises(ValidationError) as context:
            validate_document_templates(invalid_data)
        
        error_message = str(context.exception)
        self.assertIn('document_templates.contrato_padrao.tipo', error_message)
        self.assertIn('Tipo deve ser um dos seguintes: contrato, boleto, proposta, certificado', error_message)
    
    def test_validate_document_templates_valid_tipos(self):
        """Testa validação com tipos válidos."""
        # Testa um tipo por vez para isolar o problema
        data = {
            "template_contrato": {
                "nome": "Template Contrato",
                "tipo": "contrato",
                "conteudo": "{{cliente_nome}} {{empresa_nome}}"
            }
        }
        
        # Não deve levantar exceção
        try:
            validate_document_templates(data)
        except ValidationError as e:
            self.fail(f"validate_document_templates levantou ValidationError para tipo válido 'contrato': {e}")
        
        # Testa outro tipo
        data = {
            "template_boleto": {
                "nome": "Template Boleto",
                "tipo": "boleto",
                "conteudo": "{{cliente_nome}} {{empresa_nome}}"
            }
        }
        
        try:
            validate_document_templates(data)
        except ValidationError as e:
            self.fail(f"validate_document_templates levantou ValidationError para tipo válido 'boleto': {e}")
    
    def test_validate_document_templates_empty_conteudo(self):
        """Testa validação com conteúdo vazio."""
        invalid_data = {
            "contrato_padrao": {
                "nome": "Contrato Padrão",
                "tipo": "contrato",
                "conteudo": ""  # Conteúdo vazio
            }
        }
        
        with self.assertRaises(ValidationError) as context:
            validate_document_templates(invalid_data)
        
        error_message = str(context.exception)
        self.assertIn('document_templates.contrato_padrao.conteudo', error_message)
        self.assertIn('Conteúdo do template é obrigatório', error_message)
    
    def test_validate_document_templates_conteudo_not_string(self):
        """Testa validação com conteúdo que não é string."""
        invalid_data = {
            "contrato_padrao": {
                "nome": "Contrato Padrão",
                "tipo": "contrato",
                "conteudo": 123  # Não é string
            }
        }
        
        with self.assertRaises(ValidationError) as context:
            validate_document_templates(invalid_data)
        
        error_message = str(context.exception)
        self.assertIn('document_templates.contrato_padrao.conteudo', error_message)
        self.assertIn('Conteúdo do template é obrigatório', error_message)
    
    def test_validate_document_templates_missing_cliente_nome_variable(self):
        """Testa validação quando falta variável obrigatória cliente_nome."""
        invalid_data = {
            "contrato_padrao": {
                "nome": "Contrato Padrão",
                "tipo": "contrato",
                "conteudo": "CONTRATO\nCONTRATADA: {{empresa_nome}}"  # Falta {{cliente_nome}}
            }
        }
        
        with self.assertRaises(ValidationError) as context:
            validate_document_templates(invalid_data)
        
        error_message = str(context.exception)
        self.assertIn('document_templates.contrato_padrao.conteudo', error_message)
        self.assertIn('Template deve conter a variável {{cliente_nome}}', error_message)
    
    def test_validate_document_templates_missing_empresa_nome_variable(self):
        """Testa validação quando falta variável obrigatória empresa_nome."""
        invalid_data = {
            "contrato_padrao": {
                "nome": "Contrato Padrão",
                "tipo": "contrato",
                "conteudo": "CONTRATO\nCONTRATANTE: {{cliente_nome}}"  # Falta {{empresa_nome}}
            }
        }
        
        with self.assertRaises(ValidationError) as context:
            validate_document_templates(invalid_data)
        
        error_message = str(context.exception)
        self.assertIn('document_templates.contrato_padrao.conteudo', error_message)
        self.assertIn('Template deve conter a variável {{empresa_nome}}', error_message)
    
    def test_validate_document_templates_multiple_templates_valid(self):
        """Testa validação com múltiplos templates válidos."""
        valid_data = {
            "contrato_padrao": {
                "nome": "Contrato Padrão",
                "tipo": "contrato",
                "conteudo": "CONTRATO\nCONTRATANTE: {{cliente_nome}}\nCONTRATADA: {{empresa_nome}}"
            },
            "boleto_padrao": {
                "nome": "Boleto Padrão",
                "tipo": "boleto",
                "conteudo": "BOLETO\nCliente: {{cliente_nome}}\nEmpresa: {{empresa_nome}}"
            },
            "proposta_padrao": {
                "nome": "Proposta Padrão",
                "tipo": "proposta",
                "conteudo": "PROPOSTA\nPara: {{cliente_nome}}\nDe: {{empresa_nome}}"
            }
        }
        
        # Não deve levantar exceção
        try:
            validate_document_templates(valid_data)
        except ValidationError:
            self.fail("validate_document_templates levantou ValidationError com múltiplos templates válidos")
    
    def test_validate_document_templates_multiple_templates_one_invalid(self):
        """Testa validação com múltiplos templates, um inválido."""
        invalid_data = {
            "contrato_padrao": {
                "nome": "Contrato Padrão",
                "tipo": "contrato",
                "conteudo": "CONTRATO\n{{cliente_nome}}\n{{empresa_nome}}"
            },
            "boleto_padrao": {
                "nome": "Boleto Padrão",
                "tipo": "tipo_invalido",  # Tipo inválido
                "conteudo": "BOLETO\n{{cliente_nome}}\n{{empresa_nome}}"
            }
        }
        
        with self.assertRaises(ValidationError) as context:
            validate_document_templates(invalid_data)
        
        error_message = str(context.exception)
        self.assertIn('document_templates.boleto_padrao.tipo', error_message)
        self.assertIn('Tipo deve ser um dos seguintes', error_message)
    
    def test_validate_document_templates_empty_dict(self):
        """Testa validação com dicionário vazio."""
        empty_data = {}
        
        # Dicionário vazio deve ser válido (sem templates)
        try:
            validate_document_templates(empty_data)
        except ValidationError:
            self.fail("validate_document_templates levantou ValidationError com dicionário vazio")
    
    def test_validate_document_templates_whitespace_conteudo(self):
        """Testa validação com conteúdo apenas com espaços em branco."""
        invalid_data = {
            "contrato_padrao": {
                "nome": "Contrato Padrão",
                "tipo": "contrato",
                "conteudo": "   \n\t  "  # Apenas espaços em branco
            }
        }
        
        with self.assertRaises(ValidationError) as context:
            validate_document_templates(invalid_data)
        
        error_message = str(context.exception)
        self.assertIn('document_templates.contrato_padrao.conteudo', error_message)
        self.assertIn('Conteúdo do template é obrigatório', error_message)
    
    def test_validate_document_templates_case_sensitive_variables(self):
        """Testa que variáveis são case-sensitive."""
        invalid_data = {
            "contrato_padrao": {
                "nome": "Contrato Padrão",
                "tipo": "contrato",
                "conteudo": "CONTRATO\n{{CLIENTE_NOME}}\n{{EMPRESA_NOME}}"  # Maiúsculas
            }
        }
        
        with self.assertRaises(ValidationError) as context:
            validate_document_templates(invalid_data)
        
        error_message = str(context.exception)
        self.assertIn('Template deve conter a variável {{cliente_nome}}', error_message)
    
    def test_validate_document_templates_complex_conteudo(self):
        """Testa validação com conteúdo complexo válido."""
        complex_data = {
            "contrato_completo": {
                "nome": "Contrato Completo",
                "tipo": "contrato",
                "conteudo": """
CONTRATO DE PRESTAÇÃO DE SERVIÇOS

CONTRATANTE: {{cliente_nome}}
CNPJ: {{cliente_cnpj}}
Endereço: {{cliente_endereco}}

CONTRATADA: {{empresa_nome}}
CNPJ: {{empresa_cnpj}}
Endereço: {{empresa_endereco}}

OBJETO: Prestação de serviços conforme especificado.

VALOR: R$ {{valor_servico}}
VIGÊNCIA: {{data_inicio}} a {{data_fim}}

Cláusulas especiais:
1. O contratante se compromete ao pagamento.
2. A contratada prestará serviços conforme acordado.

{{data_contrato}}

________________________        ________________________
    CONTRATANTE                       CONTRATADA
"""
            }
        }
        
        # Não deve levantar exceção
        try:
            validate_document_templates(complex_data)
        except ValidationError:
            self.fail("validate_document_templates levantou ValidationError com conteúdo complexo válido")
