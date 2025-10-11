"""
Testes para o serviço de integração com ViaCEP.
"""

from django.test import TestCase
from django.core.cache import cache
from unittest.mock import patch, Mock
import requests

from integrations.cep_service import CEPService, buscar_cep


class CEPServiceTests(TestCase):
    """Testes para CEPService"""
    
    def setUp(self):
        """Setup para os testes"""
        # Limpar cache antes de cada teste
        cache.clear()
        
        # Dados de resposta simulados da API
        self.mock_response_data = {
            'cep': '01001-000',
            'logradouro': 'Praça da Sé',
            'complemento': 'lado ímpar',
            'bairro': 'Sé',
            'localidade': 'São Paulo',
            'uf': 'SP',
            'ibge': '3550308',
            'gia': '1004',
            'ddd': '11',
            'siafi': '7107'
        }
    
    def tearDown(self):
        """Limpeza após os testes"""
        cache.clear()
    
    def test_limpar_cep(self):
        """Testa limpeza de CEP"""
        # CEP com formatação
        self.assertEqual(CEPService._limpar_cep('01001-000'), '01001000')
        
        # CEP sem formatação
        self.assertEqual(CEPService._limpar_cep('01001000'), '01001000')
        
        # CEP com espaços
        self.assertEqual(CEPService._limpar_cep('01 001-000'), '01001000')
        
        # CEP com outros caracteres
        self.assertEqual(CEPService._limpar_cep('01.001-000'), '01001000')
    
    def test_validar_cep_valido(self):
        """Testa validação de CEP válido"""
        self.assertTrue(CEPService._validar_cep('01001000'))
        self.assertTrue(CEPService._validar_cep('12345678'))
    
    def test_validar_cep_invalido(self):
        """Testa validação de CEP inválido"""
        # CEP curto
        self.assertFalse(CEPService._validar_cep('1234567'))
        
        # CEP longo
        self.assertFalse(CEPService._validar_cep('123456789'))
        
        # CEP vazio
        self.assertFalse(CEPService._validar_cep(''))
        
        # CEP com letras
        self.assertFalse(CEPService._validar_cep('0100100a'))
    
    @patch('integrations.cep_service.requests.get')
    def test_consultar_cep_sucesso(self, mock_get):
        """Testa consulta de CEP com sucesso"""
        # Configurar mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Consultar CEP
        result = CEPService.consultar_cep('01001-000')
        
        # Verificar resultado
        self.assertIsNotNone(result)
        self.assertEqual(result['cep'], '01001-000')
        self.assertEqual(result['logradouro'], 'Praça da Sé')
        self.assertEqual(result['bairro'], 'Sé')
        self.assertEqual(result['localidade'], 'São Paulo')
        self.assertEqual(result['uf'], 'SP')
        
        # Verificar que a API foi chamada corretamente
        mock_get.assert_called_once_with(
            'https://viacep.com.br/ws/01001000/json/',
            timeout=5
        )
    
    @patch('integrations.cep_service.requests.get')
    def test_consultar_cep_nao_encontrado(self, mock_get):
        """Testa consulta de CEP não encontrado"""
        # Configurar mock para retornar erro
        mock_response = Mock()
        mock_response.json.return_value = {'erro': True}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Consultar CEP
        result = CEPService.consultar_cep('99999-999')
        
        # Verificar que retorna None
        self.assertIsNone(result)
    
    def test_consultar_cep_formato_invalido(self):
        """Testa consulta de CEP com formato inválido"""
        with self.assertRaises(ValueError):
            CEPService.consultar_cep('123')
        
        with self.assertRaises(ValueError):
            CEPService.consultar_cep('abc12345')
    
    @patch('integrations.cep_service.requests.get')
    def test_consultar_cep_timeout(self, mock_get):
        """Testa timeout na consulta de CEP"""
        # Configurar mock para timeout
        mock_get.side_effect = requests.exceptions.Timeout()
        
        # Verificar que lança exceção
        with self.assertRaises(requests.exceptions.RequestException):
            CEPService.consultar_cep('01001-000')
    
    @patch('integrations.cep_service.requests.get')
    def test_consultar_cep_erro_http(self, mock_get):
        """Testa erro HTTP na consulta de CEP"""
        # Configurar mock para erro HTTP
        mock_get.side_effect = requests.exceptions.HTTPError()
        
        # Verificar que lança exceção
        with self.assertRaises(requests.exceptions.RequestException):
            CEPService.consultar_cep('01001-000')
    
    @patch('integrations.cep_service.requests.get')
    def test_consultar_cep_com_cache(self, mock_get):
        """Testa que consultas subsequentes usam cache"""
        # Configurar mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Primeira consulta (deve chamar API)
        result1 = CEPService.consultar_cep('01001-000')
        self.assertIsNotNone(result1)
        self.assertEqual(mock_get.call_count, 1)
        
        # Segunda consulta (deve usar cache)
        result2 = CEPService.consultar_cep('01001-000')
        self.assertIsNotNone(result2)
        self.assertEqual(result1, result2)
        # Ainda deve ter chamado apenas 1 vez (cache foi usado)
        self.assertEqual(mock_get.call_count, 1)
    
    def test_formatar_endereco(self):
        """Testa formatação de endereço"""
        # Formatar dados da API
        formatted = CEPService.formatar_endereco(self.mock_response_data)
        
        # Verificar campos formatados
        self.assertEqual(formatted['endereco'], 'Praça da Sé')
        self.assertEqual(formatted['bairro'], 'Sé')
        self.assertEqual(formatted['cidade'], 'São Paulo')
        self.assertEqual(formatted['estado'], 'SP')
        self.assertEqual(formatted['cep'], '01001000')
        self.assertEqual(formatted['complemento'], 'lado ímpar')
    
    @patch('integrations.cep_service.requests.get')
    def test_buscar_cep_funcao_auxiliar(self, mock_get):
        """Testa função auxiliar buscar_cep"""
        # Configurar mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Usar função auxiliar
        result = buscar_cep('01001-000')
        
        # Verificar resultado
        self.assertIsNotNone(result)
        self.assertEqual(result['cep'], '01001-000')

