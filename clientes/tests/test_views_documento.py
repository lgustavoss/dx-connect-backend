"""
Testes unitários para as views de DocumentoCliente.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date, timedelta
from unittest.mock import patch, Mock
import tempfile
import os

from clientes.models import Cliente, DocumentoCliente, GrupoEmpresa
from core.models import Config

User = get_user_model()


class DocumentoClienteViewSetTests(APITestCase):
    """Testes para DocumentoClienteViewSet."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Limpa dados anteriores
        DocumentoCliente.objects.all().delete()
        Cliente.objects.all().delete()
        GrupoEmpresa.objects.all().delete()
        
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@example.com'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        self.grupo = GrupoEmpresa.objects.create(
            nome="Grupo Teste",
            descricao="Descrição do grupo teste"
        )
        
        self.cliente = Cliente.objects.create(
            razao_social="Empresa Teste LTDA",
            cnpj="11.222.333/0001-81",
            grupo_empresa=self.grupo,
            responsavel_legal_nome="João Silva",
            responsavel_legal_cpf="111.111.111-11",
            criado_por=self.user
        )
        
        self.documento = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Documento Teste",
            tipo_documento="contrato",
            status="gerado",
            origem="manual",
            descricao="Descrição do documento",
            arquivo="teste.txt",
            usuario_upload=self.user
        )
        
        # Configurar autenticação
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_list_documentos_authenticated(self):
        """Testa listagem de documentos autenticado."""
        response = self.client.get('/api/v1/documentos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['nome'], "Documento Teste")
    
    def test_list_documentos_unauthenticated(self):
        """Testa listagem de documentos sem autenticação."""
        self.client.credentials()
        response = self.client.get('/api/v1/documentos/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_documento_authenticated(self):
        """Testa criação de documento autenticado."""
        data = {
            'cliente': self.cliente.id,
            'nome': 'Novo Documento',
            'tipo_documento': 'boleto',
            'descricao': 'Boleto de cobrança',
            'data_vencimento': (date.today() + timedelta(days=30)).isoformat()
        }
        
        response = self.client.post('/api/v1/documentos/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nome'], 'Novo Documento')
        self.assertEqual(response.data['usuario_upload'], self.user.id)
        
        # Verifica que foi criado no banco
        documento = DocumentoCliente.objects.get(id=response.data['id'])
        self.assertEqual(documento.usuario_upload, self.user)
    
    def test_create_documento_invalid_data(self):
        """Testa criação de documento com dados inválidos."""
        data = {
            'cliente': self.cliente.id,
            'nome': '',  # Nome vazio
            'tipo_documento': 'tipo_inexistente'  # Tipo inválido
        }
        
        response = self.client.post('/api/v1/documentos/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nome', response.data)
        self.assertIn('tipo_documento', response.data)
    
    def test_retrieve_documento_authenticated(self):
        """Testa recuperação de documento específico."""
        response = self.client.get(f'/api/v1/documentos/{self.documento.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome'], "Documento Teste")
        self.assertEqual(response.data['is_contrato'], True)
    
    def test_retrieve_documento_not_found(self):
        """Testa recuperação de documento inexistente."""
        response = self.client.get('/api/v1/documentos/999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_documento_authenticated(self):
        """Testa atualização de documento."""
        data = {
            'nome': 'Documento Atualizado',
            'descricao': 'Nova descrição',
            'status': 'assinado'
        }
        
        response = self.client.patch(f'/api/v1/documentos/{self.documento.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome'], 'Documento Atualizado')
        self.assertEqual(response.data['status'], 'assinado')
        
        # Verifica no banco
        self.documento.refresh_from_db()
        self.assertEqual(self.documento.nome, 'Documento Atualizado')
        self.assertEqual(self.documento.status, 'assinado')
    
    def test_delete_documento_soft_delete(self):
        """Testa soft delete de documento."""
        response = self.client.delete(f'/api/v1/documentos/{self.documento.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verifica que foi marcado como inativo
        self.documento.refresh_from_db()
        self.assertFalse(self.documento.ativo)
        
        # Verifica que não aparece na listagem
        response = self.client.get('/api/v1/documentos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
    
    def test_filter_documentos_by_tipo(self):
        """Testa filtro de documentos por tipo."""
        # Cria outro documento
        DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Boleto Teste",
            tipo_documento="boleto",
            arquivo="boleto.txt",
            usuario_upload=self.user
        )
        
        # Filtra por tipo contrato
        response = self.client.get('/api/v1/documentos/?tipo_documento=contrato')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['tipo_documento'], 'contrato')
        
        # Filtra por tipo boleto
        response = self.client.get('/api/v1/documentos/?tipo_documento=boleto')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['tipo_documento'], 'boleto')
    
    def test_filter_documentos_by_status(self):
        """Testa filtro de documentos por status."""
        response = self.client.get('/api/v1/documentos/?status=gerado')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['status'], 'gerado')
    
    def test_filter_documentos_by_cliente(self):
        """Testa filtro de documentos por cliente."""
        response = self.client.get(f'/api/v1/documentos/?cliente={self.cliente.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['cliente'], self.cliente.id)
    
    def test_search_documentos_by_nome(self):
        """Testa busca de documentos por nome."""
        response = self.client.get('/api/v1/documentos/?search=Teste')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertIn('Teste', response.data['results'][0]['nome'])
    
    def test_ordering_documentos_by_data_upload(self):
        """Testa ordenação de documentos por data de upload."""
        # Cria outro documento
        doc2 = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Segundo Documento",
            tipo_documento="boleto",
            arquivo="boleto.txt",
            usuario_upload=self.user
        )
        
        # Ordena por data de upload (padrão: mais recente primeiro)
        response = self.client.get('/api/v1/documentos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['id'], doc2.id)  # Mais recente primeiro
    
    def test_user_filtering_non_superuser(self):
        """Testa que usuário não-superuser vê apenas documentos de clientes criados por ele."""
        # Cria outro usuário e cliente
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123',
            email='other@example.com'
        )
        
        other_cliente = Cliente.objects.create(
            razao_social="Outra Empresa LTDA",
            cnpj="99.999.999/0001-99",
            responsavel_legal_nome="Outro Responsável",
            responsavel_legal_cpf="999.999.999-99",
            criado_por=other_user
        )
        
        # Cria documento para outro cliente
        DocumentoCliente.objects.create(
            cliente=other_cliente,
            nome="Documento Outro Cliente",
            tipo_documento="contrato",
            arquivo="outro.txt",
            usuario_upload=other_user
        )
        
        # Usuário atual deve ver apenas seus documentos
        response = self.client.get('/api/v1/documentos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # Apenas o documento do seu cliente
    
    def test_superuser_sees_all_documentos(self):
        """Testa que superuser vê todos os documentos."""
        # Autentica como superuser
        refresh = RefreshToken.for_user(self.superuser)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Cria outro usuário e documento
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123',
            email='other@example.com'
        )
        
        other_cliente = Cliente.objects.create(
            razao_social="Outra Empresa LTDA",
            cnpj="99.999.999/0001-99",
            responsavel_legal_nome="Outro Responsável",
            responsavel_legal_cpf="999.999.999-99",
            criado_por=other_user
        )
        
        DocumentoCliente.objects.create(
            cliente=other_cliente,
            nome="Documento Outro Cliente",
            tipo_documento="contrato",
            arquivo="outro.txt",
            usuario_upload=other_user
        )
        
        # Superuser deve ver todos os documentos
        response = self.client.get('/api/v1/documentos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # Todos os documentos


class DocumentoClienteGeracaoTests(APITestCase):
    """Testes para geração automática de documentos."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Limpa dados anteriores
        DocumentoCliente.objects.all().delete()
        Cliente.objects.all().delete()
        GrupoEmpresa.objects.all().delete()
        Config.objects.all().delete()
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        self.grupo = GrupoEmpresa.objects.create(
            nome="Grupo Teste",
            descricao="Descrição do grupo teste"
        )
        
        self.cliente = Cliente.objects.create(
            razao_social="Empresa Teste LTDA",
            cnpj="11.222.333/0001-81",
            grupo_empresa=self.grupo,
            responsavel_legal_nome="João Silva",
            responsavel_legal_cpf="111.111.111-11",
            criado_por=self.user,
            email_principal="contato@empresateste.com",
            telefone_principal="(11) 99999-9999",
            logradouro="Rua das Flores",
            numero="123",
            bairro="Centro",
            cidade="São Paulo",
            estado="SP",
            cep="01234-567"
        )
        
        # Cria configuração com dados da empresa
        self.config = Config.objects.create(
            company_data={
                "razao_social": "Minha Empresa LTDA",
                "cnpj": "00.000.000/0001-00",
                "endereco": {
                    "logradouro": "Rua da Empresa",
                    "numero": "456",
                    "bairro": "Empresarial",
                    "cidade": "São Paulo",
                    "uf": "SP"
                }
            }
        )
        
        # Configurar autenticação
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    @patch('tempfile.NamedTemporaryFile')
    def test_gerar_contrato_success(self, mock_temp_file):
        """Testa geração bem-sucedida de contrato."""
        # Mock do arquivo temporário
        mock_file = Mock()
        mock_file.name = '/tmp/contrato.txt'
        mock_temp_file.return_value.__enter__.return_value = mock_file
        
        data = {
            'cliente_id': self.cliente.id,
            'template_nome': 'contrato_padrao',
            'dados_contrato': {
                'valor_servico': '1000.00',
                'data_inicio': '01/01/2024',
                'data_fim': '31/12/2024',
                'prazo_contrato': '1 ano'
            }
        }
        
        response = self.client.post('/api/v1/documentos/gerar-contrato/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('Contrato gerado com sucesso', response.data['message'])
        self.assertEqual(response.data['documento']['tipo_documento'], 'contrato')
        self.assertEqual(response.data['documento']['origem'], 'gerado')
        self.assertEqual(response.data['documento']['status'], 'gerado')
        self.assertEqual(response.data['documento']['template_usado'], 'Contrato de Prestação de Serviços Padrão')
        
        # Verifica que foi criado no banco
        documento = DocumentoCliente.objects.get(id=response.data['documento']['id'])
        self.assertEqual(documento.cliente, self.cliente)
        self.assertEqual(documento.tipo_documento, 'contrato')
        self.assertEqual(documento.origem, 'gerado')
        self.assertIn('valor_servico', documento.dados_preenchidos)
        self.assertEqual(documento.dados_preenchidos['valor_servico'], '1000.00')
    
    def test_gerar_contrato_cliente_inexistente(self):
        """Testa geração de contrato com cliente inexistente."""
        data = {
            'cliente_id': 999,  # Cliente inexistente
            'template_nome': 'contrato_padrao'
        }
        
        response = self.client.post('/api/v1/documentos/gerar-contrato/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Cliente não encontrado', response.data['error'])
    
    def test_gerar_contrato_template_inexistente(self):
        """Testa geração de contrato com template inexistente."""
        data = {
            'cliente_id': self.cliente.id,
            'template_nome': 'template_inexistente'
        }
        
        response = self.client.post('/api/v1/documentos/gerar-contrato/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Template "template_inexistente" não encontrado', response.data['error'])
    
    def test_gerar_contrato_missing_cliente_id(self):
        """Testa geração de contrato sem cliente_id."""
        data = {
            'template_nome': 'contrato_padrao'
        }
        
        response = self.client.post('/api/v1/documentos/gerar-contrato/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cliente_id é obrigatório', response.data['error'])
    
    @patch('tempfile.NamedTemporaryFile')
    def test_gerar_boleto_success(self, mock_temp_file):
        """Testa geração bem-sucedida de boleto."""
        # Mock do arquivo temporário
        mock_file = Mock()
        mock_file.name = '/tmp/boleto.txt'
        mock_temp_file.return_value.__enter__.return_value = mock_file
        
        data = {
            'cliente_id': self.cliente.id,
            'template_nome': 'boleto_padrao',
            'dados_boleto': {
                'valor_total': '500.00',
                'data_vencimento': (date.today() + timedelta(days=30)).isoformat(),
                'descricao_servicos': 'Suporte técnico mensal',
                'banco': 'Banco do Brasil',
                'agencia': '1234',
                'conta': '56789-0'
            }
        }
        
        response = self.client.post('/api/v1/documentos/gerar-boleto/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('Boleto gerado com sucesso', response.data['message'])
        self.assertEqual(response.data['documento']['tipo_documento'], 'boleto')
        self.assertEqual(response.data['documento']['origem'], 'gerado')
        
        # Verifica que foi criado no banco
        documento = DocumentoCliente.objects.get(id=response.data['documento']['id'])
        self.assertEqual(documento.tipo_documento, 'boleto')
        self.assertIn('valor_total', documento.dados_preenchidos)
        self.assertEqual(documento.dados_preenchidos['valor_total'], '500.00')
    
    def test_gerar_boleto_cliente_inexistente(self):
        """Testa geração de boleto com cliente inexistente."""
        data = {
            'cliente_id': 999,
            'template_nome': 'boleto_padrao'
        }
        
        response = self.client.post('/api/v1/documentos/gerar-boleto/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Cliente não encontrado', response.data['error'])
    
    def test_gerar_documento_unauthenticated(self):
        """Testa geração de documento sem autenticação."""
        self.client.credentials()
        
        data = {
            'cliente_id': self.cliente.id,
            'template_nome': 'contrato_padrao'
        }
        
        response = self.client.post('/api/v1/documentos/gerar-contrato/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @patch('tempfile.NamedTemporaryFile')
    def test_template_preenchimento_dados_cliente_empresa(self, mock_temp_file):
        """Testa preenchimento correto do template com dados do cliente e empresa."""
        # Mock do arquivo temporário
        mock_file = Mock()
        mock_file.name = '/tmp/contrato.txt'
        mock_temp_file.return_value.__enter__.return_value = mock_file
        
        data = {
            'cliente_id': self.cliente.id,
            'template_nome': 'contrato_padrao',
            'dados_contrato': {
                'valor_servico': '2000.00'
            }
        }
        
        response = self.client.post('/api/v1/documentos/gerar-contrato/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verifica dados preenchidos
        documento = DocumentoCliente.objects.get(id=response.data['documento']['id'])
        dados = documento.dados_preenchidos
        
        # Dados do cliente (contratante)
        self.assertEqual(dados['cliente_nome'], self.cliente.razao_social)
        self.assertEqual(dados['cliente_cnpj'], self.cliente.cnpj)
        self.assertEqual(dados['cliente_email'], self.cliente.email_principal)
        self.assertEqual(dados['cliente_telefone'], self.cliente.telefone_principal)
        
        # Dados da empresa (contratada) - da configuração
        self.assertEqual(dados['empresa_nome'], 'Minha Empresa LTDA')
        self.assertEqual(dados['empresa_cnpj'], '00.000.000/0001-00')
        
        # Dados extras fornecidos
        self.assertEqual(dados['valor_servico'], '2000.00')
        
        # Dados do sistema
        self.assertIn('data_contrato', dados)
        self.assertIn('data_geracao', dados)
