from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from clientes.models import Cliente, ContatoCliente, GrupoEmpresa
from clientes.serializers import (
    DadosCapturadosChatSerializer,
    CadastroManualContatoSerializer,
    BuscaContatoSerializer,
    ContatoClienteSerializer,
    GrupoEmpresaSerializer
)

User = get_user_model()


class DadosCapturadosChatSerializerTests(TestCase):
    """Testes para o serializer DadosCapturadosChatSerializer."""
    
    def test_valid_data(self):
        """Testa dados válidos."""
        data = {
            'whatsapp': '+5511999999999',
            'nome': 'João Silva',
            'empresa_nome': 'Empresa ABC LTDA',
            'cargo': 'Gerente'
        }
        
        serializer = DadosCapturadosChatSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['whatsapp'], '+5511999999999')
        self.assertEqual(serializer.validated_data['nome'], 'João Silva')
        self.assertEqual(serializer.validated_data['empresa_nome'], 'Empresa ABC LTDA')
        self.assertEqual(serializer.validated_data['cargo'], 'Gerente')
    
    def test_whatsapp_validation_valid(self):
        """Testa validação de WhatsApp válido."""
        valid_whatsapps = [
            '+5511999999999',
            '5511999999999',
            '+1234567890',
            '1234567890'
        ]
        
        for whatsapp in valid_whatsapps:
            with self.subTest(whatsapp=whatsapp):
                data = {
                    'whatsapp': whatsapp,
                    'nome': 'João Silva',
                    'empresa_nome': 'Empresa ABC LTDA'
                }
                serializer = DadosCapturadosChatSerializer(data=data)
                self.assertTrue(serializer.is_valid(), f"Falhou para WhatsApp: {whatsapp}")
    
    def test_whatsapp_validation_invalid(self):
        """Testa validação de WhatsApp inválido."""
        invalid_whatsapps = [
            '123',  # Muito curto
            'abc',  # Não numérico
            '',     # Vazio
            '+123', # Muito curto
        ]
        
        for whatsapp in invalid_whatsapps:
            with self.subTest(whatsapp=whatsapp):
                data = {
                    'whatsapp': whatsapp,
                    'nome': 'João Silva',
                    'empresa_nome': 'Empresa ABC LTDA'
                }
                serializer = DadosCapturadosChatSerializer(data=data)
                self.assertFalse(serializer.is_valid(), f"Deve falhar para WhatsApp: {whatsapp}")
                self.assertIn('whatsapp', serializer.errors)
    
    def test_required_fields(self):
        """Testa campos obrigatórios."""
        required_fields = ['whatsapp', 'nome', 'empresa_nome']
        
        for field in required_fields:
            with self.subTest(field=field):
                data = {
                    'whatsapp': '+5511999999999',
                    'nome': 'João Silva',
                    'empresa_nome': 'Empresa ABC LTDA'
                }
                del data[field]
                
                serializer = DadosCapturadosChatSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)


