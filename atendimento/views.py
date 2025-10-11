"""
Views para sistema de filas de atendimento (Issue #37).
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Departamento, FilaAtendimento, Atendimento
from .serializers import (
    DepartamentoSerializer,
    FilaAtendimentoSerializer,
    AtendimentoSerializer,
    AtendimentoListSerializer
)
from .service import get_distribuicao_service


class DepartamentoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de departamentos"""
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['ativo']
    search_fields = ['nome', 'descricao']
    ordering = ['nome']


class FilaAtendimentoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de filas"""
    queryset = FilaAtendimento.objects.select_related('departamento', 'cliente')
    serializer_class = FilaAtendimentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['departamento', 'prioridade']
    ordering_fields = ['entrou_na_fila_em', 'prioridade']
    ordering = ['-prioridade', 'entrou_na_fila_em']
    
    @action(detail=False, methods=['post'], url_path='distribuir')
    def distribuir(self, request):
        """Força distribuição automática de uma fila"""
        departamento_id = request.data.get('departamento_id')
        
        if not departamento_id:
            return Response(
                {'error': 'departamento_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = get_distribuicao_service()
        distribuidos = service.distribuir_automaticamente(departamento_id)
        
        return Response({
            'message': f'{distribuidos} atendimentos distribuídos',
            'distribuidos': distribuidos
        }, status=status.HTTP_200_OK)


class AtendimentoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de atendimentos"""
    queryset = Atendimento.objects.select_related('departamento', 'cliente', 'atendente')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'departamento', 'atendente', 'prioridade']
    search_fields = ['cliente__razao_social', 'numero_whatsapp', 'observacoes']
    ordering_fields = ['criado_em', 'iniciado_em', 'finalizado_em']
    ordering = ['-criado_em']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AtendimentoListSerializer
        return AtendimentoSerializer
    
    def get_queryset(self):
        """Filtra atendimentos do usuário ou todos se admin"""
        queryset = super().get_queryset()
        
        if not self.request.user.is_superuser:
            # Atendente vê apenas seus atendimentos
            queryset = queryset.filter(atendente=self.request.user)
        
        return queryset
    
    @action(detail=False, methods=['get'], url_path='meus-atendimentos')
    def meus_atendimentos(self, request):
        """Lista atendimentos ativos do atendente logado"""
        atendimentos = Atendimento.objects.filter(
            atendente=request.user,
            status__in=['aguardando', 'em_atendimento', 'pausado']
        )
        
        serializer = self.get_serializer(atendimentos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='finalizar')
    def finalizar(self, request, pk=None):
        """Finaliza atendimento"""
        atendimento = self.get_object()
        observacoes = request.data.get('observacoes', '')
        
        atendimento.finalizar(observacoes)
        
        return Response({
            'message': 'Atendimento finalizado',
            'atendimento_id': atendimento.id
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='avaliar')
    def avaliar(self, request, pk=None):
        """Adiciona avaliação ao atendimento"""
        atendimento = self.get_object()
        
        avaliacao = request.data.get('avaliacao')
        comentario = request.data.get('comentario', '')
        
        if not avaliacao or avaliacao not in [1, 2, 3, 4, 5]:
            return Response(
                {'error': 'Avaliação deve ser de 1 a 5'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        atendimento.avaliacao = avaliacao
        atendimento.comentario_avaliacao = comentario
        atendimento.save(update_fields=['avaliacao', 'comentario_avaliacao'])
        
        return Response({
            'message': 'Avaliação registrada',
            'avaliacao': avaliacao
        }, status=status.HTTP_200_OK)

