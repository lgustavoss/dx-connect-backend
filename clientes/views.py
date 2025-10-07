from rest_framework import viewsets, status, filters, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Cliente, ContatoCliente, GrupoEmpresa
from .serializers import (
    ClienteSerializer,
    ClienteListSerializer,
    ContatoClienteSerializer,
    DadosCapturadosChatSerializer,
    CadastroManualContatoSerializer,
    BuscaContatoSerializer,
    GrupoEmpresaSerializer
)
from .filters import ClienteFilter, ContatoClienteFilter


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