class CadastroManualContatoSerializerTests(TestCase):
    """Testes para o serializer CadastroManualContatoSerializer."""
    
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
            razao_social='Empresa Existente LTDA',
            cnpj='12.345.678/0001-90',
            grupo_empresa=self.grupo,
            criado_por=self.user
        )
    
    def test_valid_data_with_existing_empresa(self):
        """Testa dados válidos com empresa existente."""
        data = {
            'whatsapp': '+5511999999999',
            'nome': 'João Silva',
            'cargo': 'Gerente',
            'email': 'joao@empresa.com',
            'empresa_id': self.cliente.id
        }
        
        serializer = CadastroManualContatoSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_valid_data_with_new_empresa(self):
        """Testa dados válidos com nova empresa."""
        data = {
            'whatsapp': '+5511888888888',
            'nome': 'Maria Santos',
            'cargo': 'Supervisora',
            'email': 'maria@empresa.com',
            'empresa_nome': 'Nova Empresa LTDA',
            'empresa_cnpj': '11.222.333/0001-81',  # CNPJ válido
            'grupo_empresa_id': self.grupo.id
        }
        
        serializer = CadastroManualContatoSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_validation_empresa_id_or_nome_required(self):
        """Testa que deve ter empresa_id OU empresa_nome."""
        data = {
            'whatsapp': '+5511999999999',
            'nome': 'João Silva'
            # Sem empresa_id nem empresa_nome
        }
        
        serializer = CadastroManualContatoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_create_with_existing_empresa(self):
        """Testa criação com empresa existente."""
        data = {
            'whatsapp': '+5511999999999',
            'nome': 'João Silva',
            'cargo': 'Gerente',
            'email': 'joao@empresa.com',
            'empresa_id': self.cliente.id
        }
        
        serializer = CadastroManualContatoSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        contato = serializer.save()
        
        self.assertEqual(contato.cliente, self.cliente)
        self.assertEqual(contato.nome, 'João Silva')
        self.assertEqual(contato.whatsapp, '+5511999999999')
        self.assertEqual(contato.cargo, 'Gerente')
        self.assertEqual(contato.email, 'joao@empresa.com')
    
    def test_create_with_new_empresa(self):
        """Testa criação com nova empresa."""
        data = {
            'whatsapp': '+5511888888888',
            'nome': 'Maria Santos',
            'cargo': 'Supervisora',
            'email': 'maria@empresa.com',
            'empresa_nome': 'Nova Empresa LTDA',
            'empresa_cnpj': '11.222.333/0001-81',  # CNPJ válido
            'grupo_empresa_id': self.grupo.id
        }
        
        serializer = CadastroManualContatoSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        contato = serializer.save()
        
        self.assertEqual(contato.nome, 'Maria Santos')
        self.assertEqual(contato.whatsapp, '+5511888888888')
        self.assertEqual(contato.cliente.razao_social, 'Nova Empresa LTDA')
        self.assertEqual(contato.cliente.cnpj, '11222333000181')
        self.assertEqual(contato.cliente.grupo_empresa, self.grupo)
    
    def test_create_with_duplicate_whatsapp_same_empresa(self):
        """Testa criação com WhatsApp duplicado na mesma empresa (deve falhar)."""
        # Criar contato existente
        ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='João Existente',
            whatsapp='+5511999999999',
            criado_por=self.user
        )
        
        data = {
            'whatsapp': '+5511999999999',  # Mesmo WhatsApp na mesma empresa
            'nome': 'João Novo',
            'empresa_id': self.cliente.id
        }
        
        serializer = CadastroManualContatoSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Deve falhar ao salvar devido ao unique_together
        with self.assertRaises(Exception):  # IntegrityError ou ValidationError
            serializer.save()
    
    def test_whatsapp_validation(self):
        """Testa validação de WhatsApp."""
        data = {
            'whatsapp': '123',  # Inválido
            'nome': 'João Silva',
            'empresa_id': self.cliente.id
        }
        
        serializer = CadastroManualContatoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('whatsapp', serializer.errors)
    
    def test_empresa_cnpj_validation(self):
        """Testa validação de CNPJ."""
        data = {
            'whatsapp': '+5511999999999',
            'nome': 'João Silva',
            'empresa_nome': 'Nova Empresa LTDA',
            'empresa_cnpj': '123'  # CNPJ inválido (muito curto)
        }
        
        serializer = CadastroManualContatoSerializer(data=data)
        # Deve falhar na validação do CNPJ
        self.assertFalse(serializer.is_valid())
        self.assertIn('empresa_cnpj', serializer.errors)
    
    def test_grupo_empresa_validation(self):
        """Testa validação de grupo de empresa."""
        data = {
            'whatsapp': '+5511999999999',
            'nome': 'João Silva',
            'empresa_nome': 'Nova Empresa LTDA',
            'grupo_empresa_id': 999  # Grupo inexistente
        }
        
        serializer = CadastroManualContatoSerializer(data=data)
        # O serializer valida se o grupo existe
        self.assertFalse(serializer.is_valid())
        self.assertIn('grupo_empresa_id', serializer.errors)


