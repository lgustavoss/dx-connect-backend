from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from clientes.models import Cliente, GrupoEmpresa, ContatoCliente

User = get_user_model()


class ClienteRefatoradoModelTests(TestCase):
    """Testes para o modelo Cliente refatorado (Pessoa Jurídica)."""
    
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
    
    def test_cliente_creation_basic(self):
        """Testa criação básica de cliente."""
        cliente = Cliente.objects.create(
            razao_social='Empresa Teste LTDA',
            cnpj='12.345.678/0001-90',
            grupo_empresa=self.grupo,
            criado_por=self.user
        )
        
        self.assertEqual(cliente.razao_social, 'Empresa Teste LTDA')
        self.assertEqual(cliente.cnpj, '12.345.678/0001-90')
        self.assertEqual(cliente.grupo_empresa, self.grupo)
        self.assertEqual(cliente.criado_por, self.user)
        self.assertEqual(cliente.regime_tributario, 'simples_nacional')
    
    def test_cliente_creation_with_all_fields(self):
        """Testa criação de cliente com todos os campos."""
        cliente = Cliente.objects.create(
            grupo_empresa=self.grupo,
            razao_social='Empresa Completa LTDA',
            nome_fantasia='Empresa Fantasia',
            cnpj='98.765.432/0001-10',
            inscricao_estadual='123456789',
            inscricao_municipal='987654321',
            ramo_atividade='Tecnologia',
            regime_tributario='lucro_real',
            responsavel_legal_nome='João Silva',
            responsavel_legal_cpf='123.456.789-00',
            responsavel_legal_cargo='Diretor',
            email_principal='contato@empresa.com',
            telefone_principal='+5511999999999',
            endereco='Rua das Flores, 123',
            numero='123',
            complemento='Sala 45',
            bairro='Centro',
            cidade='São Paulo',
            estado='SP',
            cep='01234-567',
            status='ativo',
            observacoes='Cliente VIP',
            criado_por=self.user,
            atualizado_por=self.user
        )
        
        # Verificar campos básicos
        self.assertEqual(cliente.razao_social, 'Empresa Completa LTDA')
        self.assertEqual(cliente.nome_fantasia, 'Empresa Fantasia')
        self.assertEqual(cliente.cnpj, '98.765.432/0001-10')
        
        # Verificar campos específicos PJ
        self.assertEqual(cliente.inscricao_estadual, '123456789')
        self.assertEqual(cliente.inscricao_municipal, '987654321')
        self.assertEqual(cliente.ramo_atividade, 'Tecnologia')
        self.assertEqual(cliente.regime_tributario, 'lucro_real')
        
        # Verificar responsável legal
        self.assertEqual(cliente.responsavel_legal_nome, 'João Silva')
        self.assertEqual(cliente.responsavel_legal_cpf, '123.456.789-00')
        self.assertEqual(cliente.responsavel_legal_cargo, 'Diretor')
        
        # Verificar contatos
        self.assertEqual(cliente.email_principal, 'contato@empresa.com')
        self.assertEqual(cliente.telefone_principal, '+5511999999999')
        
        # Verificar endereço
        self.assertEqual(cliente.endereco, 'Rua das Flores, 123')
        self.assertEqual(cliente.numero, '123')
        self.assertEqual(cliente.complemento, 'Sala 45')
        self.assertEqual(cliente.bairro, 'Centro')
        self.assertEqual(cliente.cidade, 'São Paulo')
        self.assertEqual(cliente.estado, 'SP')
        self.assertEqual(cliente.cep, '01234-567')
        
        # Verificar status e observações
        self.assertEqual(cliente.status, 'ativo')
        self.assertEqual(cliente.observacoes, 'Cliente VIP')
        
        # Verificar auditoria
        self.assertEqual(cliente.criado_por, self.user)
        self.assertEqual(cliente.atualizado_por, self.user)
    
    def test_cliente_cnpj_unique(self):
        """Testa que CNPJ deve ser único."""
        Cliente.objects.create(
            razao_social='Empresa 1',
            cnpj='11.111.111/0001-11',
            criado_por=self.user
        )
        
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(
                razao_social='Empresa 2',
                cnpj='11.111.111/0001-11',  # Mesmo CNPJ
                criado_por=self.user
            )
    
    def test_cliente_str_representation(self):
        """Testa representação string do cliente."""
        cliente = Cliente.objects.create(
            razao_social='Empresa ABC LTDA',
            cnpj='12.345.678/0001-90',
            criado_por=self.user
        )
        
        self.assertEqual(str(cliente), 'Empresa ABC LTDA (12.345.678/0001-90)')
    
    def test_cliente_verbose_names(self):
        """Testa verbose names do modelo."""
        self.assertEqual(Cliente._meta.verbose_name, 'Cliente')
        self.assertEqual(Cliente._meta.verbose_name_plural, 'Clientes')
    
    def test_cliente_choices(self):
        """Testa choices do modelo."""
        # Testar regime tributário
        regimes = [choice[0] for choice in Cliente.REGIME_TRIBUTARIO_CHOICES]
        expected_regimes = ['simples_nacional', 'lucro_presumido', 'lucro_real', 'mei', 'outro']
        self.assertEqual(regimes, expected_regimes)
        
        # Testar status
        status_choices = [choice[0] for choice in Cliente.STATUS_CHOICES]
        expected_status = ['ativo', 'inativo', 'suspenso', 'bloqueado']
        self.assertEqual(status_choices, expected_status)
    
    def test_cliente_clean_method_valid_cnpj(self):
        """Testa método clean com CNPJ válido."""
        cliente = Cliente(
            razao_social='Empresa Teste',
            cnpj='11.222.333/0001-81',  # CNPJ válido
            responsavel_legal_cpf='123.456.789-09',  # CPF válido
            criado_por=self.user
        )
        
        # Não deve levantar exceção
        cliente.clean()
    
    def test_cliente_clean_method_invalid_cnpj(self):
        """Testa método clean com CNPJ inválido."""
        cliente = Cliente(
            razao_social='Empresa Teste',
            cnpj='11.222.333/0001-82',  # CNPJ inválido
            responsavel_legal_cpf='123.456.789-09',
            criado_por=self.user
        )
        
        with self.assertRaises(ValidationError):
            cliente.clean()
    
    def test_cliente_clean_method_invalid_cpf(self):
        """Testa método clean com CPF inválido."""
        cliente = Cliente(
            razao_social='Empresa Teste',
            cnpj='11.222.333/0001-81',
            responsavel_legal_cpf='123.456.789-10',  # CPF inválido
            criado_por=self.user
        )
        
        with self.assertRaises(ValidationError):
            cliente.clean()
    
    def test_cliente_properties(self):
        """Testa propriedades do modelo."""
        cliente = Cliente.objects.create(
            razao_social='Empresa Razão Social',
            nome_fantasia='Empresa Fantasia',
            cnpj='12.345.678/0001-90',
            endereco='Rua das Flores',
            numero='123',
            complemento='Sala 45',
            bairro='Centro',
            cidade='São Paulo',
            estado='SP',
            cep='01234-567',
            criado_por=self.user
        )
        
        # Testar nome_display
        self.assertEqual(cliente.nome_display, 'Empresa Fantasia')
        
        # Testar endereco_completo
        endereco_esperado = 'Rua das Flores - nº 123 - Sala 45 - Centro - São Paulo - SP - CEP: 01234-567'
        self.assertEqual(cliente.endereco_completo, endereco_esperado)
    
    def test_cliente_properties_without_fantasia(self):
        """Testa propriedades quando não há nome fantasia."""
        cliente = Cliente.objects.create(
            razao_social='Empresa Razão Social',
            cnpj='12.345.678/0001-90',
            criado_por=self.user
        )
        
        # Testar nome_display sem fantasia
        self.assertEqual(cliente.nome_display, 'Empresa Razão Social')
    
    def test_cliente_contatos_principais_property(self):
        """Testa propriedade contatos_principais (email e telefone da empresa)."""
        cliente = Cliente.objects.create(
            razao_social='Empresa Teste',
            cnpj='12.345.678/0001-90',
            email_principal='contato@empresa.com',
            telefone_principal='+5511999999999',
            criado_por=self.user
        )
        
        # Verificar propriedade (contatos de email/telefone da empresa)
        contatos = cliente.contatos_principais
        self.assertEqual(len(contatos), 2)
        self.assertIn('Email: contato@empresa.com', contatos)
        self.assertIn('Tel: +5511999999999', contatos)
    
    def test_cliente_indexes(self):
        """Testa se os índices foram criados corretamente."""
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'clientes_cliente'
                AND indexname LIKE '%clientes_cliente%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
        
        # Verificar índices esperados
        expected_indexes = [
            'clientes_cliente_cnpj_idx',
            'clientes_cliente_razao_social_idx',
            'clientes_cliente_nome_fantasia_idx',
            'clientes_cliente_status_idx',
            'clientes_cliente_criado_em_idx'
        ]
        
        for expected_idx in expected_indexes:
            self.assertTrue(any(expected_idx in idx for idx in indexes))
    
    def test_cliente_auto_timestamps(self):
        """Testa timestamps automáticos."""
        cliente = Cliente.objects.create(
            razao_social='Empresa Timestamp',
            cnpj='12.345.678/0001-90',
            criado_por=self.user
        )
        
        # Verificar que timestamps foram criados
        self.assertIsNotNone(cliente.criado_em)
        self.assertIsNotNone(cliente.atualizado_em)
        
        # Atualizar e verificar se atualizado_em mudou
        import time
        time.sleep(0.1)
        
        cliente.razao_social = 'Empresa Atualizada'
        cliente.save()
        
        # Verificar que atualizado_em foi atualizado
        self.assertGreater(cliente.atualizado_em, cliente.criado_em)
    
    def test_cliente_grupo_empresa_relationship(self):
        """Testa relacionamento com grupo de empresa."""
        cliente = Cliente.objects.create(
            razao_social='Empresa do Grupo',
            cnpj='12.345.678/0001-90',
            grupo_empresa=self.grupo,
            criado_por=self.user
        )
        
        # Verificar relacionamento
        self.assertEqual(cliente.grupo_empresa, self.grupo)
        self.assertIn(cliente, self.grupo.empresas.all())
    
    def test_cliente_without_grupo(self):
        """Testa cliente sem grupo de empresa."""
        cliente = Cliente.objects.create(
            razao_social='Empresa Independente',
            cnpj='12.345.678/0001-90',
            criado_por=self.user
        )
        
        # Verificar que grupo é None
        self.assertIsNone(cliente.grupo_empresa)
