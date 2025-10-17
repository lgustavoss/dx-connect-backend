"""
Views para monitoramento de status de mensagens
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import WhatsAppMessage
from .message_status_service import get_message_status_service

logger = logging.getLogger(__name__)


class MessageStatsView(APIView):
    """
    Endpoint para obter estatísticas de mensagens
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Estatísticas de mensagens",
        description="Retorna estatísticas detalhadas de mensagens do usuário",
        responses={200: {
            'type': 'object',
            'properties': {
                'total': {'type': 'integer'},
                'sent': {'type': 'integer'},
                'delivered': {'type': 'integer'},
                'read': {'type': 'integer'},
                'failed': {'type': 'integer'},
                'error': {'type': 'integer'},
                'queued': {'type': 'integer'},
                'sending': {'type': 'integer'},
                'retrying': {'type': 'integer'},
                'delivery_rate': {'type': 'number'},
                'read_rate': {'type': 'number'},
                'failure_rate': {'type': 'number'},
            }
        }}
    )
    def get(self, request):
        """Retorna estatísticas de mensagens"""
        try:
            service = get_message_status_service()
            stats = await service.get_message_stats(user_id=request.user.id)
            
            return Response(stats, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return Response(
                {'error': 'Erro ao obter estatísticas'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MessageStatusListView(APIView):
    """
    Endpoint para listar mensagens por status
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Listar mensagens por status",
        description="Lista mensagens filtradas por status",
        parameters=[
            {
                'name': 'status',
                'in': 'query',
                'description': 'Status da mensagem',
                'required': False,
                'schema': {'type': 'string'}
            },
            {
                'name': 'chat_id',
                'in': 'query',
                'description': 'ID do chat',
                'required': False,
                'schema': {'type': 'string'}
            },
            {
                'name': 'limit',
                'in': 'query',
                'description': 'Número de mensagens por página',
                'required': False,
                'schema': {'type': 'integer', 'default': 50}
            },
            {
                'name': 'offset',
                'in': 'query',
                'description': 'Offset para paginação',
                'required': False,
                'schema': {'type': 'integer', 'default': 0}
            }
        ]
    )
    def get(self, request):
        """Lista mensagens filtradas por status"""
        try:
            # Parâmetros de filtro
            status_filter = request.query_params.get('status')
            chat_id = request.query_params.get('chat_id')
            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))
            
            # Construir queryset
            queryset = WhatsAppMessage.objects.filter(usuario=request.user)
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            if chat_id:
                queryset = queryset.filter(chat_id=chat_id)
            
            # Ordenar por data de criação (mais recentes primeiro)
            queryset = queryset.order_by('-created_at')
            
            # Paginação
            total = queryset.count()
            messages = queryset[offset:offset + limit]
            
            # Serializar dados
            from .serializers import WhatsAppMessageSerializer
            serializer = WhatsAppMessageSerializer(messages, many=True)
            
            return Response({
                'total': total,
                'limit': limit,
                'offset': offset,
                'results': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erro ao listar mensagens: {e}")
            return Response(
                {'error': 'Erro ao listar mensagens'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RetryFailedMessagesView(APIView):
    """
    Endpoint para tentar reenviar mensagens que falharam
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Reenviar mensagens falhadas",
        description="Tenta reenviar mensagens que falharam no envio",
        responses={200: {
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'messages_retried': {'type': 'integer'},
                'message': {'type': 'string'}
            }
        }}
    )
    def post(self, request):
        """Tenta reenviar mensagens que falharam"""
        try:
            service = get_message_status_service()
            count = await service.retry_failed_messages()
            
            return Response({
                'success': True,
                'messages_retried': count,
                'message': f'{count} mensagens marcadas para retry'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erro ao processar retry: {e}")
            return Response(
                {'error': 'Erro ao processar retry'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MessageStatusUpdateView(APIView):
    """
    Endpoint para atualizar status de mensagem manualmente
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Atualizar status de mensagem",
        description="Atualiza o status de uma mensagem específica",
        request={
            'type': 'object',
            'properties': {
                'message_id': {'type': 'string'},
                'status': {'type': 'string'},
                'error_message': {'type': 'string'},
                'failure_reason': {'type': 'string'}
            },
            'required': ['message_id', 'status']
        },
        responses={200: {
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'message_id': {'type': 'string'},
                'status': {'type': 'string'}
            }
        }}
    )
    def post(self, request):
        """Atualiza status de uma mensagem"""
        try:
            message_id = request.data.get('message_id')
            status_value = request.data.get('status')
            error_message = request.data.get('error_message', '')
            failure_reason = request.data.get('failure_reason', '')
            
            if not message_id or not status_value:
                return Response(
                    {'error': 'message_id e status são obrigatórios'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar se a mensagem pertence ao usuário
            try:
                message = WhatsAppMessage.objects.get(
                    message_id=message_id,
                    usuario=request.user
                )
            except WhatsAppMessage.DoesNotExist:
                return Response(
                    {'error': 'Mensagem não encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            service = get_message_status_service()
            updated_message = await service.update_message_status(
                message_id=message_id,
                status=status_value,
                error_message=error_message,
                failure_reason=failure_reason
            )
            
            if updated_message:
                return Response({
                    'success': True,
                    'message_id': message_id,
                    'status': status_value
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Erro ao atualizar status'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Erro ao atualizar status da mensagem: {e}")
            return Response(
                {'error': 'Erro ao atualizar status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatReadStatusView(APIView):
    """
    Endpoint para marcar mensagens de um chat como lidas
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Marcar chat como lido",
        description="Marca todas as mensagens não lidas de um chat como lidas",
        request={
            'type': 'object',
            'properties': {
                'chat_id': {'type': 'string'}
            },
            'required': ['chat_id']
        },
        responses={200: {
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'chat_id': {'type': 'string'},
                'messages_marked_as_read': {'type': 'integer'}
            }
        }}
    )
    def post(self, request):
        """Marca mensagens de um chat como lidas"""
        try:
            chat_id = request.data.get('chat_id')
            
            if not chat_id:
                return Response(
                    {'error': 'chat_id é obrigatório'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            service = get_message_status_service()
            count = await service.mark_as_read_by_chat(chat_id)
            
            return Response({
                'success': True,
                'chat_id': chat_id,
                'messages_marked_as_read': count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erro ao marcar chat como lido: {e}")
            return Response(
                {'error': 'Erro ao marcar chat como lido'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