class BuscaContatoSerializerTests(TestCase):
    """Testes para o serializer BuscaContatoSerializer."""
    
    def test_valid_whatsapp(self):
        """Testa WhatsApp válido."""
        data = {'whatsapp': '+5511999999999'}
        serializer = BuscaContatoSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['whatsapp'], '+5511999999999')
    
    def test_invalid_whatsapp(self):
        """Testa WhatsApp inválido."""
        invalid_whatsapps = ['123', 'abc', '', '+123']
        
        for whatsapp in invalid_whatsapps:
            with self.subTest(whatsapp=whatsapp):
                data = {'whatsapp': whatsapp}
                serializer = BuscaContatoSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn('whatsapp', serializer.errors)
    
    def test_required_whatsapp(self):
        """Testa que WhatsApp é obrigatório."""
        data = {}
        serializer = BuscaContatoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('whatsapp', serializer.errors)


class ContatoClienteSerializerTests(TestCase):
    """Testes para o serializer ContatoClienteSerializer."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.cliente = Cliente.objects.create(
            razao_social='Empresa Teste LTDA',
            cnpj='12.345.678/0001-90',
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
    
    def test_serialization(self):
        """Testa serialização do contato."""
        serializer = ContatoClienteSerializer(self.contato)
        data = serializer.data
        
        self.assertEqual(data['id'], self.contato.id)
        self.assertEqual(data['cliente'], self.cliente.id)
        self.assertEqual(data['cliente_nome'], 'Empresa Teste LTDA')
        self.assertEqual(data['nome'], 'João Silva')
        self.assertEqual(data['whatsapp'], '+5511999999999')
        self.assertEqual(data['cargo'], 'Gerente')
        self.assertEqual(data['email'], 'joao@empresa.com')
        self.assertTrue(data['ativo'])
    
    def test_deserialization_valid(self):
        """Testa deserialização válida."""
        data = {
            'cliente': self.cliente.id,
            'nome': 'Maria Santos',
            'whatsapp': '+5511888888888',
            'cargo': 'Supervisora',
            'email': 'maria@empresa.com'
        }
        
        serializer = ContatoClienteSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_whatsapp_validation(self):
        """Testa validação de WhatsApp."""
        data = {
            'cliente': self.cliente.id,
            'nome': 'Maria Santos',
            'whatsapp': '123',  # Inválido
            'email': 'maria@empresa.com'
        }
        
        serializer = ContatoClienteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('whatsapp', serializer.errors)


class GrupoEmpresaSerializerTests(TestCase):
    """Testes para o serializer GrupoEmpresaSerializer."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.grupo = GrupoEmpresa.objects.create(
            nome='Grupo Teste',
            descricao='Descrição do grupo',
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
    
    def test_serialization(self):
        """Testa serialização do grupo."""
        serializer = GrupoEmpresaSerializer(self.grupo)
        data = serializer.data
        
        self.assertEqual(data['id'], self.grupo.id)
        self.assertEqual(data['nome'], 'Grupo Teste')
        self.assertEqual(data['descricao'], 'Descrição do grupo')
        self.assertTrue(data['ativo'])
        self.assertEqual(data['empresas_count'], 2)
    
    def test_empresas_count_property(self):
        """Testa propriedade empresas_count."""
        serializer = GrupoEmpresaSerializer(self.grupo)
        data = serializer.data
        
        self.assertEqual(data['empresas_count'], 2)
        
        # Adicionar mais uma empresa
        Cliente.objects.create(
            razao_social='Empresa 3 LTDA',
            cnpj='33.333.333/0001-33',
            grupo_empresa=self.grupo,
            criado_por=self.user
        )
        
        # Recarregar e testar novamente
        self.grupo.refresh_from_db()
        serializer = GrupoEmpresaSerializer(self.grupo)
        data = serializer.data
        
        self.assertEqual(data['empresas_count'], 3)
    
    def test_deserialization_valid(self):
        """Testa deserialização válida."""
        data = {
            'nome': 'Novo Grupo',
            'descricao': 'Descrição do novo grupo',
            'ativo': True
        }
        
        serializer = GrupoEmpresaSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_deserialization_invalid(self):
        """Testa deserialização inválida."""
        data = {
            'nome': '',  # Nome vazio
            'descricao': 'Descrição válida'
        }
        
        serializer = GrupoEmpresaSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('nome', serializer.errors)
