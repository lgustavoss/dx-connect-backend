"""
Testes unitários para os serializers de DocumentoCliente.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from rest_framework.test import APIRequestFactory
from rest_framework import serializers

from clientes.models import Cliente, DocumentoCliente, GrupoEmpresa
from clientes.serializers import DocumentoClienteSerializer, DocumentoClienteListSerializer

User = get_user_model()


class DocumentoClienteSerializerTests(TestCase):
    """Testes para DocumentoClienteSerializer."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.factory = APIRequestFactory()
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
            arquivo="teste.txt",
            descricao="Descrição do documento",
            usuario_upload=self.user
        )
    
    def test_serializer_valid_data(self):
        """Testa serialização com dados válidos."""
        serializer = DocumentoClienteSerializer(self.documento)
        data = serializer.data
        
        # Verifica campos básicos
        self.assertEqual(data['id'], self.documento.id)
        self.assertEqual(data['cliente'], self.cliente.id)
        self.assertEqual(data['cliente_nome'], self.cliente.razao_social)
        self.assertEqual(data['nome'], "Documento Teste")
        self.assertEqual(data['tipo_documento'], "contrato")
        self.assertEqual(data['status'], "gerado")
        self.assertEqual(data['origem'], "manual")
        self.assertEqual(data['descricao'], "Descrição do documento")
        
        # Verifica campos relacionados
        self.assertEqual(data['usuario_upload'], self.user.id)
        self.assertEqual(data['usuario_upload_nome'], self.user.username)
        
        # Verifica propriedades calculadas
        # tamanho_arquivo pode ser None se arquivo não existir fisicamente
        self.assertEqual(data['is_gerado_automaticamente'], False)
        self.assertEqual(data['is_contrato'], True)
        self.assertEqual(data['is_boleto'], False)
        self.assertEqual(data['is_vencido'], False)
    
    def test_serializer_documento_gerado_automaticamente(self):
        """Testa serialização de documento gerado automaticamente."""
        dados_preenchidos = {
            "valor_servico": "1000.00",
            "data_inicio": "01/01/2024"
        }
        
        documento_gerado = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Contrato Gerado",
            tipo_documento="contrato",
            status="assinado",
            origem="gerado",
            template_usado="contrato_padrao",
            dados_preenchidos=dados_preenchidos,
            data_vencimento=date.today() + timedelta(days=30),
            arquivo="contrato.txt",
            usuario_upload=self.user
        )
        
        serializer = DocumentoClienteSerializer(documento_gerado)
        data = serializer.data
        
        self.assertEqual(data['status'], "assinado")
        self.assertEqual(data['origem'], "gerado")
        self.assertEqual(data['template_usado'], "contrato_padrao")
        self.assertEqual(data['dados_preenchidos'], dados_preenchidos)
        self.assertIsNotNone(data['data_vencimento'])
        self.assertEqual(data['is_gerado_automaticamente'], True)
    
    def test_serializer_validation_valid_data(self):
        """Testa validação com dados válidos."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Cria um arquivo temporário para o teste
        arquivo_teste = SimpleUploadedFile(
            "teste.txt",
            b"conteudo do arquivo de teste",
            content_type="text/plain"
        )
        
        data = {
            'cliente': self.cliente.id,
            'nome': 'Novo Documento',
            'tipo_documento': 'boleto',
            'status': 'gerado',
            'origem': 'manual',
            'descricao': 'Boleto de cobrança',
            'data_vencimento': (date.today() + timedelta(days=30)).isoformat(),
            'arquivo': arquivo_teste
        }
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = DocumentoClienteSerializer(
            data=data,
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid())
        
        documento = serializer.save()
        self.assertEqual(documento.cliente, self.cliente)
        self.assertEqual(documento.nome, 'Novo Documento')
        self.assertEqual(documento.tipo_documento, 'boleto')
        self.assertEqual(documento.usuario_upload, self.user)
    
    def test_serializer_validation_invalid_data_vencimento(self):
        """Testa validação com data de vencimento no passado."""
        data = {
            'cliente': self.cliente.id,
            'nome': 'Documento Inválido',
            'tipo_documento': 'boleto',
            'data_vencimento': (date.today() - timedelta(days=1)).isoformat()
        }
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = DocumentoClienteSerializer(
            data=data,
            context={'request': request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('data_vencimento', serializer.errors)
    
    def test_serializer_validation_invalid_dados_preenchidos(self):
        """Testa validação com dados_preenchidos inválidos."""
        data = {
            'cliente': self.cliente.id,
            'nome': 'Documento Inválido',
            'tipo_documento': 'contrato',
            'dados_preenchidos': "string_invalida"  # Deveria ser dict
        }
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = DocumentoClienteSerializer(
            data=data,
            context={'request': request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('dados_preenchidos', serializer.errors)
    
    def test_serializer_create_with_user_auto_assignment(self):
        """Testa criação automática de usuário no serializer."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Cria um arquivo temporário para o teste
        arquivo_teste = SimpleUploadedFile(
            "contrato.txt",
            b"conteudo do contrato de teste",
            content_type="text/plain"
        )
        
        data = {
            'cliente': self.cliente.id,
            'nome': 'Documento Auto User',
            'tipo_documento': 'contrato',
            'arquivo': arquivo_teste
        }
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = DocumentoClienteSerializer(
            data=data,
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid())
        
        documento = serializer.save()
        self.assertEqual(documento.usuario_upload, self.user)
    
    def test_serializer_update_existing_document(self):
        """Testa atualização de documento existente."""
        data = {
            'nome': 'Documento Atualizado',
            'descricao': 'Nova descrição',
            'status': 'assinado'
        }
        
        serializer = DocumentoClienteSerializer(
            self.documento,
            data=data,
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        
        documento_atualizado = serializer.save()
        self.assertEqual(documento_atualizado.nome, 'Documento Atualizado')
        self.assertEqual(documento_atualizado.descricao, 'Nova descrição')
        self.assertEqual(documento_atualizado.status, 'assinado')
    
    def test_serializer_read_only_fields(self):
        """Testa que campos read-only não podem ser alterados."""
        data = {
            'id': 999,  # Campo read-only
            'data_upload': '2023-01-01T00:00:00Z',  # Campo read-only
            'is_contrato': False,  # Campo read-only
            'nome': 'Documento Teste'
        }
        
        serializer = DocumentoClienteSerializer(
            self.documento,
            data=data,
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        documento_atualizado = serializer.save()
        
        # Verifica que campos read-only não foram alterados
        self.assertEqual(documento_atualizado.id, self.documento.id)
        self.assertEqual(documento_atualizado.data_upload, self.documento.data_upload)
        self.assertTrue(documento_atualizado.is_contrato)  # Deve permanecer True
    
    def test_serializer_choices_validation(self):
        """Testa validação de choices."""
        # Tipo de documento inválido
        data = {
            'cliente': self.cliente.id,
            'nome': 'Documento Inválido',
            'tipo_documento': 'tipo_inexistente'
        }
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = DocumentoClienteSerializer(
            data=data,
            context={'request': request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('tipo_documento', serializer.errors)
        
        # Status inválido
        data = {
            'cliente': self.cliente.id,
            'nome': 'Documento Inválido',
            'tipo_documento': 'contrato',
            'status': 'status_inexistente'
        }
        
        serializer = DocumentoClienteSerializer(
            data=data,
            context={'request': request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)
    
    def test_serializer_required_fields(self):
        """Testa campos obrigatórios."""
        # Cliente é obrigatório
        data = {
            'nome': 'Documento sem Cliente',
            'tipo_documento': 'contrato'
        }
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = DocumentoClienteSerializer(
            data=data,
            context={'request': request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('cliente', serializer.errors)
        
        # Nome é obrigatório
        data = {
            'cliente': self.cliente.id,
            'tipo_documento': 'contrato'
        }
        
        serializer = DocumentoClienteSerializer(
            data=data,
            context={'request': request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('nome', serializer.errors)


class DocumentoClienteListSerializerTests(TestCase):
    """Testes para DocumentoClienteListSerializer."""
    
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
        
        self.documento = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Documento Lista",
            tipo_documento="contrato",
            status="gerado",
            origem="manual",
            data_vencimento=date.today() + timedelta(days=30),
            arquivo="teste.txt",
            usuario_upload=self.user
        )
    
    def test_list_serializer_fields(self):
        """Testa campos do serializer de listagem."""
        serializer = DocumentoClienteListSerializer(self.documento)
        data = serializer.data
        
        # Verifica campos incluídos
        expected_fields = [
            'id', 'cliente', 'cliente_nome', 'nome', 'tipo_documento',
            'status', 'origem', 'data_vencimento', 'data_upload', 'ativo'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
        
        # Verifica campos não incluídos (campos detalhados)
        excluded_fields = [
            'descricao', 'template_usado', 'dados_preenchidos',
            'usuario_upload', 'usuario_upload_nome', 'tamanho_arquivo',
            'is_gerado_automaticamente', 'is_contrato', 'is_boleto', 'is_vencido'
        ]
        
        for field in excluded_fields:
            self.assertNotIn(field, data)
    
    def test_list_serializer_cliente_nome(self):
        """Testa campo cliente_nome no serializer de listagem."""
        serializer = DocumentoClienteListSerializer(self.documento)
        data = serializer.data
        
        self.assertEqual(data['cliente_nome'], self.cliente.razao_social)
        self.assertEqual(data['cliente'], self.cliente.id)
    
    def test_list_serializer_data_types(self):
        """Testa tipos de dados no serializer de listagem."""
        serializer = DocumentoClienteListSerializer(self.documento)
        data = serializer.data
        
        # Verifica tipos
        self.assertIsInstance(data['id'], int)
        self.assertIsInstance(data['cliente'], int)
        self.assertIsInstance(data['cliente_nome'], str)
        self.assertIsInstance(data['nome'], str)
        self.assertIsInstance(data['tipo_documento'], str)
        self.assertIsInstance(data['status'], str)
        self.assertIsInstance(data['origem'], str)
        self.assertIsInstance(data['ativo'], bool)
        
        # Verifica data_vencimento (pode ser None)
        if data['data_vencimento'] is not None:
            self.assertIsInstance(data['data_vencimento'], str)
    
    def test_list_serializer_multiple_documents(self):
        """Testa serialização de múltiplos documentos."""
        # Cria mais documentos
        doc2 = DocumentoCliente.objects.create(
            cliente=self.cliente,
            nome="Segundo Documento",
            tipo_documento="boleto",
            status="enviado",
            origem="gerado",
            arquivo="boleto.txt",
            usuario_upload=self.user
        )
        
        # Serializa lista
        documentos = DocumentoCliente.objects.all()
        serializer = DocumentoClienteListSerializer(documentos, many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 2)
        
        # Verifica que ambos estão na lista
        nomes = [doc['nome'] for doc in data]
        self.assertIn("Documento Lista", nomes)
        self.assertIn("Segundo Documento", nomes)
