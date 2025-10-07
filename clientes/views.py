from rest_framework import viewsets, status, filters, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Cliente, ContatoCliente, GrupoEmpresa, DocumentoCliente
from .serializers import (
    ClienteSerializer,
    ClienteListSerializer,
    ContatoClienteSerializer,
    DadosCapturadosChatSerializer,
    CadastroManualContatoSerializer,
    BuscaContatoSerializer,
    GrupoEmpresaSerializer,
    DocumentoClienteSerializer,
    DocumentoClienteListSerializer
)
from .filters import ClienteFilter, ContatoClienteFilter, DocumentoClienteFilter


class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar clientes.
    
    Endpoints disponíveis:
    - GET /api/v1/clientes/ - Listar clientes
    - POST /api/v1/clientes/ - Criar cliente
    - GET /api/v1/clientes/{id}/ - Detalhar cliente
    - PUT /api/v1/clientes/{id}/ - Atualizar cliente (completo)
    - PATCH /api/v1/clientes/{id}/ - Atualizar cliente (parcial)
    - DELETE /api/v1/clientes/{id}/ - Deletar cliente
    - GET /api/v1/clientes/search/ - Buscar clientes
    - GET /api/v1/clientes/status/{status}/ - Listar por status
    """
    
    queryset = Cliente.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ClienteFilter
    search_fields = ['razao_social', 'nome_fantasia', 'cnpj', 'email_principal']
    ordering_fields = ['razao_social', 'criado_em', 'atualizado_em', 'status']
    ordering = ['-criado_em']
    
    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na ação"""
        if self.action == 'list':
            return ClienteListSerializer
        return ClienteSerializer
    
    def get_queryset(self):
        """Filtra queryset baseado no usuário autenticado"""
        queryset = super().get_queryset()
        
        # Se o usuário não for superuser, pode ver apenas clientes criados por ele
        if not self.request.user.is_superuser:
            queryset = queryset.filter(criado_por=self.request.user)
        
        return queryset
    
    def perform_create(self, serializer):
        """Define o usuário criador ao criar cliente"""
        serializer.save(criado_por=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """Lista clientes com filtros e paginação"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Aplicar paginação se configurada
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Detalha um cliente específico"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Cria um novo cliente"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def update(self, request, *args, **kwargs):
        """Atualiza um cliente completamente"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """Atualiza um cliente parcialmente"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Deleta um cliente"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """
        Busca avançada de clientes.
        
        Query parameters:
        - q: termo de busca (nome, documento, email)
        - status: filtrar por status
        - tipo_documento: filtrar por tipo de documento
        - cidade: filtrar por cidade
        - estado: filtrar por estado
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Busca por termo
        search_term = request.query_params.get('q', '')
        if search_term:
            queryset = queryset.filter(
                Q(nome__icontains=search_term) |
                Q(nome_fantasia__icontains=search_term) |
                Q(documento__icontains=search_term) |
                Q(email__icontains=search_term)
            )
        
        # Aplicar paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='status/(?P<status_param>[^/.]+)')
    def list_by_status(self, request, status_param=None):
        """
        Lista clientes por status específico.
        
        URL: /api/v1/clientes/status/{status}/
        """
        if status_param not in [choice[0] for choice in Cliente.STATUS_CHOICES]:
            return Response(
                {'error': f'Status inválido. Opções: {[choice[0] for choice in Cliente.STATUS_CHOICES]}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.filter_queryset(self.get_queryset().filter(status=status_param))
        
        # Aplicar paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """
        Atualiza apenas o status de um cliente.
        
        URL: /api/v1/clientes/{id}/status/
        Body: {"status": "ativo"}
        """
        instance = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'Campo "status" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in [choice[0] for choice in Cliente.STATUS_CHOICES]:
            return Response(
                {'error': f'Status inválido. Opções: {[choice[0] for choice in Cliente.STATUS_CHOICES]}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.status = new_status
        instance.save(update_fields=['status', 'atualizado_em'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        Retorna estatísticas dos clientes.
        
        URL: /api/v1/clientes/stats/
        """
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'por_status': {},
            'por_tipo_documento': {},
            'por_cidade': {},
            'por_estado': {},
            'recentes': queryset.filter(
                criado_em__gte=timezone.now() - timezone.timedelta(days=30)
            ).count(),
        }
        
        # Contagem por status
        for status_choice in Cliente.STATUS_CHOICES:
            count = queryset.filter(status=status_choice[0]).count()
            stats['por_status'][status_choice[0]] = count
        
        # Contagem por tipo de documento
        for tipo_choice in Cliente.TIPO_DOCUMENTO_CHOICES:
            count = queryset.filter(tipo_documento=tipo_choice[0]).count()
            stats['por_tipo_documento'][tipo_choice[0]] = count
        
        # Top 10 cidades
        from django.db.models import Count
        cidades = queryset.values('cidade').annotate(
            count=Count('cidade')
        ).filter(cidade__isnull=False).order_by('-count')[:10]
        
        stats['por_cidade'] = {item['cidade']: item['count'] for item in cidades}
        
        # Top 10 estados
        estados = queryset.values('estado').annotate(
            count=Count('estado')
        ).filter(estado__isnull=False).order_by('-count')[:10]
        
        stats['por_estado'] = {item['estado']: item['count'] for item in estados}
        
        return Response(stats)


class ContatoClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar contatos das empresas.
    """
    
    queryset = ContatoCliente.objects.all()
    serializer_class = ContatoClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ContatoClienteFilter
    search_fields = ['nome', 'whatsapp', 'email', 'cliente__razao_social']
    ordering_fields = ['nome', 'criado_em', 'ativo']
    ordering = ['nome']
    
    def get_queryset(self):
        """Filtra contatos baseado no usuário autenticado"""
        queryset = super().get_queryset()
        
        # Filtrar apenas contatos ativos
        queryset = queryset.filter(ativo=True)
        
        # Se o usuário não for superuser, pode filtrar por empresa
        if not self.request.user.is_superuser:
            # Mostra contatos de empresas onde o usuário tem acesso
            queryset = queryset.filter(cliente__status='ativo')
        
        return queryset
    
    def destroy(self, request, *args, **kwargs):
        """Implementa soft delete marcando contato como inativo"""
        instance = self.get_object()
        instance.ativo = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChatIntegrationView(viewsets.GenericViewSet):
    """
    View para integração com chat.
    
    Gerencia busca de contatos e pré-cadastro de dados capturados.
    """
    
    permission_classes = [AllowAny]  # Acesso público para chat
    
    @action(detail=False, methods=['post'], url_path='buscar-contato')
    def buscar_contato(self, request):
        """
        Busca contato por WhatsApp.
        
        POST /api/v1/clientes/chat/buscar-contato/
        """
        serializer = BuscaContatoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        whatsapp = serializer.validated_data['whatsapp']
        contatos = ContatoCliente.objects.filter(
            whatsapp=whatsapp,
            ativo=True
        ).select_related('cliente')
        
        if contatos.exists():
            serializer_contatos = ContatoClienteSerializer(contatos, many=True)
            return Response({
                'encontrado': True,
                'contatos': serializer_contatos.data
            })
        else:
            return Response({
                'encontrado': False,
                'message': 'WhatsApp não encontrado. Dados capturados disponíveis para cadastro.'
            })
    
    @action(detail=False, methods=['post'], url_path='dados-capturados')
    def dados_capturados(self, request):
        """
        Recebe dados capturados do chat para pré-cadastro.
        
        POST /api/v1/clientes/chat/dados-capturados/
        """
        serializer = DadosCapturadosChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Retorna os dados capturados para o atendente editar
        return Response({
            'message': 'Dados capturados recebidos',
            'dados_capturados': serializer.validated_data,
            'proximo_passo': 'Atendente deve editar e salvar os dados'
        })


class CadastroManualView(APIView):
    """
    View para cadastro manual de contatos pelo atendente.
    """
    
    permission_classes = [IsAuthenticated]  # Apenas atendentes autenticados
    
    def post(self, request):
        """
        Cadastra contato manualmente pelo atendente.
        
        POST /api/v1/clientes/cadastro-manual/
        """
        serializer = CadastroManualContatoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verificar se o WhatsApp já está cadastrado
        whatsapp = serializer.validated_data['whatsapp']
        contato_existente = ContatoCliente.objects.filter(
            whatsapp=whatsapp,
            ativo=True
        ).first()
        
        if contato_existente:
            return Response({
                'message': 'WhatsApp já cadastrado',
                'contato': ContatoClienteSerializer(contato_existente).data
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Criar contato e empresa
        contato = serializer.save()
        
        return Response({
            'message': 'Contato cadastrado com sucesso',
            'contato': ContatoClienteSerializer(contato).data
        }, status=status.HTTP_201_CREATED)


class GrupoEmpresaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar grupos de empresas.
    """
    
    queryset = GrupoEmpresa.objects.all()
    serializer_class = GrupoEmpresaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'descricao']
    ordering_fields = ['nome', 'criado_em']
    ordering = ['nome']


class DocumentoClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar documentos de clientes.
    
    Endpoints disponíveis:
    - GET /api/v1/documentos/ - Listar documentos
    - POST /api/v1/documentos/ - Criar documento
    - GET /api/v1/documentos/{id}/ - Detalhar documento
    - PUT /api/v1/documentos/{id}/ - Atualizar documento
    - PATCH /api/v1/documentos/{id}/ - Atualizar parcialmente documento
    - DELETE /api/v1/documentos/{id}/ - Remover documento (soft delete)
    - POST /api/v1/documentos/gerar-contrato/ - Gerar contrato automaticamente
    - POST /api/v1/documentos/gerar-boleto/ - Gerar boleto automaticamente
    """
    
    queryset = DocumentoCliente.objects.filter(ativo=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DocumentoClienteFilter
    search_fields = ['nome', 'descricao', 'template_usado']
    ordering_fields = ['nome', 'data_upload', 'data_vencimento', 'status']
    ordering = ['-data_upload']
    
    def get_serializer_class(self):
        """Retorna serializer apropriado baseado na ação"""
        if self.action == 'list':
            return DocumentoClienteListSerializer
        return DocumentoClienteSerializer
    
    def get_queryset(self):
        """Filtra documentos por usuário (não superuser vê apenas os próprios)"""
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            # Filtrar apenas documentos de clientes criados pelo usuário atual
            queryset = queryset.filter(cliente__criado_por=self.request.user)
        return queryset
    
    def perform_create(self, serializer):
        """Define o usuário que fez o upload"""
        serializer.save(usuario_upload=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """Implementa soft delete marcando documento como inativo"""
        instance = self.get_object()
        instance.ativo = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'], url_path='gerar-contrato')
    def gerar_contrato(self, request):
        """
        Gera um contrato automaticamente usando template.
        
        POST /api/v1/documentos/gerar-contrato/
        """
        from core.models import Config
        from core.defaults import DEFAULT_DOCUMENT_TEMPLATES
        
        # Dados obrigatórios
        cliente_id = request.data.get('cliente_id')
        template_nome = request.data.get('template_nome', 'contrato_padrao')
        dados_contrato = request.data.get('dados_contrato', {})
        
        if not cliente_id:
            return Response({
                'error': 'cliente_id é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cliente = get_object_or_404(Cliente, id=cliente_id, ativo=True)
        except:
            return Response({
                'error': 'Cliente não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Buscar configurações e templates
        try:
            config = Config.objects.first()
            if config and config.document_templates:
                templates = config.document_templates
            else:
                templates = DEFAULT_DOCUMENT_TEMPLATES
            
            template = templates.get(template_nome)
            if not template:
                return Response({
                    'error': f'Template "{template_nome}" não encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'error': f'Erro ao buscar templates: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Gerar documento
        try:
            documento = self._gerar_documento_automatico(
                cliente=cliente,
                template=template,
                tipo='contrato',
                dados_extra=dados_contrato,
                usuario=request.user
            )
            
            serializer = DocumentoClienteSerializer(documento)
            return Response({
                'message': 'Contrato gerado com sucesso',
                'documento': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Erro ao gerar contrato: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='gerar-boleto')
    def gerar_boleto(self, request):
        """
        Gera um boleto automaticamente usando template.
        
        POST /api/v1/documentos/gerar-boleto/
        """
        from core.models import Config
        from core.defaults import DEFAULT_DOCUMENT_TEMPLATES
        
        # Dados obrigatórios
        cliente_id = request.data.get('cliente_id')
        template_nome = request.data.get('template_nome', 'boleto_padrao')
        dados_boleto = request.data.get('dados_boleto', {})
        
        if not cliente_id:
            return Response({
                'error': 'cliente_id é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cliente = get_object_or_404(Cliente, id=cliente_id, ativo=True)
        except:
            return Response({
                'error': 'Cliente não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Buscar configurações e templates
        try:
            config = Config.objects.first()
            if config and config.document_templates:
                templates = config.document_templates
            else:
                templates = DEFAULT_DOCUMENT_TEMPLATES
            
            template = templates.get(template_nome)
            if not template:
                return Response({
                    'error': f'Template "{template_nome}" não encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'error': f'Erro ao buscar templates: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Gerar documento
        try:
            documento = self._gerar_documento_automatico(
                cliente=cliente,
                template=template,
                tipo='boleto',
                dados_extra=dados_boleto,
                usuario=request.user
            )
            
            serializer = DocumentoClienteSerializer(documento)
            return Response({
                'message': 'Boleto gerado com sucesso',
                'documento': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Erro ao gerar boleto: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _gerar_documento_automatico(self, cliente, template, tipo, dados_extra, usuario):
        """
        Método auxiliar para gerar documentos automaticamente.
        """
        from core.models import Config
        from django.utils import timezone
        import os
        import tempfile
        
        # Buscar dados da empresa (contratada)
        config = Config.objects.first()
        empresa_data = config.company_data if config else {}
        
        # Preparar dados para preenchimento
        dados_preenchimento = {
            # Dados do cliente (contratante)
            'cliente_nome': cliente.razao_social,
            'cliente_cnpj': cliente.cnpj,
            'cliente_endereco': cliente.endereco_completo,
            'cliente_email': cliente.email_principal,
            'cliente_telefone': cliente.telefone_principal,
            
            # Dados da empresa (contratada)
            'empresa_nome': empresa_data.get('razao_social', 'Empresa'),
            'empresa_cnpj': empresa_data.get('cnpj', ''),
            'empresa_endereco': f"{empresa_data.get('endereco', {}).get('logradouro', '')}, {empresa_data.get('endereco', {}).get('numero', '')} - {empresa_data.get('endereco', {}).get('bairro', '')}",
            
            # Dados extras fornecidos
            **dados_extra,
            
            # Dados do sistema
            'data_contrato': timezone.now().strftime('%d/%m/%Y'),
            'data_geracao': timezone.now().strftime('%d/%m/%Y %H:%M'),
        }
        
        # Preencher template
        conteudo_preenchido = template['conteudo']
        for variavel, valor in dados_preenchimento.items():
            conteudo_preenchido = conteudo_preenchido.replace(f'{{{{{variavel}}}}}', str(valor))
        
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(conteudo_preenchido)
            arquivo_temp = f.name
        
        # Criar documento no banco
        documento = DocumentoCliente.objects.create(
            cliente=cliente,
            nome=f"{template['nome']} - {cliente.razao_social}",
            tipo_documento=tipo,
            status='gerado',
            origem='gerado',
            template_usado=template['nome'],
            dados_preenchidos=dados_preenchimento,
            data_vencimento=dados_extra.get('data_vencimento'),
            usuario_upload=usuario,
            arquivo=arquivo_temp
        )
        
        # Limpar arquivo temporário
        try:
            os.unlink(arquivo_temp)
        except:
            pass
        
        return documento