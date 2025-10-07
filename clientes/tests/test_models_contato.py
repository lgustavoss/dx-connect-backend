from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from clientes.models import Cliente, ContatoCliente, GrupoEmpresa

User = get_user_model()


class ContatoClienteModelTests(TestCase):
    """Testes para o modelo ContatoCliente."""
    
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
    
    def test_contato_creation_basic(self):
        """Testa criação básica de contato."""
        contato = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='João Silva',
            whatsapp='+5511999999999',
            criado_por=self.user
        )
        
        self.assertEqual(contato.cliente, self.cliente)
        self.assertEqual(contato.nome, 'João Silva')
        self.assertEqual(contato.whatsapp, '+5511999999999')
        self.assertEqual(contato.criado_por, self.user)
        self.assertTrue(contato.ativo)
        self.assertIsNotNone(contato.criado_em)
        self.assertIsNotNone(contato.atualizado_em)
    
    def test_contato_creation_with_all_fields(self):
        """Testa criação de contato com todos os campos."""
        contato = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='Maria Santos',
            cargo='Gerente de Vendas',
            whatsapp='+5511888888888',
            email='maria@empresa.com',
            ativo=True,
            criado_por=self.user
        )
        
        self.assertEqual(contato.cliente, self.cliente)
        self.assertEqual(contato.nome, 'Maria Santos')
        self.assertEqual(contato.cargo, 'Gerente de Vendas')
        self.assertEqual(contato.whatsapp, '+5511888888888')
        self.assertEqual(contato.email, 'maria@empresa.com')
        self.assertTrue(contato.ativo)
        self.assertEqual(contato.criado_por, self.user)
    
    def test_contato_str_representation(self):
        """Testa representação string do contato."""
        contato = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='Pedro Costa',
            whatsapp='+5511777777777',
            criado_por=self.user
        )
        
        expected = 'Pedro Costa - Empresa Teste LTDA'
        self.assertEqual(str(contato), expected)
    
    def test_contato_verbose_names(self):
        """Testa verbose names do modelo."""
        self.assertEqual(ContatoCliente._meta.verbose_name, 'Contato da Empresa')
        self.assertEqual(ContatoCliente._meta.verbose_name_plural, 'Contatos das Empresas')
    
    def test_contato_ordering(self):
        """Testa ordenação padrão do modelo."""
        contato1 = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='Carlos',
            whatsapp='+5511111111111',
            criado_por=self.user
        )
        
        contato2 = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='Ana',
            whatsapp='+5511222222222',
            criado_por=self.user
        )
        
        contato3 = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='Bruno',
            whatsapp='+5511333333333',
            criado_por=self.user
        )
        
        contatos = list(ContatoCliente.objects.all())
        self.assertEqual(contatos[0], contato2)  # Ana
        self.assertEqual(contatos[1], contato3)  # Bruno
        self.assertEqual(contatos[2], contato1)  # Carlos
    
    def test_contato_unique_together(self):
        """Testa constraint unique_together (cliente, whatsapp)."""
        # Criar primeiro contato
        ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='João Silva',
            whatsapp='+5511999999999',
            criado_por=self.user
        )
        
        # Tentar criar segundo contato com mesmo WhatsApp na mesma empresa
        with self.assertRaises(IntegrityError):
            ContatoCliente.objects.create(
                cliente=self.cliente,
                nome='João Santos',
                whatsapp='+5511999999999',  # Mesmo WhatsApp
                criado_por=self.user
            )
    
    def test_contato_same_whatsapp_different_empresas(self):
        """Testa que mesmo WhatsApp pode existir em empresas diferentes."""
        # Criar segunda empresa
        cliente2 = Cliente.objects.create(
            razao_social='Empresa 2 LTDA',
            cnpj='98.765.432/0001-10',
            criado_por=self.user
        )
        
        # Criar contato na primeira empresa
        contato1 = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='João Silva',
            whatsapp='+5511999999999',
            criado_por=self.user
        )
        
        # Criar contato na segunda empresa com mesmo WhatsApp
        contato2 = ContatoCliente.objects.create(
            cliente=cliente2,
            nome='João Santos',
            whatsapp='+5511999999999',  # Mesmo WhatsApp, empresa diferente
            criado_por=self.user
        )
        
        # Deve funcionar sem erro
        self.assertEqual(contato1.whatsapp, contato2.whatsapp)
        self.assertNotEqual(contato1.cliente, contato2.cliente)
    
    def test_contato_contatos_disponiveis_property(self):
        """Testa propriedade contatos_disponiveis."""
        # Contato com WhatsApp e email
        contato1 = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='João Silva',
            whatsapp='+5511999999999',
            email='joao@empresa.com',
            criado_por=self.user
        )
        
        contatos = contato1.contatos_disponiveis
        self.assertEqual(len(contatos), 2)
        self.assertIn('WA: +5511999999999', contatos)
        self.assertIn('Email: joao@empresa.com', contatos)
        
        # Contato apenas com WhatsApp
        contato2 = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='Maria Santos',
            whatsapp='+5511888888888',
            criado_por=self.user
        )
        
        contatos = contato2.contatos_disponiveis
        self.assertEqual(len(contatos), 1)
        self.assertIn('WA: +5511888888888', contatos)
    
    def test_contato_auto_timestamps(self):
        """Testa timestamps automáticos."""
        contato = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='Contato Timestamp',
            whatsapp='+5511999999999',
            criado_por=self.user
        )
        
        # Verificar que timestamps foram criados
        self.assertIsNotNone(contato.criado_em)
        self.assertIsNotNone(contato.atualizado_em)
        
        # Atualizar e verificar se atualizado_em mudou
        import time
        time.sleep(0.1)
        
        contato.nome = 'Contato Atualizado'
        contato.save()
        
        # Verificar que atualizado_em foi atualizado
        self.assertGreater(contato.atualizado_em, contato.criado_em)
    
    def test_contato_cascade_delete(self):
        """Testa comportamento ao deletar cliente."""
        contato = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='Contato para Deletar',
            whatsapp='+5511999999999',
            criado_por=self.user
        )
        
        # Deletar cliente
        self.cliente.delete()
        
        # Verificar que contato foi deletado também
        self.assertFalse(ContatoCliente.objects.filter(id=contato.id).exists())
    
    def test_contato_indexes(self):
        """Testa se os índices foram criados corretamente."""
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'clientes_contatocliente'
                AND indexname LIKE '%clientes_contatocliente%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
        
        # Verificar índices esperados
        expected_indexes = [
            'clientes_contatocliente_cliente_ativo_idx',
            'clientes_contatocliente_whatsapp_idx',
            'clientes_contatocliente_nome_idx'
        ]
        
        for expected_idx in expected_indexes:
            self.assertTrue(any(expected_idx in idx for idx in indexes))
    
    def test_contato_optional_fields(self):
        """Testa campos opcionais do contato."""
        contato = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='Contato Simples',
            whatsapp='+5511999999999'
        )
        
        self.assertEqual(contato.nome, 'Contato Simples')
        self.assertEqual(contato.whatsapp, '+5511999999999')
        self.assertIsNone(contato.cargo)
        self.assertIsNone(contato.email)
        self.assertTrue(contato.ativo)
        self.assertIsNone(contato.criado_por)
    
    def test_contato_whatsapp_validation(self):
        """Testa validação de formato do WhatsApp."""
        # WhatsApp válido
        contato = ContatoCliente(
            cliente=self.cliente,
            nome='Teste',
            whatsapp='+5511999999999'
        )
        contato.full_clean()  # Não deve levantar exceção
        
        # WhatsApp inválido (muito curto)
        contato_invalido = ContatoCliente(
            cliente=self.cliente,
            nome='Teste',
            whatsapp='123'
        )
        with self.assertRaises(ValidationError):
            contato_invalido.full_clean()
    
    def test_contato_email_validation(self):
        """Testa validação de formato do email."""
        # Email válido
        contato = ContatoCliente(
            cliente=self.cliente,
            nome='Teste',
            whatsapp='+5511999999999',
            email='teste@empresa.com'
        )
        contato.full_clean()  # Não deve levantar exceção
        
        # Email inválido
        contato_invalido = ContatoCliente(
            cliente=self.cliente,
            nome='Teste',
            whatsapp='+5511999999999',
            email='email-invalido'
        )
        with self.assertRaises(ValidationError):
            contato_invalido.full_clean()
    
    def test_contato_relationship_with_cliente(self):
        """Testa relacionamento com cliente."""
        contato = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='Relacionamento Teste',
            whatsapp='+5511999999999',
            criado_por=self.user
        )
        
        # Verificar relacionamento direto
        self.assertEqual(contato.cliente, self.cliente)
        
        # Verificar relacionamento reverso
        self.assertIn(contato, self.cliente.contatos.all())
    
    def test_contato_relationship_with_user(self):
        """Testa relacionamento com usuário criador."""
        contato = ContatoCliente.objects.create(
            cliente=self.cliente,
            nome='User Teste',
            whatsapp='+5511999999999',
            criado_por=self.user
        )
        
        # Verificar relacionamento
        self.assertEqual(contato.criado_por, self.user)
        
        # Verificar relacionamento reverso
        self.assertIn(contato, self.user.contatos_criados.all())
