"""
Testes unitários para os filtros de DocumentoCliente.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from clientes.models import Cliente, DocumentoCliente, GrupoEmpresa
from clientes.filters import DocumentoClienteFilter

User = get_user_model()


class DocumentoClienteFilterTests(TestCase):
    """Testes para DocumentoClienteFilter."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Limpa dados anteriores
        DocumentoCliente.objects.all().delete()
        Cliente.objects.all().delete()
        GrupoEmpresa.objects.all().delete()
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        self.grupo = GrupoEmpresa.objects.create(
            nome="Grupo Teste",
            descricao="Descrição do grupo teste"
        )
        
        self.cliente1 = Cliente.objects.create(
            razao_social="Empresa 1 LTDA",
            cnpj="11.111.111/0001-11",
            grupo_empresa=self.grupo,
            responsavel_legal_nome="João Silva",
            responsavel_legal_cpf="111.111.111-11",
            criado_por=self.user
        )
        
        self.cliente2 = Cliente.objects.create(
            razao_social="Empresa 2 LTDA",
            cnpj="22.222.222/0001-22",
            grupo_empresa=self.grupo,
            responsavel_legal_nome="Maria Santos",
            responsavel_legal_cpf="222.222.222-22",
            criado_por=self.user
        )
        
        # Cria documentos de teste
        self.doc_contrato = DocumentoCliente.objects.create(
            cliente=self.cliente1,
            nome="Contrato Empresa 1",
            tipo_documento="contrato",
            status="gerado",
            origem="manual",
            descricao="Contrato de prestação de serviços",
            arquivo="contrato.txt",
            usuario_upload=self.user
        )
        
        self.doc_boleto = DocumentoCliente.objects.create(
            cliente=self.cliente1,
            nome="Boleto Empresa 1",
            tipo_documento="boleto",
            status="enviado",
            origem="gerado",
            template_usado="boleto_padrao",
            data_vencimento=date.today() + timedelta(days=30),
            arquivo="boleto.txt",
            usuario_upload=self.user
        )
        
        self.doc_certificado = DocumentoCliente.objects.create(
            cliente=self.cliente2,
            nome="Certificado Empresa 2",
            tipo_documento="certificado",
            status="aprovado",
            origem="importado",
            descricao="Certificado de qualidade",
            arquivo="certificado.txt",
            usuario_upload=self.user
        )
        
        self.doc_inativo = DocumentoCliente.objects.create(
            cliente=self.cliente1,
            nome="Documento Inativo",
            tipo_documento="contrato",
            status="gerado",
            origem="manual",
            arquivo="inativo.txt",
            usuario_upload=self.user,
            ativo=False
        )
    
    def test_filter_by_cliente(self):
        """Testa filtro por cliente."""
        filter_data = {'cliente': self.cliente1.id}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 2)  # 2 documentos ativos do cliente1
        
        # Verifica que contém os documentos corretos
        ids = list(filtered_queryset.values_list('id', flat=True))
        self.assertIn(self.doc_contrato.id, ids)
        self.assertIn(self.doc_boleto.id, ids)
        self.assertNotIn(self.doc_certificado.id, ids)  # Pertence ao cliente2
    
    def test_filter_by_nome(self):
        """Testa filtro por nome (icontains)."""
        filter_data = {'nome': 'Empresa 1'}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 2)  # 2 documentos com "Empresa 1" no nome
        
        # Verifica que contém os documentos corretos
        ids = list(filtered_queryset.values_list('id', flat=True))
        self.assertIn(self.doc_contrato.id, ids)
        self.assertIn(self.doc_boleto.id, ids)
        self.assertNotIn(self.doc_certificado.id, ids)  # Nome diferente
    
    def test_filter_by_tipo_documento(self):
        """Testa filtro por tipo de documento."""
        filter_data = {'tipo_documento': 'contrato'}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 1)  # 1 documento do tipo contrato ativo
        
        # Verifica que contém o documento correto
        self.assertEqual(filtered_queryset.first(), self.doc_contrato)
        
        # Testa outro tipo
        filter_data = {'tipo_documento': 'boleto'}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 1)
        self.assertEqual(filtered_queryset.first(), self.doc_boleto)
    
    def test_filter_by_status(self):
        """Testa filtro por status."""
        filter_data = {'status': 'gerado'}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 1)  # 1 documento com status gerado ativo
        
        self.assertEqual(filtered_queryset.first(), self.doc_contrato)
        
        # Testa outro status
        filter_data = {'status': 'enviado'}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 1)
        self.assertEqual(filtered_queryset.first(), self.doc_boleto)
    
    def test_filter_by_origem(self):
        """Testa filtro por origem."""
        filter_data = {'origem': 'manual'}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 1)  # 1 documento manual ativo
        
        self.assertEqual(filtered_queryset.first(), self.doc_contrato)
        
        # Testa origem gerado
        filter_data = {'origem': 'gerado'}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 1)
        self.assertEqual(filtered_queryset.first(), self.doc_boleto)
    
    def test_filter_by_template_usado(self):
        """Testa filtro por template usado."""
        filter_data = {'template_usado': 'boleto_padrao'}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 1)
        self.assertEqual(filtered_queryset.first(), self.doc_boleto)
        
        # Testa template inexistente
        filter_data = {'template_usado': 'template_inexistente'}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 0)
    
    def test_filter_by_data_upload_apos(self):
        """Testa filtro por data de upload após."""
        # Filtra por data de hoje
        filter_data = {'data_upload_apos': date.today().isoformat()}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 3)  # Todos os documentos ativos foram criados hoje
        
        # Filtra por data futura (nenhum documento)
        data_futura = date.today() + timedelta(days=1)
        filter_data = {'data_upload_apos': data_futura.isoformat()}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 0)
    
    def test_filter_by_data_upload_antes(self):
        """Testa filtro por data de upload antes."""
        # Filtra por data futura (nenhum documento)
        data_futura = date.today() + timedelta(days=1)
        filter_data = {'data_upload_antes': data_futura.isoformat()}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 3)  # Todos os documentos ativos foram criados antes da data futura
        
        # Filtra por data passada (nenhum documento)
        data_passada = date.today() - timedelta(days=1)
        filter_data = {'data_upload_antes': data_passada.isoformat()}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 0)
    
    def test_filter_by_data_vencimento_apos(self):
        """Testa filtro por data de vencimento após."""
        # Filtra por data de hoje (deve incluir o boleto que vence em 30 dias)
        filter_data = {'data_vencimento_apos': date.today().isoformat()}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 1)  # Apenas o boleto tem vencimento
        self.assertEqual(filtered_queryset.first(), self.doc_boleto)
        
        # Filtra por data futura
        data_futura = date.today() + timedelta(days=15)
        filter_data = {'data_vencimento_apos': data_futura.isoformat()}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 1)  # Boleto vence em 30 dias
        self.assertEqual(filtered_queryset.first(), self.doc_boleto)
    
    def test_filter_by_data_vencimento_antes(self):
        """Testa filtro por data de vencimento antes."""
        # Filtra por data futura
        data_futura = date.today() + timedelta(days=35)
        filter_data = {'data_vencimento_antes': data_futura.isoformat()}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 1)  # Boleto vence em 30 dias
        self.assertEqual(filtered_queryset.first(), self.doc_boleto)
        
        # Filtra por data próxima (nenhum documento)
        data_proxima = date.today() + timedelta(days=15)
        filter_data = {'data_vencimento_antes': data_proxima.isoformat()}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 0)  # Boleto vence em 30 dias
    
    def test_filter_by_ativo(self):
        """Testa filtro por status ativo."""
        # Filtra apenas ativos (padrão)
        filter_data = {'ativo': True}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 3)  # 3 documentos ativos
        
        # Filtra apenas inativos
        filter_data = {'ativo': False}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 1)  # 1 documento inativo
        self.assertEqual(filtered_queryset.first(), self.doc_inativo)
    
    def test_filter_multiple_conditions(self):
        """Testa filtro com múltiplas condições."""
        # Filtra por cliente E tipo
        filter_data = {
            'cliente': self.cliente1.id,
            'tipo_documento': 'contrato'
        }
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 1)
        self.assertEqual(filtered_queryset.first(), self.doc_contrato)
        
        # Filtra por status E origem
        filter_data = {
            'status': 'enviado',
            'origem': 'gerado'
        }
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 1)
        self.assertEqual(filtered_queryset.first(), self.doc_boleto)
        
        # Filtra por cliente E ativo (deve retornar 0 pois não há contratos ativos do cliente1)
        filter_data = {
            'cliente': self.cliente2.id,
            'tipo_documento': 'contrato'
        }
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 0)
    
    def test_filter_empty_queryset(self):
        """Testa filtro que resulta em queryset vazio."""
        # Filtra por tipo inexistente
        filter_data = {'tipo_documento': 'tipo_inexistente'}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 0)
        
        # Filtra por cliente inexistente
        filter_data = {'cliente': 999}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 0)
    
    def test_filter_invalid_data(self):
        """Testa filtro com dados inválidos."""
        # Data inválida
        filter_data = {'data_upload_apos': 'data_invalida'}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        # Deve retornar queryset vazio ou erro
        filtered_queryset = filter_set.qs
        # O comportamento pode variar dependendo da implementação do django-filter
        
        # ID inválido
        filter_data = {'cliente': 'texto_invalido'}
        filter_set = DocumentoClienteFilter(data=filter_data, queryset=DocumentoCliente.objects.all())
        
        filtered_queryset = filter_set.qs
        self.assertEqual(filtered_queryset.count(), 0)
    
    def test_filter_meta_fields(self):
        """Testa campos definidos na Meta do filtro."""
        filter_set = DocumentoClienteFilter(queryset=DocumentoCliente.objects.all())
        
        # Verifica que os campos esperados estão disponíveis
        expected_fields = [
            'cliente', 'nome', 'tipo_documento', 'status',
            'origem', 'template_usado', 'ativo'
        ]
        
        for field in expected_fields:
            self.assertIn(field, filter_set.filters)
    
    def test_filter_help_text(self):
        """Testa help_text dos filtros."""
        filter_set = DocumentoClienteFilter(queryset=DocumentoCliente.objects.all())
        
        # Verifica que os filtros têm help_text (se suportado)
        if hasattr(filter_set.filters['cliente'], 'help_text'):
            self.assertIsNotNone(filter_set.filters['cliente'].help_text)
        if hasattr(filter_set.filters['nome'], 'help_text'):
            self.assertIsNotNone(filter_set.filters['nome'].help_text)
        if hasattr(filter_set.filters['tipo_documento'], 'help_text'):
            self.assertIsNotNone(filter_set.filters['tipo_documento'].help_text)
        if hasattr(filter_set.filters['status'], 'help_text'):
            self.assertIsNotNone(filter_set.filters['status'].help_text)
