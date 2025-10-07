from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from clientes.models import GrupoEmpresa, Cliente

User = get_user_model()


class GrupoEmpresaModelTests(TestCase):
    """Testes para o modelo GrupoEmpresa."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_grupo_empresa_creation(self):
        """Testa criação básica de grupo de empresa."""
        grupo = GrupoEmpresa.objects.create(
            nome='Grupo Teste',
            descricao='Descrição do grupo teste',
            criado_por=self.user
        )
        
        self.assertEqual(grupo.nome, 'Grupo Teste')
        self.assertEqual(grupo.descricao, 'Descrição do grupo teste')
        self.assertTrue(grupo.ativo)
        self.assertEqual(grupo.criado_por, self.user)
        self.assertIsNotNone(grupo.criado_em)
        self.assertIsNotNone(grupo.atualizado_em)
    
    def test_grupo_empresa_str_representation(self):
        """Testa representação string do grupo."""
        grupo = GrupoEmpresa.objects.create(
            nome='Grupo ABC',
            criado_por=self.user
        )
        
        self.assertEqual(str(grupo), 'Grupo ABC')
    
    def test_grupo_empresa_verbose_names(self):
        """Testa verbose names do modelo."""
        self.assertEqual(GrupoEmpresa._meta.verbose_name, 'Grupo de Empresas')
        self.assertEqual(GrupoEmpresa._meta.verbose_name_plural, 'Grupos de Empresas')
    
    def test_grupo_empresa_ordering(self):
        """Testa ordenação padrão do modelo."""
        grupo1 = GrupoEmpresa.objects.create(nome='Grupo B', criado_por=self.user)
        grupo2 = GrupoEmpresa.objects.create(nome='Grupo A', criado_por=self.user)
        grupo3 = GrupoEmpresa.objects.create(nome='Grupo C', criado_por=self.user)
        
        grupos = list(GrupoEmpresa.objects.all())
        self.assertEqual(grupos[0], grupo2)  # Grupo A
        self.assertEqual(grupos[1], grupo1)  # Grupo B
        self.assertEqual(grupos[2], grupo3)  # Grupo C
    
    def test_grupo_empresa_optional_fields(self):
        """Testa campos opcionais do grupo."""
        grupo = GrupoEmpresa.objects.create(
            nome='Grupo Simples',
            ativo=False
        )
        
        self.assertEqual(grupo.nome, 'Grupo Simples')
        self.assertFalse(grupo.ativo)
        self.assertIsNone(grupo.descricao)
        self.assertIsNone(grupo.criado_por)
    
    def test_grupo_empresa_empresas_relationship(self):
        """Testa relacionamento com empresas."""
        grupo = GrupoEmpresa.objects.create(
            nome='Grupo Teste',
            criado_por=self.user
        )
        
        # Criar empresas no grupo
        empresa1 = Cliente.objects.create(
            razao_social='Empresa 1 LTDA',
            cnpj='11.111.111/0001-11',
            grupo_empresa=grupo
        )
        
        empresa2 = Cliente.objects.create(
            razao_social='Empresa 2 LTDA',
            cnpj='22.222.222/0001-22',
            grupo_empresa=grupo
        )
        
        # Verificar relacionamento
        self.assertEqual(grupo.empresas.count(), 2)
        self.assertIn(empresa1, grupo.empresas.all())
        self.assertIn(empresa2, grupo.empresas.all())
    
    def test_grupo_empresa_auto_timestamps(self):
        """Testa timestamps automáticos."""
        grupo = GrupoEmpresa.objects.create(
            nome='Grupo Timestamp',
            criado_por=self.user
        )
        
        # Verificar que timestamps foram criados
        self.assertIsNotNone(grupo.criado_em)
        self.assertIsNotNone(grupo.atualizado_em)
        
        # Atualizar e verificar se atualizado_em mudou
        import time
        time.sleep(0.1)  # Pequena pausa para garantir diferença de tempo
        
        grupo.nome = 'Grupo Atualizado'
        grupo.save()
        
        # Verificar que atualizado_em foi atualizado
        self.assertGreater(grupo.atualizado_em, grupo.criado_em)
    
    def test_grupo_empresa_cascade_delete(self):
        """Testa comportamento ao deletar grupo."""
        grupo = GrupoEmpresa.objects.create(
            nome='Grupo para Deletar',
            criado_por=self.user
        )
        
        empresa = Cliente.objects.create(
            razao_social='Empresa Teste LTDA',
            cnpj='33.333.333/0001-33',
            grupo_empresa=grupo
        )
        
        # Deletar grupo
        grupo.delete()
        
        # Verificar que empresa ainda existe mas grupo_empresa é None
        empresa.refresh_from_db()
        self.assertIsNone(empresa.grupo_empresa)
    
    def test_grupo_empresa_indexes(self):
        """Testa se os índices foram criados corretamente."""
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'clientes_grupoempresa'
                AND indexname LIKE '%nome%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
        
        # Verificar se índice de nome existe
        self.assertTrue(any('nome' in idx for idx in indexes))
    
    def test_grupo_empresa_empresas_count_property(self):
        """Testa propriedade empresas_count no serializer."""
        grupo = GrupoEmpresa.objects.create(
            nome='Grupo Contagem',
            criado_por=self.user
        )
        
        # Criar algumas empresas
        Cliente.objects.create(
            razao_social='Empresa 1',
            cnpj='11.111.111/0001-11',
            grupo_empresa=grupo
        )
        
        Cliente.objects.create(
            razao_social='Empresa 2',
            cnpj='22.222.222/0001-22',
            grupo_empresa=grupo
        )
        
        # Verificar contagem
        self.assertEqual(grupo.empresas.count(), 2)
