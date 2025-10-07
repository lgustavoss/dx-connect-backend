from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from clientes.models import Cliente, ContatoCliente, GrupoEmpresa

User = get_user_model()


class ChatIntegrationViewTests(APITestCase):
    """Testes para ChatIntegrationView."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.grupo = GrupoEmpresa.objects.create(
            nome='Grupo Teste',
            criado_por=self.user
        )
        
        self.cliente = Cliente.objects.create(
            razao_social='Empresa Teste LTDA',
            cnpj='12.345.678/0001-90',
            grupo_empresa=self.grupo,
            criado_por=self.user
        )
        
        self.contato = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='João Silva',
            whatsapp='+5511999999999',
            cargo='Gerente',
            email='joao@empresa.com',
            criado_por=self.user
        )
    
    def test_buscar_contato_encontrado(self):
        """Testa busca de contato existente."""
        url = '/api/v1/clientes/chat/buscar-contato/'
        data = {'whatsapp': '+5511999999999'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['encontrado'])
        self.assertEqual(len(response.data['contatos']), 1)
        self.assertEqual(response.data['contatos'][0]['nome'], 'João Silva')
        self.assertEqual(response.data['contatos'][0]['cliente_nome'], 'Empresa Teste LTDA')
    
    def test_buscar_contato_nao_encontrado(self):
        """Testa busca de contato inexistente."""
        url = '/api/v1/clientes/chat/buscar-contato/'
        data = {'whatsapp': '+5511888888888'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['encontrado'])
        self.assertIn('WhatsApp não encontrado', response.data['message'])
    
    def test_buscar_contato_whatsapp_invalido(self):
        """Testa busca com WhatsApp inválido."""
        url = '/api/v1/clientes/chat/buscar-contato/'
        data = {'whatsapp': '123'}  # Inválido
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('whatsapp', response.data)
    
    def test_buscar_contato_whatsapp_obrigatorio(self):
        """Testa busca sem WhatsApp."""
        url = '/api/v1/clientes/chat/buscar-contato/'
        data = {}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('whatsapp', response.data)
    
    def test_buscar_contato_multiplos_contatos(self):
        """Testa busca quando há múltiplos contatos com mesmo WhatsApp."""
        # Criar segunda empresa no mesmo grupo
        cliente2 = Cliente.objects.create(
            razao_social='Empresa 2 LTDA',
            cnpj='98.765.432/0001-10',
            grupo_empresa=self.grupo,
            criado_por=self.user
        )
        
        # Criar contato na segunda empresa com mesmo WhatsApp
        contato2 = ContatoCliente.objects.create(
            cliente=cliente2,
            nome='João Santos',
            whatsapp='+5511999999999',  # Mesmo WhatsApp
            cargo='Supervisor',
            criado_por=self.user
        )
        
        url = '/api/v1/clientes/chat/buscar-contato/'
        data = {'whatsapp': '+5511999999999'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['encontrado'])
        self.assertEqual(len(response.data['contatos']), 2)
    
    def test_dados_capturados_validos(self):
        """Testa captura de dados válidos do chat."""
        url = '/api/v1/clientes/chat/dados-capturados/'
        data = {
            'whatsapp': '+5511888888888',
            'nome': 'Maria Santos',
            'empresa_nome': 'Nova Empresa LTDA',
            'cargo': 'Analista'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Dados capturados recebidos', response.data['message'])
        self.assertEqual(response.data['dados_capturados']['whatsapp'], '+5511888888888')
        self.assertEqual(response.data['dados_capturados']['nome'], 'Maria Santos')
        self.assertEqual(response.data['dados_capturados']['empresa_nome'], 'Nova Empresa LTDA')
        self.assertEqual(response.data['dados_capturados']['cargo'], 'Analista')
        self.assertEqual(response.data['proximo_passo'], 'Atendente deve editar e salvar os dados')
    
    def test_dados_capturados_whatsapp_invalido(self):
        """Testa captura com WhatsApp inválido."""
        url = '/api/v1/clientes/chat/dados-capturados/'
        data = {
            'whatsapp': '123',  # Inválido
            'nome': 'Maria Santos',
            'empresa_nome': 'Nova Empresa LTDA'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('whatsapp', response.data)
    
    def test_dados_capturados_campos_obrigatorios(self):
        """Testa captura sem campos obrigatórios."""
        url = '/api/v1/clientes/chat/dados-capturados/'
        data = {
            'nome': 'Maria Santos',
            'empresa_nome': 'Nova Empresa LTDA'
            # Sem WhatsApp
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('whatsapp', response.data)
    
    def test_endpoints_publicos(self):
        """Testa que os endpoints de chat são públicos (AllowAny)."""
        # Testar sem autenticação
        url_buscar = '/api/v1/clientes/chat/buscar-contato/'
        url_dados = '/api/v1/clientes/chat/dados-capturados/'
        
        data_buscar = {'whatsapp': '+5511999999999'}
        data_dados = {
            'whatsapp': '+5511888888888',
            'nome': 'Teste',
            'empresa_nome': 'Empresa Teste'
        }
        
        response_buscar = self.client.post(url_buscar, data_buscar, format='json')
        response_dados = self.client.post(url_dados, data_dados, format='json')
        
        # Ambos devem funcionar sem autenticação
        self.assertEqual(response_buscar.status_code, status.HTTP_200_OK)
        self.assertEqual(response_dados.status_code, status.HTTP_200_OK)


class CadastroManualViewTests(APITestCase):
    """Testes para CadastroManualView."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.grupo = GrupoEmpresa.objects.create(
            nome='Grupo Teste',
            criado_por=self.user
        )
        
        self.cliente = Cliente.objects.create(
            razao_social='Empresa Teste LTDA',
            cnpj='12.345.678/0001-90',
            grupo_empresa=self.grupo,
            criado_por=self.user
        )
        
        # Obter token JWT
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_cadastro_manual_sucesso_empresa_existente(self):
        """Testa cadastro manual com empresa existente."""
        url = '/api/v1/clientes/cadastro-manual/'
        data = {
            'whatsapp': '+5511888888888',
            'nome': 'Maria Santos',
            'cargo': 'Analista',
            'email': 'maria@empresa.com',
            'empresa_id': self.cliente.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('Contato cadastrado com sucesso', response.data['message'])
        self.assertEqual(response.data['contato']['nome'], 'Maria Santos')
        self.assertEqual(response.data['contato']['cliente_nome'], 'Empresa Teste LTDA')
        
        # Verificar se contato foi criado no banco
        contato = ContatoCliente.objects.get(whatsapp='+5511888888888')
        self.assertEqual(contato.nome, 'Maria Santos')
        self.assertEqual(contato.cliente, self.cliente)
    
    def test_cadastro_manual_sucesso_nova_empresa(self):
        """Testa cadastro manual com nova empresa."""
        url = '/api/v1/clientes/cadastro-manual/'
        data = {
            'whatsapp': '+5511777777777',
            'nome': 'Pedro Costa',
            'cargo': 'Gerente',
            'email': 'pedro@novaempresa.com',
            'empresa_nome': 'Nova Empresa LTDA',
            'empresa_cnpj': '11.222.333/0001-81',
            'grupo_empresa_id': self.grupo.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('Contato cadastrado com sucesso', response.data['message'])
        self.assertEqual(response.data['contato']['nome'], 'Pedro Costa')
        self.assertEqual(response.data['contato']['cliente_nome'], 'Nova Empresa LTDA')
        
        # Verificar se empresa e contato foram criados
        contato = ContatoCliente.objects.get(whatsapp='+5511777777777')
        self.assertEqual(contato.nome, 'Pedro Costa')
        self.assertEqual(contato.cliente.razao_social, 'Nova Empresa LTDA')
        self.assertEqual(contato.cliente.grupo_empresa, self.grupo)
    
    def test_cadastro_manual_whatsapp_duplicado(self):
        """Testa cadastro com WhatsApp já existente."""
        # Criar contato existente
        ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='João Existente',
            whatsapp='+5511999999999',
            criado_por=self.user
        )
        
        url = '/api/v1/clientes/cadastro-manual/'
        data = {
            'whatsapp': '+5511999999999',  # Mesmo WhatsApp
            'nome': 'João Novo',
            'empresa_id': self.cliente.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('WhatsApp já cadastrado', response.data['message'])
    
    def test_cadastro_manual_dados_invalidos(self):
        """Testa cadastro com dados inválidos."""
        url = '/api/v1/clientes/cadastro-manual/'
        data = {
            'whatsapp': '123',  # WhatsApp inválido
            'nome': 'Teste',
            'empresa_id': self.cliente.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('whatsapp', response.data)
    
    def test_cadastro_manual_empresa_obrigatoria(self):
        """Testa cadastro sem empresa (deve falhar)."""
        url = '/api/v1/clientes/cadastro-manual/'
        data = {
            'whatsapp': '+5511888888888',
            'nome': 'Teste'
            # Sem empresa_id nem empresa_nome
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_cadastro_manual_cnpj_invalido(self):
        """Testa cadastro com CNPJ inválido."""
        url = '/api/v1/clientes/cadastro-manual/'
        data = {
            'whatsapp': '+5511888888888',
            'nome': 'Teste',
            'empresa_nome': 'Empresa Teste',
            'empresa_cnpj': '123'  # CNPJ inválido
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('empresa_cnpj', response.data)
    
    def test_cadastro_manual_grupo_inexistente(self):
        """Testa cadastro com grupo de empresa inexistente."""
        url = '/api/v1/clientes/cadastro-manual/'
        data = {
            'whatsapp': '+5511888888888',
            'nome': 'Teste',
            'empresa_nome': 'Empresa Teste',
            'grupo_empresa_id': 999  # Grupo inexistente
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('grupo_empresa_id', response.data)
    
    def test_cadastro_manual_requer_autenticacao(self):
        """Testa que cadastro manual requer autenticação."""
        # Remover autenticação
        self.client.credentials()
        
        url = '/api/v1/clientes/cadastro-manual/'
        data = {
            'whatsapp': '+5511888888888',
            'nome': 'Teste',
            'empresa_id': self.cliente.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_cadastro_manual_empresa_inexistente(self):
        """Testa cadastro com empresa inexistente."""
        url = '/api/v1/clientes/cadastro-manual/'
        data = {
            'whatsapp': '+5511888888888',
            'nome': 'Teste',
            'empresa_id': 999  # Empresa inexistente
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('empresa_id', response.data)


class ContatoClienteViewSetTests(APITestCase):
    """Testes para ContatoClienteViewSet."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Limpar dados anteriores
        ContatoCliente.objects.all().delete()
        Cliente.objects.all().delete()
        GrupoEmpresa.objects.all().delete()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.grupo = GrupoEmpresa.objects.create(
            nome='Grupo Teste',
            criado_por=self.user
        )
        
        self.cliente = Cliente.objects.create(
            razao_social='Empresa Teste LTDA',
            cnpj='12.345.678/0001-90',
            grupo_empresa=self.grupo,
            criado_por=self.user
        )
        
        self.contato = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='João Silva',
            whatsapp='+5511999999999',
            cargo='Gerente',
            email='joao@empresa.com',
            criado_por=self.user
        )
        
        # Obter token JWT
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_list_contatos_authenticated(self):
        """Testa listagem de contatos autenticado."""
        url = '/api/v1/contatos/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['nome'], 'João Silva')
    
    def test_list_contatos_unauthenticated(self):
        """Testa listagem de contatos sem autenticação."""
        self.client.credentials()
        
        url = '/api/v1/contatos/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_contato(self):
        """Testa criação de contato."""
        url = '/api/v1/contatos/'
        data = {
            'cliente': self.cliente.id,
            'nome': 'Maria Santos',
            'whatsapp': '+5511888888888',
            'cargo': 'Analista',
            'email': 'maria@empresa.com'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nome'], 'Maria Santos')
        
        # Verificar no banco
        contato = ContatoCliente.objects.get(whatsapp='+5511888888888')
        self.assertEqual(contato.nome, 'Maria Santos')
        self.assertEqual(contato.cliente, self.cliente)
    
    def test_retrieve_contato(self):
        """Testa detalhamento de contato."""
        url = f'/api/v1/contatos/{self.contato.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome'], 'João Silva')
        self.assertEqual(response.data['whatsapp'], '+5511999999999')
    
    def test_update_contato(self):
        """Testa atualização de contato."""
        url = f'/api/v1/contatos/{self.contato.id}/'
        data = {
            'cliente': self.cliente.id,
            'nome': 'João Silva Atualizado',
            'whatsapp': '+5511999999999',
            'cargo': 'Gerente Senior',
            'email': 'joao.senior@empresa.com'
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome'], 'João Silva Atualizado')
        self.assertEqual(response.data['cargo'], 'Gerente Senior')
        
        # Verificar no banco
        self.contato.refresh_from_db()
        self.assertEqual(self.contato.nome, 'João Silva Atualizado')
        self.assertEqual(self.contato.cargo, 'Gerente Senior')
    
    def test_partial_update_contato(self):
        """Testa atualização parcial de contato."""
        url = f'/api/v1/contatos/{self.contato.id}/'
        data = {'cargo': 'Supervisor'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cargo'], 'Supervisor')
        
        # Verificar no banco
        self.contato.refresh_from_db()
        self.assertEqual(self.contato.cargo, 'Supervisor')
    
    def test_delete_contato(self):
        """Testa exclusão de contato."""
        url = f'/api/v1/contatos/{self.contato.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar que foi marcado como inativo (soft delete)
        self.contato.refresh_from_db()
        self.assertFalse(self.contato.ativo)
    
    def test_filter_contatos_por_cliente(self):
        """Testa filtro de contatos por cliente."""
        # Criar segundo cliente e contato
        cliente2 = Cliente.objects.create(
            razao_social='Empresa 2 LTDA',
            cnpj='98.765.432/0001-10',
            criado_por=self.user
        )
        
        contato2 = ContatoCliente.objects.create(
            cliente=cliente2,
            nome='Maria Santos',
            whatsapp='+5511888888888',
            criado_por=self.user
        )
        
        url = f'/api/v1/contatos/?cliente={self.cliente.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['nome'], 'João Silva')
    
    def test_search_contatos_por_nome(self):
        """Testa busca de contatos por nome."""
        url = '/api/v1/contatos/?search=João'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['nome'], 'João Silva')
    
    def test_contato_whatsapp_duplicado_mesmo_cliente(self):
        """Testa criação de contato com WhatsApp duplicado no mesmo cliente."""
        url = '/api/v1/contatos/'
        data = {
            'cliente': self.cliente.id,
            'nome': 'João Duplicado',
            'whatsapp': '+5511999999999',  # Mesmo WhatsApp do contato existente
            'cargo': 'Analista'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('unique', str(response.data).lower())


class GrupoEmpresaViewSetTests(APITestCase):
    """Testes para GrupoEmpresaViewSet."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Limpar dados anteriores
        ContatoCliente.objects.all().delete()
        Cliente.objects.all().delete()
        GrupoEmpresa.objects.all().delete()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.grupo = GrupoEmpresa.objects.create(
            nome='Grupo Teste',
            descricao='Descrição do grupo teste',
            criado_por=self.user
        )
        
        # Criar empresas no grupo
        self.cliente1 = Cliente.objects.create(
            razao_social='Empresa 1 LTDA',
            cnpj='11.111.111/0001-11',
            grupo_empresa=self.grupo,
            criado_por=self.user
        )
        
        self.cliente2 = Cliente.objects.create(
            razao_social='Empresa 2 LTDA',
            cnpj='22.222.222/0001-22',
            grupo_empresa=self.grupo,
            criado_por=self.user
        )
        
        # Obter token JWT
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_list_grupos_authenticated(self):
        """Testa listagem de grupos autenticado."""
        url = '/api/v1/grupos-empresa/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['nome'], 'Grupo Teste')
        self.assertEqual(response.data['results'][0]['empresas_count'], 2)
    
    def test_list_grupos_unauthenticated(self):
        """Testa listagem de grupos sem autenticação."""
        self.client.credentials()
        
        url = '/api/v1/grupos-empresa/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_grupo(self):
        """Testa criação de grupo."""
        url = '/api/v1/grupos-empresa/'
        data = {
            'nome': 'Novo Grupo',
            'descricao': 'Descrição do novo grupo',
            'ativo': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nome'], 'Novo Grupo')
        
        # Verificar no banco
        grupo = GrupoEmpresa.objects.get(nome='Novo Grupo')
        self.assertEqual(grupo.descricao, 'Descrição do novo grupo')
        self.assertTrue(grupo.ativo)
    
    def test_retrieve_grupo(self):
        """Testa detalhamento de grupo."""
        url = f'/api/v1/grupos-empresa/{self.grupo.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome'], 'Grupo Teste')
        self.assertEqual(response.data['empresas_count'], 2)
    
    def test_update_grupo(self):
        """Testa atualização de grupo."""
        url = f'/api/v1/grupos-empresa/{self.grupo.id}/'
        data = {
            'nome': 'Grupo Atualizado',
            'descricao': 'Nova descrição',
            'ativo': False
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome'], 'Grupo Atualizado')
        self.assertEqual(response.data['descricao'], 'Nova descrição')
        self.assertFalse(response.data['ativo'])
        
        # Verificar no banco
        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.nome, 'Grupo Atualizado')
        self.assertFalse(self.grupo.ativo)
    
    def test_partial_update_grupo(self):
        """Testa atualização parcial de grupo."""
        url = f'/api/v1/grupos-empresa/{self.grupo.id}/'
        data = {'descricao': 'Descrição atualizada'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['descricao'], 'Descrição atualizada')
        
        # Verificar no banco
        self.grupo.refresh_from_db()
        self.assertEqual(self.grupo.descricao, 'Descrição atualizada')
    
    def test_delete_grupo(self):
        """Testa exclusão de grupo."""
        url = f'/api/v1/grupos-empresa/{self.grupo.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar que foi deletado
        self.assertFalse(GrupoEmpresa.objects.filter(id=self.grupo.id).exists())
        
        # Verificar que empresas ainda existem mas grupo_empresa é None
        self.cliente1.refresh_from_db()
        self.cliente2.refresh_from_db()
        self.assertIsNone(self.cliente1.grupo_empresa)
        self.assertIsNone(self.cliente2.grupo_empresa)
    
    def test_search_grupos_por_nome(self):
        """Testa busca de grupos por nome."""
        url = '/api/v1/grupos-empresa/?search=Teste'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['nome'], 'Grupo Teste')
    
    def test_ordering_grupos_por_nome(self):
        """Testa ordenação de grupos por nome."""
        # Criar segundo grupo
        grupo2 = GrupoEmpresa.objects.create(
            nome='Grupo A',
            criado_por=self.user
        )
        
        url = '/api/v1/grupos-empresa/?ordering=nome'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['nome'], 'Grupo A')
        self.assertEqual(response.data['results'][1]['nome'], 'Grupo Teste')
    
    def test_grupo_nome_obrigatorio(self):
        """Testa criação de grupo sem nome."""
        url = '/api/v1/grupos-empresa/'
        data = {
            'descricao': 'Grupo sem nome'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nome', response.data)
