"""
Testes unitários para o modelo DocumentoCliente.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from clientes.models import Cliente, DocumentoCliente, GrupoEmpresa

User = get_user_model()


class DocumentoClienteModelTests(TestCase):
    """Testes para o modelo DocumentoCliente."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
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
    
    def test_documento_creation_basic(self):
        """Testa criação básica de documento."""
        documento = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Documento Teste",
            tipo_documento="contrato",
            arquivo="teste.txt",
            usuario_upload=self.user
        )
        
        self.assertEqual(documento.cliente, self.cliente)
        self.assertEqual(documento.nome, "Documento Teste")
        self.assertEqual(documento.tipo_documento, "contrato")
        self.assertEqual(documento.status, "gerado")  # valor padrão
        self.assertEqual(documento.origem, "manual")  # valor padrão
        self.assertEqual(documento.usuario_upload, self.user)
        self.assertTrue(documento.ativo)  # valor padrão
    
    def test_documento_creation_with_all_fields(self):
        """Testa criação de documento com todos os campos."""
        dados_preenchidos = {
            "valor_servico": "1000.00",
            "data_inicio": "01/01/2024",
            "data_fim": "31/12/2024"
        }
        
        data_vencimento = date.today() + timedelta(days=30)
        
        documento = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Contrato Completo",
            tipo_documento="contrato",
            status="assinado",
            origem="gerado",
            arquivo="contrato.txt",
            descricao="Contrato de prestação de serviços",
            template_usado="contrato_padrao",
            dados_preenchidos=dados_preenchidos,
            data_vencimento=data_vencimento,
            usuario_upload=self.user
        )
        
        self.assertEqual(documento.status, "assinado")
        self.assertEqual(documento.origem, "gerado")
        self.assertEqual(documento.template_usado, "contrato_padrao")
        self.assertEqual(documento.dados_preenchidos, dados_preenchidos)
        self.assertEqual(documento.data_vencimento, data_vencimento)
        self.assertEqual(documento.descricao, "Contrato de prestação de serviços")
    
    def test_documento_str_representation(self):
        """Testa representação string do documento."""
        documento = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Documento Teste",
            tipo_documento="contrato",
            arquivo="teste.txt",
            usuario_upload=self.user
        )
        
        expected = f"Documento Teste - {self.cliente.razao_social}"
        self.assertEqual(str(documento), expected)
    
    def test_documento_properties(self):
        """Testa propriedades do documento."""
        # Documento gerado automaticamente
        documento_gerado = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Contrato Gerado",
            tipo_documento="contrato",
            origem="gerado",
            arquivo="contrato.txt",
            usuario_upload=self.user
        )
        
        # Documento manual
        documento_manual = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Documento Manual",
            tipo_documento="certificado",
            origem="manual",
            arquivo="certificado.txt",
            usuario_upload=self.user
        )
        
        # Documento boleto
        documento_boleto = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Boleto",
            tipo_documento="boleto",
            arquivo="boleto.txt",
            usuario_upload=self.user
        )
        
        # Testa propriedades
        self.assertTrue(documento_gerado.is_gerado_automaticamente)
        self.assertFalse(documento_manual.is_gerado_automaticamente)
        
        self.assertTrue(documento_gerado.is_contrato)
        self.assertFalse(documento_manual.is_contrato)
        
        self.assertTrue(documento_boleto.is_boleto)
        self.assertFalse(documento_gerado.is_boleto)
    
    def test_documento_vencimento_property(self):
        """Testa propriedade de vencimento."""
        # Documento sem vencimento
        documento_sem_vencimento = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Sem Vencimento",
            tipo_documento="contrato",
            arquivo="contrato.txt",
            usuario_upload=self.user
        )
        
        # Documento com vencimento futuro
        data_futura = date.today() + timedelta(days=30)
        documento_futuro = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Vencimento Futuro",
            tipo_documento="boleto",
            data_vencimento=data_futura,
            arquivo="boleto.txt",
            usuario_upload=self.user
        )
        
        # Documento com vencimento passado
        data_passada = date.today() - timedelta(days=30)
        documento_passado = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Vencimento Passado",
            tipo_documento="boleto",
            data_vencimento=data_passada,
            arquivo="boleto.txt",
            usuario_upload=self.user
        )
        
        # Testa propriedades
        self.assertFalse(documento_sem_vencimento.is_vencido)
        self.assertFalse(documento_futuro.is_vencido)
        self.assertTrue(documento_passado.is_vencido)
    
    def test_documento_tamanho_arquivo_property(self):
        """Testa propriedade de tamanho do arquivo."""
        # Mock do tamanho do arquivo
        documento = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Documento Teste",
            tipo_documento="contrato",
            arquivo="teste.txt",
            usuario_upload=self.user
        )
        
        # Mock do método size do arquivo
        from unittest.mock import Mock
        mock_arquivo = Mock()
        mock_arquivo.size = 1024  # 1KB
        documento.arquivo = mock_arquivo
        
        # Testa formatação do tamanho
        tamanho_formatado = documento.tamanho_arquivo
        self.assertEqual(tamanho_formatado, "1.0 KB")
    
    def test_documento_choices_validation(self):
        """Testa validação de choices."""
        # Testa tipo_documento válido
        documento = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Documento Teste",
            tipo_documento="contrato",  # choice válido
            arquivo="teste.txt",
            usuario_upload=self.user
        )
        self.assertEqual(documento.tipo_documento, "contrato")
        
        # Testa status válido
        documento.status = "assinado"
        documento.save()
        self.assertEqual(documento.status, "assinado")
        
        # Testa origem válida
        documento.origem = "gerado"
        documento.save()
        self.assertEqual(documento.origem, "gerado")
    
    def test_documento_relationship_with_cliente(self):
        """Testa relacionamento com cliente."""
        documento = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Documento Teste",
            tipo_documento="contrato",
            arquivo="teste.txt",
            usuario_upload=self.user
        )
        
        # Testa relacionamento direto
        self.assertEqual(documento.cliente, self.cliente)
        
        # Testa relacionamento reverso
        documentos_do_cliente = self.cliente.documentos.all()
        self.assertIn(documento, documentos_do_cliente)
        self.assertEqual(documentos_do_cliente.count(), 1)
    
    def test_documento_relationship_with_user(self):
        """Testa relacionamento com usuário."""
        documento = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Documento Teste",
            tipo_documento="contrato",
            arquivo="teste.txt",
            usuario_upload=self.user
        )
        
        # Testa relacionamento direto
        self.assertEqual(documento.usuario_upload, self.user)
        
        # Testa que usuário pode ser None (SET_NULL)
        documento.usuario_upload = None
        documento.save()
        documento.refresh_from_db()
        self.assertIsNone(documento.usuario_upload)
    
    def test_documento_timestamps(self):
        """Testa timestamps automáticos."""
        documento = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Documento Teste",
            tipo_documento="contrato",
            arquivo="teste.txt",
            usuario_upload=self.user
        )
        
        # Verifica que data_upload foi definida automaticamente
        self.assertIsNotNone(documento.data_upload)
        self.assertAlmostEqual(
            timezone.now().timestamp(),
            documento.data_upload.timestamp(),
            delta=5  # 5 segundos de tolerância
        )
    
    def test_documento_meta_ordering(self):
        """Testa ordenação padrão por data_upload decrescente."""
        # Cria documentos em ordem
        doc1 = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Primeiro Documento",
            tipo_documento="contrato",
            arquivo="doc1.txt",
            usuario_upload=self.user
        )
        
        doc2 = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Segundo Documento",
            tipo_documento="boleto",
            arquivo="doc2.txt",
            usuario_upload=self.user
        )
        
        # Verifica ordenação (mais recente primeiro)
        documentos = DocumentoCliente.objects.all()
        self.assertEqual(documentos[0], doc2)  # Mais recente
        self.assertEqual(documentos[1], doc1)  # Mais antigo
    
    def test_documento_indexes(self):
        """Testa índices do banco de dados."""
        from django.db import connection
        
        # Obtém índices da tabela
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'clientes_documentocliente'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
        
        # Verifica se os índices esperados existem
        expected_indexes = [
            'clientes_do_cliente_5c54c9_idx',  # cliente, tipo_documento
            'clientes_do_data_up_065a04_idx',  # data_upload
            'clientes_do_status_fe238b_idx',   # status
            'clientes_do_origem_625b14_idx',   # origem
        ]
        
        for expected_index in expected_indexes:
            self.assertIn(expected_index, indexes)
    
    def test_documento_soft_delete(self):
        """Testa soft delete do documento."""
        documento = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Documento para Deletar",
            tipo_documento="contrato",
            arquivo="teste.txt",
            usuario_upload=self.user
        )
        
        # Verifica que está ativo
        self.assertTrue(documento.ativo)
        
        # Simula soft delete
        documento.ativo = False
        documento.save()
        
        # Verifica que foi marcado como inativo
        self.assertFalse(documento.ativo)
        
        # Verifica que não aparece na query padrão (ativo=True)
        documentos_ativos = DocumentoCliente.objects.filter(ativo=True)
        self.assertNotIn(documento, documentos_ativos)
    
    def test_documento_json_field_validation(self):
        """Testa validação do campo JSON dados_preenchidos."""
        # Dados válidos
        dados_validos = {
            "valor_servico": "1000.00",
            "data_inicio": "01/01/2024",
            "cliente_nome": "Empresa Teste"
        }
        
        documento = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Documento JSON",
            tipo_documento="contrato",
            dados_preenchidos=dados_validos,
            arquivo="teste.txt",
            usuario_upload=self.user
        )
        
        self.assertEqual(documento.dados_preenchidos, dados_validos)
        
        # Dados vazios (dict vazio é permitido)
        documento.dados_preenchidos = {}
        documento.save()
        self.assertEqual(documento.dados_preenchidos, {})
