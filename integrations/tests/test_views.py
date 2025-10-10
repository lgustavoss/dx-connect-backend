"""
Testes para as views de integrações.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, Mock
import requests

from integrations.cep_service import CEPService


class CEPConsultaViewTests(APITestCase):
    """Testes para CEPConsultaView"""
    
    def setUp(self):
        """Setup para os testes"""
        # Limpar cache antes de cada teste
        from django.core.cache import cache
        cache.clear()
        
        self.url_pattern = '/api/v1/integrations/cep/{}/'
        
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
        from django.core.cache import cache
        cache.clear()
    
    @patch('integrations.cep_service.requests.get')
    def test_consultar_cep_sucesso(self, mock_get):
        """Testa consulta de CEP com sucesso"""
        # Configurar mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Fazer requisição
        url = self.url_pattern.format('01001-000')
        response = self.client.get(url)
        
        # Verificar resposta
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cep'], '01001-000')
        self.assertEqual(response.data['logradouro'], 'Praça da Sé')
        self.assertEqual(response.data['bairro'], 'Sé')
        self.assertEqual(response.data['cidade'], 'São Paulo')  # Alias
        self.assertEqual(response.data['estado'], 'SP')  # Alias
        self.assertEqual(response.data['localidade'], 'São Paulo')
        self.assertEqual(response.data['uf'], 'SP')
    
    @patch('integrations.cep_service.requests.get')
    def test_consultar_cep_nao_encontrado(self, mock_get):
        """Testa consulta de CEP não encontrado"""
        # Configurar mock para retornar erro
        mock_response = Mock()
        mock_response.json.return_value = {'erro': True}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Fazer requisição
        url = self.url_pattern.format('99999-999')
        response = self.client.get(url)
        
        # Verificar resposta
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertIn('CEP não encontrado', response.data['error'])
    
    def test_consultar_cep_formato_invalido(self):
        """Testa consulta de CEP com formato inválido"""
        # CEP curto
        url = self.url_pattern.format('123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # CEP com letras
        url = self.url_pattern.format('abc12345')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('integrations.cep_service.requests.get')
    def test_consultar_cep_timeout(self, mock_get):
        """Testa timeout na consulta de CEP"""
        # Configurar mock para timeout
        mock_get.side_effect = requests.exceptions.Timeout()
        
        # Fazer requisição
        url = self.url_pattern.format('01001-000')
        response = self.client.get(url)
        
        # Verificar resposta de erro
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
    
    @patch('integrations.cep_service.requests.get')
    def test_consultar_cep_erro_generico(self, mock_get):
        """Testa erro genérico na consulta de CEP"""
        # Configurar mock para erro genérico
        mock_get.side_effect = Exception("Erro desconhecido")
        
        # Fazer requisição
        url = self.url_pattern.format('01001-000')
        response = self.client.get(url)
        
        # Verificar resposta de erro
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
    
    def test_endpoint_publico(self):
        """Testa que o endpoint é público (não requer autenticação)"""
        # Fazer requisição sem autenticação
        with patch('integrations.cep_service.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = self.mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            url = self.url_pattern.format('01001-000')
            response = self.client.get(url)
            
            # Verificar que retorna 200 (não 401/403)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    @patch('integrations.cep_service.requests.get')
    def test_consultar_cep_com_diferentes_formatos(self, mock_get):
        """Testa consulta de CEP com diferentes formatos"""
        # Configurar mock
        mock_response = Mock()
        mock_response.json.return_value = self.mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Testar diferentes formatos
        formatos = ['01001000', '01001-000', '01.001-000', '01 001 000']
        
        for formato in formatos:
            with self.subTest(formato=formato):
                url = self.url_pattern.format(formato)
                response = self.client.get(url)
                
                # Todos devem retornar sucesso
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data['cep'], '01001-000')


class CEPIntegrationTests(APITestCase):
    """Testes de integração com a API real do ViaCEP"""
    
    def test_consultar_cep_real_sucesso(self):
        """Testa consulta real de CEP conhecido"""
        # Este teste faz uma requisição real à API do ViaCEP
        # Use com moderação para não sobrecarregar a API
        
        # CEP da Praça da Sé, São Paulo
        url = '/api/v1/integrations/cep/01001-000/'
        response = self.client.get(url)
        
        # Verificar resposta
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cep'], '01001-000')
        self.assertEqual(response.data['uf'], 'SP')
        self.assertIn('localidade', response.data)
    
    def test_consultar_cep_real_nao_encontrado(self):
        """Testa consulta real de CEP inexistente"""
        # CEP que não existe
        url = '/api/v1/integrations/cep/99999-999/'
        response = self.client.get(url)
        
        # Verificar resposta
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

