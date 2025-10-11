"""
Views para sistema de filas de atendimento (Issue #37).
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Departamento, FilaAtendimento, Atendimento, TransferenciaAtendimento
from .serializers import (
    DepartamentoSerializer,
    FilaAtendimentoSerializer,
    AtendimentoSerializer,
    AtendimentoListSerializer,
    TransferenciaAtendimentoSerializer,
    TransferirAtendimentoSerializer
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
    
    @action(detail=True, methods=['post'], url_path='transferir')
    def transferir(self, request, pk=None):
        """
        Transfere atendimento para outro atendente (Issue #38).
        
        Valida permissões, cria registro de auditoria e notifica via WebSocket.
        """
        import logging
        from django.contrib.auth import get_user_model
        from django.db import transaction
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        logger = logging.getLogger(__name__)
        User = get_user_model()
        
        atendimento = self.get_object()
        serializer = TransferirAtendimentoSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        atendente_destino_id = data['atendente_destino_id']
        motivo = data['motivo']
        departamento_destino_id = data.get('departamento_destino_id')
        
        # Validações
        if atendimento.status not in ['aguardando', 'em_atendimento', 'pausado']:
            return Response(
                {'error': 'Atendimento não pode ser transferido no estado atual'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Busca atendente destino
        try:
            atendente_destino = User.objects.get(id=atendente_destino_id, is_active=True)
        except User.DoesNotExist:
            return Response(
                {'error': 'Atendente destino não encontrado ou inativo'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Não pode transferir para si mesmo
        if atendente_destino == atendimento.atendente:
            return Response(
                {'error': 'Não é possível transferir para o mesmo atendente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Se transferência entre departamentos
        departamento_destino = atendimento.departamento
        if departamento_destino_id:
            try:
                departamento_destino = Departamento.objects.get(
                    id=departamento_destino_id,
                    ativo=True
                )
            except Departamento.DoesNotExist:
                return Response(
                    {'error': 'Departamento destino não encontrado ou inativo'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verifica se atendente pertence ao departamento destino
            if not departamento_destino.atendentes.filter(id=atendente_destino_id).exists():
                return Response(
                    {'error': 'Atendente destino não pertence ao departamento destino'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Executa transferência
        with transaction.atomic():
            # Salva dados atuais para auditoria
            atendente_origem = atendimento.atendente
            departamento_origem = atendimento.departamento
            
            # Atualiza atendimento
            atendimento.atendente = atendente_destino
            atendimento.departamento = departamento_destino
            atendimento.save(update_fields=['atendente', 'departamento', 'atualizado_em'])
            
            # Cria registro de transferência
            transferencia = TransferenciaAtendimento.objects.create(
                atendimento=atendimento,
                atendente_origem=atendente_origem,
                atendente_destino=atendente_destino,
                departamento_origem=departamento_origem,
                departamento_destino=departamento_destino,
                motivo=motivo,
                aceito=True,
                aceito_em=timezone.now()
            )
            
            logger.info(
                f"Atendimento {atendimento.id} transferido: "
                f"{atendente_origem.username if atendente_origem else 'Sistema'} → "
                f"{atendente_destino.username} "
                f"(motivo: {motivo[:50]}...)"
            )
        
        # Emite evento WebSocket para atendente destino (Issue #38)
        channel_layer = get_channel_layer()
        if channel_layer:
            event_payload = {
                "event": "chat_transferred",
                "data": {
                    "atendimento_id": atendimento.id,
                    "cliente_nome": atendimento.cliente.razao_social,
                    "chat_id": atendimento.chat_id,
                    "de": atendente_origem.username if atendente_origem else "Sistema",
                    "motivo": motivo,
                    "timestamp": timezone.now().isoformat()
                },
                "version": "v1"
            }
            
            async_to_sync(channel_layer.group_send)(
                f"user_{atendente_destino.id}_whatsapp",
                {"type": "whatsapp.event", "event": event_payload}
            )
            
            logger.info(f"Notificação de transferência enviada para {atendente_destino.username}")
        
        # Retorna dados da transferência
        transferencia_serializer = TransferenciaAtendimentoSerializer(transferencia)
        return Response({
            'message': 'Atendimento transferido com sucesso',
            'transferencia': transferencia_serializer.data,
            'atendimento_id': atendimento.id
        }, status=status.HTTP_200_OK)

