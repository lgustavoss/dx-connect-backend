"""
Testes de integração para o fluxo completo de chat.

Estes testes simulam cenários reais de uso do sistema de chat,
testando a integração entre diferentes componentes do sistema.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from clientes.models import Cliente, ContatoCliente, GrupoEmpresa

User = get_user_model()


class ChatFlowIntegrationTests(APITestCase):
    """
    Testes de integração para fluxos completos de chat.
    """
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Limpar dados anteriores
        ContatoCliente.objects.all().delete()
        Cliente.objects.all().delete()
        GrupoEmpresa.objects.all().delete()
        
        # Criar usuário atendente
        self.atendente = User.objects.create_user(
            username='atendente',
            email='atendente@empresa.com',
            password='testpass123'
        )
        
        # Criar grupo de empresas
        self.grupo_google = GrupoEmpresa.objects.create(
            nome='Grupo Google',
            descricao='Grupo de empresas do Google',
            criado_por=self.atendente
        )
        
        # Criar empresas
        self.empresa_drive = Cliente.objects.create(
            razao_social='Google Drive Brasil LTDA',
            cnpj='12.345.678/0001-90',
            grupo_empresa=self.grupo_google,
            criado_por=self.atendente
        )
        
        self.empresa_gmail = Cliente.objects.create(
            razao_social='Gmail Brasil LTDA',
            cnpj='98.765.432/0001-10',
            grupo_empresa=self.grupo_google,
            criado_por=self.atendente
        )
        
        self.empresa_independente = Cliente.objects.create(
            razao_social='Empresa Independente LTDA',
            cnpj='11.222.333/0001-81',
            criado_por=self.atendente
        )
        
        # Criar contatos existentes
        self.contato_joao = ContatoCliente.objects.create(
            cliente=self.empresa_drive,
            nome='João Silva',
            whatsapp='+5511999999999',
            cargo='Gerente de TI',
            email='joao@google.com',
            criado_por=self.atendente
        )
        
        # Contato do João também trabalha na Gmail
        self.contato_joao_gmail = ContatoCliente.objects.create(
            cliente=self.empresa_gmail,
            nome='João Silva',
            whatsapp='+5511999999999',
            cargo='Coordenador',
            email='joao@gmail.com',
            criado_por=self.atendente
        )
        
        # Obter token JWT para o atendente
        refresh = RefreshToken.for_user(self.atendente)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_fluxo_contato_nao_cadastrado_completo(self):
        """
        Testa fluxo completo: WhatsApp não cadastrado → busca → não encontrado → 
        captura dados → cadastro manual com nova empresa.
        """
        whatsapp_novo = '+5511888888888'
        
        # 1. Buscar contato (não deve encontrar)
        response = self.client.post('/api/v1/clientes/chat/buscar-contato/', {
            'whatsapp': whatsapp_novo
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['encontrado'])
        self.assertIn('Dados capturados disponíveis', response.data['message'])
        
        # 2. Capturar dados do chat
        response = self.client.post('/api/v1/clientes/chat/dados-capturados/', {
            'whatsapp': whatsapp_novo,
            'nome': 'Maria Santos',
            'empresa_nome': 'Nova Empresa LTDA',
            'cargo': 'Analista'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Dados capturados recebidos', response.data['message'])
        self.assertEqual(response.data['dados_capturados']['nome'], 'Maria Santos')
        
        # 3. Cadastrar contato manualmente
        response = self.client.post('/api/v1/clientes/cadastro-manual/', {
            'whatsapp': whatsapp_novo,
            'nome': 'Maria Santos',
            'cargo': 'Analista de Sistemas',
            'email': 'maria@novaempresa.com',
            'empresa_nome': 'Nova Empresa LTDA',
            'empresa_cnpj': '11.222.333/0001-81',
            'grupo_empresa_id': self.grupo_google.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('Contato cadastrado com sucesso', response.data['message'])
        
        # 4. Verificar se contato foi criado
        contato = ContatoCliente.objects.get(whatsapp=whatsapp_novo)
        self.assertEqual(contato.nome, 'Maria Santos')
        self.assertEqual(contato.cargo, 'Analista de Sistemas')
        self.assertEqual(contato.email, 'maria@novaempresa.com')
        
        # 5. Verificar se empresa foi criada
        empresa = contato.cliente
        self.assertEqual(empresa.razao_social, 'Nova Empresa LTDA')
        self.assertEqual(empresa.grupo_empresa, self.grupo_google)
        
        # 6. Agora buscar novamente deve encontrar
        response = self.client.post('/api/v1/clientes/chat/buscar-contato/', {
            'whatsapp': whatsapp_novo
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['encontrado'])
        self.assertEqual(len(response.data['contatos']), 1)
        self.assertEqual(response.data['contatos'][0]['nome'], 'Maria Santos')
    
    def test_fluxo_contato_ja_cadastrado_simples(self):
        """
        Testa fluxo: WhatsApp já cadastrado → busca → encontrado → exibe informações.
        """
        # Buscar contato existente
        response = self.client.post('/api/v1/clientes/chat/buscar-contato/', {
            'whatsapp': '+5511999999999'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['encontrado'])
        self.assertEqual(len(response.data['contatos']), 2)  # João está em 2 empresas
        
        # Verificar dados dos contatos
        contatos = response.data['contatos']
        nomes = [c['nome'] for c in contatos]
        self.assertIn('João Silva', nomes)
        
        # Verificar empresas
        empresas = [c['cliente_nome'] for c in contatos]
        self.assertIn('Google Drive Brasil LTDA', empresas)
        self.assertIn('Gmail Brasil LTDA', empresas)
    
    def test_fluxo_cadastro_com_empresa_existente(self):
        """
        Testa fluxo: WhatsApp não cadastrado → cadastro manual vinculando a empresa existente.
        """
        whatsapp_novo = '+5511777777777'
        
        # Cadastrar contato vinculando a empresa existente
        response = self.client.post('/api/v1/clientes/cadastro-manual/', {
            'whatsapp': whatsapp_novo,
            'nome': 'Pedro Costa',
            'cargo': 'Desenvolvedor',
            'email': 'pedro@google.com',
            'empresa_id': self.empresa_drive.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar se contato foi criado na empresa correta
        contato = ContatoCliente.objects.get(whatsapp=whatsapp_novo)
        self.assertEqual(contato.cliente, self.empresa_drive)
        self.assertEqual(contato.nome, 'Pedro Costa')
        
        # Verificar se empresa não foi duplicada
        empresas_google_drive = Cliente.objects.filter(
            razao_social='Google Drive Brasil LTDA'
        )
        self.assertEqual(empresas_google_drive.count(), 1)
    
    def test_fluxo_whatsapp_duplicado_prevencao(self):
        """
        Testa que não é possível cadastrar WhatsApp duplicado.
        """
        # Tentar cadastrar WhatsApp já existente
        response = self.client.post('/api/v1/clientes/cadastro-manual/', {
            'whatsapp': '+5511999999999',  # WhatsApp já existe
            'nome': 'João Duplicado',
            'empresa_id': self.empresa_independente.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('WhatsApp já cadastrado', response.data['message'])
        
        # Verificar que contato duplicado não foi criado
        contatos_joao_duplicado = ContatoCliente.objects.filter(
            nome='João Duplicado'
        )
        self.assertEqual(contatos_joao_duplicado.count(), 0)
    
    def test_fluxo_busca_contatos_por_empresa(self):
        """
        Testa busca de contatos filtrados por empresa.
        """
        # Buscar contatos da empresa Drive
        response = self.client.get(f'/api/v1/contatos/?cliente={self.empresa_drive.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['nome'], 'João Silva')
        
        # Buscar contatos da empresa Gmail
        response = self.client.get(f'/api/v1/contatos/?cliente={self.empresa_gmail.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['nome'], 'João Silva')
    
    def test_fluxo_edicao_contato_existente(self):
        """
        Testa edição de contato existente.
        """
        # Editar contato existente
        response = self.client.patch(f'/api/v1/contatos/{self.contato_joao.id}/', {
            'cargo': 'Gerente Sênior de TI',
            'email': 'joao.senior@google.com'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar se alterações foram salvas
        self.contato_joao.refresh_from_db()
        self.assertEqual(self.contato_joao.cargo, 'Gerente Sênior de TI')
        self.assertEqual(self.contato_joao.email, 'joao.senior@google.com')
    
    def test_fluxo_remocao_contato(self):
        """
        Testa remoção (soft delete) de contato.
        """
        # Remover contato
        response = self.client.delete(f'/api/v1/contatos/{self.contato_joao.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar se contato foi marcado como inativo
        self.contato_joao.refresh_from_db()
        self.assertFalse(self.contato_joao.ativo)
        
        # Verificar que não aparece mais na busca
        response = self.client.get('/api/v1/contatos/')
        contatos_ativos = [c for c in response.data['results'] if c['ativo']]
        self.assertEqual(len(contatos_ativos), 1)  # Apenas o contato da Gmail
    
    def test_fluxo_grupo_empresas_gerenciamento(self):
        """
        Testa gerenciamento de grupos de empresas.
        """
        # Listar grupos
        response = self.client.get('/api/v1/grupos-empresa/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['nome'], 'Grupo Google')
        
        # Criar novo grupo
        response = self.client.post('/api/v1/grupos-empresa/', {
            'nome': 'Grupo Microsoft',
            'descricao': 'Grupo de empresas da Microsoft'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar se grupo foi criado
        grupos = GrupoEmpresa.objects.all()
        self.assertEqual(grupos.count(), 2)
        
        # Buscar grupos por nome
        response = self.client.get('/api/v1/grupos-empresa/?search=Microsoft')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['nome'], 'Grupo Microsoft')
    
    def test_fluxo_endpoints_sem_autenticacao_chat(self):
        """
        Testa que endpoints de chat são públicos (não requerem autenticação).
        """
        # Remover autenticação
        self.client.credentials()
        
        # Buscar contato (deve funcionar sem autenticação)
        response = self.client.post('/api/v1/clientes/chat/buscar-contato/', {
            'whatsapp': '+5511999999999'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['encontrado'])
        
        # Capturar dados (deve funcionar sem autenticação)
        response = self.client.post('/api/v1/clientes/chat/dados-capturados/', {
            'whatsapp': '+5511555555555',
            'nome': 'Teste Público',
            'empresa_nome': 'Empresa Teste Público'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_fluxo_endpoints_com_autenticacao_obrigatoria(self):
        """
        Testa que endpoints de gerenciamento requerem autenticação.
        """
        # Remover autenticação
        self.client.credentials()
        
        # Tentar acessar endpoints que requerem autenticação
        endpoints_autenticados = [
            ('/api/v1/contatos/', 'GET'),
            ('/api/v1/grupos-empresa/', 'GET'),
            ('/api/v1/clientes/cadastro-manual/', 'POST'),
        ]
        
        for endpoint, method in endpoints_autenticados:
            if method == 'GET':
                response = self.client.get(endpoint)
            elif method == 'POST':
                response = self.client.post(endpoint, {})
            
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_fluxo_validacoes_dados_invalidos(self):
        """
        Testa validações com dados inválidos em diferentes pontos do fluxo.
        """
        # 1. WhatsApp inválido na busca
        response = self.client.post('/api/v1/clientes/chat/buscar-contato/', {
            'whatsapp': '123'  # WhatsApp inválido
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 2. WhatsApp inválido no cadastro manual
        response = self.client.post('/api/v1/clientes/cadastro-manual/', {
            'whatsapp': '123',  # WhatsApp inválido
            'nome': 'Teste',
            'empresa_nome': 'Empresa Teste'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 3. CNPJ inválido no cadastro manual
        response = self.client.post('/api/v1/clientes/cadastro-manual/', {
            'whatsapp': '+5511555555555',
            'nome': 'Teste',
            'empresa_nome': 'Empresa Teste',
            'empresa_cnpj': '123'  # CNPJ inválido
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 4. Grupo inexistente no cadastro manual
        response = self.client.post('/api/v1/clientes/cadastro-manual/', {
            'whatsapp': '+5511555555555',
            'nome': 'Teste',
            'empresa_nome': 'Empresa Teste',
            'grupo_empresa_id': 999  # Grupo inexistente
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
