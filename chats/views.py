"""
Views para API de Chats (Issue #85).

Endpoints para listagem e gerenciamento de conversas.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Max, Count, OuterRef, Subquery, F, CharField, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.shortcuts import get_object_or_404
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

from atendimento.models import Atendimento, Departamento, FilaAtendimento
from whatsapp.models import WhatsAppMessage
from .serializers import (
    ChatListSerializer,
    ChatDetailSerializer,
    ChatMessageSerializer,
    AceitarChatSerializer,
    TransferirChatSerializer,
    EncerrarChatSerializer
)

logger = logging.getLogger(__name__)


class ChatViewSet(viewsets.ViewSet):
    """
    ViewSet para gerenciamento de chats/conversas.
    
    Endpoints:
    - GET /chats/ - Lista todos os chats
    - GET /chats/{chat_id}/ - Detalhes de um chat
    - GET /chats/{chat_id}/messages/ - Mensagens do chat
    - POST /chats/{chat_id}/attend/ - Assumir chat (agentes)
    - POST /chats/{chat_id}/aceitar/ - Aceitar atendimento
    - POST /chats/{chat_id}/transferir/ - Transferir para outro atendente
    - POST /chats/{chat_id}/encerrar/ - Encerrar atendimento
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """
        Lista todos os chats disponíveis.
        
        Query params:
        - status: aguardando, em_atendimento, finalizado
        - atendente: filtrar por ID do atendente
        - departamento: filtrar por ID do departamento
        - sort: campo de ordenação (lastMessage, priority, created)
        - order: asc ou desc
        """
        # Filtros
        filters = Q()
        
        status_filter = request.query_params.get('status')
        if status_filter:
            filters &= Q(status=status_filter)
        else:
            # Por padrão, não mostrar finalizados
            filters &= ~Q(status='finalizado')
        
        atendente_filter = request.query_params.get('atendente')
        if atendente_filter:
            filters &= Q(atendente_id=atendente_filter)
        
        departamento_filter = request.query_params.get('departamento')
        if departamento_filter:
            filters &= Q(departamento_id=departamento_filter)
        
        # Se não for admin, mostrar apenas próprios atendimentos + aguardando
        if not request.user.is_superuser:
            filters &= (Q(atendente=request.user) | Q(status='aguardando'))
        
        # Subquery para última mensagem
        ultima_msg = WhatsAppMessage.objects.filter(
            chat_id=OuterRef('chat_id'),
            created_at__gte=OuterRef('criado_em')
        ).order_by('-created_at')
        
        # Query principal
        atendimentos = Atendimento.objects.filter(filters).select_related(
            'cliente', 'atendente', 'departamento'
        ).annotate(
            ultima_mensagem_texto=Subquery(ultima_msg.values('text_content')[:1]),
            ultima_mensagem_em=Subquery(ultima_msg.values('created_at')[:1]),
            ultima_mensagem_tipo=Subquery(ultima_msg.values('message_type')[:1]),
            ultima_mensagem_direcao=Subquery(ultima_msg.values('direction')[:1]),
            total_mensagens=Count('chat_id'),  # Simplified
        )
        
        # Ordenação
        sort_field = request.query_params.get('sort', 'lastMessage')
        order = request.query_params.get('order', 'desc')
        
        ordering_map = {
            'lastMessage': 'ultima_mensagem_em',
            'priority': 'prioridade',
            'created': 'criado_em',
            'updated': 'atualizado_em'
        }
        
        order_field = ordering_map.get(sort_field, 'ultima_mensagem_em')
        if order == 'asc':
            atendimentos = atendimentos.order_by(order_field)
        else:
            atendimentos = atendimentos.order_by(f'-{order_field}')
        
        # Construir resposta
        chats = []
        for atend in atendimentos:
            # Calcular mensagens não lidas
            ultima_msg_atendente = WhatsAppMessage.objects.filter(
                chat_id=atend.chat_id,
                direction='outbound',
                created_at__gte=atend.criado_em
            ).aggregate(Max('created_at'))['created_at__max']
            
            if ultima_msg_atendente:
                nao_lidas = WhatsAppMessage.objects.filter(
                    chat_id=atend.chat_id,
                    direction='inbound',
                    created_at__gt=ultima_msg_atendente
                ).count()
            else:
                nao_lidas = WhatsAppMessage.objects.filter(
                    chat_id=atend.chat_id,
                    direction='inbound',
                    created_at__gte=atend.criado_em
                ).count()
            
            chats.append({
                'chat_id': atend.chat_id,
                'numero_whatsapp': atend.numero_whatsapp,
                # Cliente
                'cliente_id': atend.cliente_id,
                'cliente_nome': atend.cliente.razao_social if atend.cliente else None,
                'cliente_email': atend.cliente.email_principal if atend.cliente else None,
                # Atendimento
                'atendimento_id': atend.id,
                'status': atend.status,
                'prioridade': atend.prioridade,
                # Atendente
                'atendente_id': atend.atendente_id,
                'atendente_nome': atend.atendente.display_name if atend.atendente else None,
                # Departamento
                'departamento_id': atend.departamento_id,
                'departamento_nome': atend.departamento.nome if atend.departamento else None,
                # Última mensagem
                'ultima_mensagem_texto': atend.ultima_mensagem_texto,
                'ultima_mensagem_em': atend.ultima_mensagem_em,
                'ultima_mensagem_tipo': atend.ultima_mensagem_tipo,
                'ultima_mensagem_direcao': atend.ultima_mensagem_direcao,
                # Contadores
                'total_mensagens': WhatsAppMessage.objects.filter(
                    chat_id=atend.chat_id,
                    created_at__gte=atend.criado_em
                ).count(),
                'mensagens_nao_lidas': nao_lidas,
                # Timestamps
                'criado_em': atend.criado_em,
                'atualizado_em': atend.atualizado_em,
            })
        
        serializer = ChatListSerializer(chats, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """
        Retorna detalhes de um chat específico (por chat_id).
        """
        # Buscar atendimento ativo por chat_id
        atendimento = get_object_or_404(
            Atendimento.objects.select_related('cliente', 'atendente', 'departamento'),
            chat_id=pk,
            status__in=['aguardando', 'em_atendimento', 'pausado']
        )
        
        # Verificar permissão
        if not request.user.is_superuser:
            if atendimento.atendente and atendimento.atendente != request.user:
                if atendimento.status != 'aguardando':
                    return Response(
                        {'error': 'Você não tem permissão para visualizar este chat'},
                        status=status.HTTP_403_FORBIDDEN
                    )
        
        serializer = ChatDetailSerializer(atendimento)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='messages')
    def messages(self, request, pk=None):
        """
        Lista mensagens de um chat específico (apenas do atendimento atual).
        
        Query params:
        - limit: número de mensagens (padrão: 50)
        - offset: paginação
        """
        # Buscar atendimento
        atendimento = get_object_or_404(
            Atendimento,
            chat_id=pk,
            status__in=['aguardando', 'em_atendimento', 'pausado', 'finalizado']
        )
        
        # Verificar permissão
        if not request.user.is_superuser:
            if atendimento.atendente and atendimento.atendente != request.user:
                if atendimento.status not in ['aguardando', 'finalizado']:
                    return Response(
                        {'error': 'Você não tem permissão para visualizar este chat'},
                        status=status.HTTP_403_FORBIDDEN
                    )
        
        # Buscar mensagens APENAS deste atendimento
        mensagens = WhatsAppMessage.objects.filter(
            chat_id=pk,
            created_at__gte=atendimento.criado_em
        ).select_related('usuario').order_by('-created_at')
        
        # Paginação simples
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        total = mensagens.count()
        mensagens = mensagens[offset:offset + limit]
        
        serializer = ChatMessageSerializer(mensagens, many=True)
        
        return Response({
            'total': total,
            'limit': limit,
            'offset': offset,
            'results': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='attend')
    def attend(self, request, pk=None):
        """
        Permite que agentes assumam chats que estão aguardando atendimento.
        
        Este endpoint permite que um agente autenticado assuma um chat pendente,
        alterando seu status para "active" e atribuindo-o ao agente.
        
        Não requer body (opcional).
        """
        # Buscar o chat pelo chat_id
        try:
            atendimento = Atendimento.objects.select_related(
                'atendente', 'departamento'
            ).get(chat_id=pk)
        except Atendimento.DoesNotExist:
            return Response(
                {'error': 'Chat não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar se o chat está disponível para atendimento
        if atendimento.status not in ['aguardando', 'pending']:
            return Response(
                {
                    'error': 'Chat não está disponível para atendimento',
                    'current_status': atendimento.status
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar se o usuário é um agente válido
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Token inválido ou expirado'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verificar se o agente já está ativo (não pode assumir múltiplos chats simultaneamente)
        # Isso é opcional, mas pode ser uma boa prática de negócio
        atendimentos_ativos = Atendimento.objects.filter(
            atendente=request.user,
            status='em_atendimento'
        ).count()
        
        if atendimentos_ativos > 0:
            logger.warning(
                f"Agente {request.user.username} tentou assumir chat {pk} "
                f"mas já tem {atendimentos_ativos} chat(s) ativo(s)"
            )
            # Não bloquear, apenas logar - permitir múltiplos atendimentos
        
        # Atribuir o chat ao agente logado
        atendimento_anterior = atendimento.atendente
        
        atendimento.atendente = request.user
        atendimento.status = 'em_atendimento'
        atendimento.iniciado_em = timezone.now()
        atendimento.save()
        
        # Registrar timestamp de quando o chat foi assumido
        logger.info(
            f"Chat {pk} assumido por {request.user.username} "
            f"(atendimento: {atendimento.id}) em {atendimento.iniciado_em}"
        )
        
        # Remover da fila (se existir)
        FilaAtendimento.objects.filter(chat_id=pk).delete()
        
        # Emitir evento WebSocket para atualizar outros agentes
        self._emit_event('chat_attended', {
            'chat_id': pk,
            'atendimento_id': atendimento.id,
            'assigned_agent': request.user.id,
            'assigned_agent_name': request.user.display_name,
            'status': 'em_atendimento',
            'assigned_at': atendimento.iniciado_em.isoformat(),
            'previous_agent': atendimento_anterior.id if atendimento_anterior else None
        })
        
        # Resposta de sucesso conforme especificação
        return Response(
            {
                'message': 'Chat atendido com sucesso',
                'chat_id': pk,
                'assigned_agent': request.user.id,
                'status': 'em_atendimento',
                'assigned_at': atendimento.iniciado_em.isoformat()
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], url_path='aceitar')
    def aceitar(self, request, pk=None):
        """
        Aceita um chat em espera e vincula ao atendente.
        
        Body (opcional):
        - atendente_id: ID do atendente (padrão: usuário atual)
        - observacoes: Observações iniciais
        """
        serializer = AceitarChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Buscar atendimento
        atendimento = get_object_or_404(Atendimento, chat_id=pk)
        
        # Validar que está aguardando
        if atendimento.status != 'aguardando':
            return Response(
                {'error': f'Este chat já está {atendimento.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Definir atendente
        atendente_id = serializer.validated_data.get('atendente_id')
        if atendente_id:
            # Validar permissão (só admin pode atribuir para outros)
            if not request.user.is_superuser and atendente_id != request.user.id:
                return Response(
                    {'error': 'Você não pode atribuir para outro atendente'},
                    status=status.HTTP_403_FORBIDDEN
                )
            from django.contrib.auth import get_user_model
            User = get_user_model()
            atendente = get_object_or_404(User, id=atendente_id)
        else:
            atendente = request.user
        
        # Atualizar atendimento
        atendimento.atendente = atendente
        atendimento.status = 'em_atendimento'
        atendimento.iniciado_em = timezone.now()
        
        observacoes = serializer.validated_data.get('observacoes')
        if observacoes:
            atendimento.observacoes = observacoes
        
        atendimento.save()
        
        # Remover da fila (se existir)
        FilaAtendimento.objects.filter(chat_id=pk).delete()
        
        # Emitir evento WebSocket
        self._emit_event('chat_accepted', {
            'chat_id': pk,
            'atendimento_id': atendimento.id,
            'atendente_id': atendente.id,
            'atendente_nome': atendente.display_name,
            'status': 'em_atendimento'
        })
        
        logger.info(
            f"Chat {pk} aceito por {atendente.username} "
            f"(atendimento: {atendimento.id})"
        )
        
        serializer_response = ChatDetailSerializer(atendimento)
        return Response(serializer_response.data)
    
    @action(detail=True, methods=['post'], url_path='transferir')
    def transferir(self, request, pk=None):
        """
        Transfere chat para outro atendente.
        
        Body:
        - atendente_destino_id: ID do atendente de destino (obrigatório)
        - departamento_destino_id: ID do departamento de destino (opcional)
        - motivo: Motivo da transferência (obrigatório)
        """
        serializer = TransferirChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Buscar atendimento
        atendimento = get_object_or_404(Atendimento, chat_id=pk)
        
        # Validar permissão
        if not request.user.is_superuser:
            if atendimento.atendente != request.user:
                return Response(
                    {'error': 'Você não pode transferir este chat'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Buscar atendente destino
        from django.contrib.auth import get_user_model
        User = get_user_model()
        atendente_destino = get_object_or_404(
            User,
            id=serializer.validated_data['atendente_destino_id']
        )
        
        # Buscar departamento destino (opcional)
        departamento_destino = None
        if serializer.validated_data.get('departamento_destino_id'):
            departamento_destino = get_object_or_404(
                Departamento,
                id=serializer.validated_data['departamento_destino_id']
            )
        
        # Criar registro de transferência
        from atendimento.models import TransferenciaAtendimento
        transferencia = TransferenciaAtendimento.objects.create(
            atendimento=atendimento,
            atendente_origem=atendimento.atendente,
            atendente_destino=atendente_destino,
            departamento_origem=atendimento.departamento,
            departamento_destino=departamento_destino,
            motivo=serializer.validated_data['motivo']
        )
        
        # Atualizar atendimento
        atendimento.atendente = atendente_destino
        if departamento_destino:
            atendimento.departamento = departamento_destino
        atendimento.save()
        
        # Emitir evento WebSocket
        self._emit_event('chat_transferred', {
            'chat_id': pk,
            'atendimento_id': atendimento.id,
            'atendente_origem_id': transferencia.atendente_origem_id,
            'atendente_destino_id': atendente_destino.id,
            'atendente_destino_nome': atendente_destino.display_name,
            'motivo': transferencia.motivo
        })
        
        logger.info(
            f"Chat {pk} transferido de {transferencia.atendente_origem.username} "
            f"para {atendente_destino.username}"
        )
        
        return Response({
            'message': 'Chat transferido com sucesso',
            'transferencia_id': transferencia.id,
            'atendente_destino': {
                'id': atendente_destino.id,
                'nome': atendente_destino.display_name
            }
        })
    
    @action(detail=True, methods=['post'], url_path='encerrar')
    def encerrar(self, request, pk=None):
        """
        Encerra um atendimento.
        
        Body (opcional):
        - observacoes: Observações finais
        - solicitar_avaliacao: Enviar solicitação de avaliação (padrão: true)
        """
        serializer = EncerrarChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Buscar atendimento
        atendimento = get_object_or_404(Atendimento, chat_id=pk)
        
        # Validar permissão
        if not request.user.is_superuser:
            if atendimento.atendente != request.user:
                return Response(
                    {'error': 'Você não pode encerrar este chat'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Validar que não está finalizado
        if atendimento.status == 'finalizado':
            return Response(
                {'error': 'Este chat já está finalizado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Finalizar
        observacoes = serializer.validated_data.get('observacoes', '')
        atendimento.finalizar(observacoes)
        
        # Emitir evento WebSocket
        self._emit_event('chat_closed', {
            'chat_id': pk,
            'atendimento_id': atendimento.id,
            'atendente_id': atendimento.atendente_id,
            'finalizado_em': atendimento.finalizado_em.isoformat() if atendimento.finalizado_em else None
        })
        
        # TODO: Implementar envio de solicitação de avaliação
        solicitar_avaliacao = serializer.validated_data.get('solicitar_avaliacao', True)
        if solicitar_avaliacao:
            logger.info(f"Solicitação de avaliação para chat {pk} (a implementar)")
        
        logger.info(f"Chat {pk} encerrado por {request.user.username}")
        
        return Response({
            'message': 'Chat encerrado com sucesso',
            'atendimento_id': atendimento.id,
            'finalizado_em': atendimento.finalizado_em
        })
    
    def _emit_event(self, event_type, data):
        """Emite evento via WebSocket"""
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                'atendentes',  # Grupo de todos os atendentes
                {
                    'type': 'chat.event',
                    'event': event_type,
                    'data': data
                }
            )
