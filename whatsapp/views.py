"""
Views DRF para gerenciamento de sessões e mensagens WhatsApp.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from drf_spectacular.utils import extend_schema, OpenApiParameter
from asgiref.sync import async_to_sync

from .models import WhatsAppSession, WhatsAppMessage
from .serializers import (
    WhatsAppSessionSerializer,
    WhatsAppSessionListSerializer,
    WhatsAppMessageSerializer,
    WhatsAppMessageListSerializer,
    WhatsAppSendMessageSerializer,
    WhatsAppSessionStatusSerializer
)
from .service import get_whatsapp_session_service


class WhatsAppSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de sessões WhatsApp.
    
    Permite listar, visualizar, criar e gerenciar sessões WhatsApp.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_active']
    search_fields = ['phone_number', 'device_name']
    ordering_fields = ['created_at', 'updated_at', 'connected_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Filtra sessões do usuário autenticado ou todas se superuser"""
        queryset = WhatsAppSession.objects.select_related('usuario')
        
        if not self.request.user.is_superuser:
            queryset = queryset.filter(usuario=self.request.user)
        
        return queryset
    
    def get_serializer_class(self):
        """Retorna serializer apropriado para a ação"""
        if self.action == 'list':
            return WhatsAppSessionListSerializer
        return WhatsAppSessionSerializer
    
    @extend_schema(
        summary="Iniciar sessão WhatsApp",
        description="Inicia uma nova sessão WhatsApp para o usuário autenticado",
        responses={202: WhatsAppSessionStatusSerializer}
    )
    @action(detail=False, methods=['post'], url_path='start')
    def start_session(self, request):
        """Inicia uma sessão WhatsApp"""
        service = get_whatsapp_session_service()
        
        try:
            result = async_to_sync(service.start_session)(request.user.id)
            return Response(result, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response(
                {'error': f'Erro ao iniciar sessão: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Parar sessão WhatsApp",
        description="Encerra a sessão WhatsApp ativa do usuário autenticado"
    )
    @action(detail=False, methods=['post'], url_path='stop')
    def stop_session(self, request):
        """Encerra uma sessão WhatsApp"""
        service = get_whatsapp_session_service()
        
        try:
            async_to_sync(service.stop_session)(request.user.id)
            return Response(
                {'message': 'Sessão encerrada com sucesso'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': f'Erro ao encerrar sessão: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Status da sessão WhatsApp",
        description="Obtém o status atual da sessão WhatsApp do usuário autenticado",
        responses={200: WhatsAppSessionStatusSerializer}
    )
    @action(detail=False, methods=['get'], url_path='status')
    def session_status(self, request):
        """Obtém status da sessão"""
        service = get_whatsapp_session_service()
        
        try:
            result = async_to_sync(service.get_session_status)(request.user.id)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Erro ao obter status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Métricas da sessão",
        description="Obtém métricas detalhadas de uma sessão específica"
    )
    @action(detail=True, methods=['get'], url_path='metrics')
    def session_metrics(self, request, pk=None):
        """Obtém métricas detalhadas da sessão"""
        session = self.get_object()
        
        # Métricas de mensagens
        messages = session.messages.all()
        
        # Calcular latência média manualmente (propriedades não podem ser usadas em queries)
        outbound_messages = messages.filter(direction='outbound', sent_at__isnull=False)
        avg_latency = None
        if outbound_messages.exists():
            from django.db.models import F, ExpressionWrapper, fields
            from django.db.models.functions import Extract
            
            # Calcula diferença em milissegundos
            latencies = []
            for msg in outbound_messages:
                if msg.sent_at and msg.queued_at:
                    delta_ms = (msg.sent_at - msg.queued_at).total_seconds() * 1000
                    latencies.append(delta_ms)
            
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
        
        metrics = {
            'session_id': session.id,
            'total_messages': messages.count(),
            'messages_sent': messages.filter(direction='outbound').count(),
            'messages_received': messages.filter(direction='inbound').count(),
            'messages_with_error': messages.filter(status='error').count(),
            'avg_latency_ms': avg_latency,
            'latency_acceptable_rate': self._calculate_latency_rate(messages),
            'uptime_seconds': session.uptime_seconds,
            'error_count': session.error_count,
        }
        
        return Response(metrics, status=status.HTTP_200_OK)
    
    def _calculate_latency_rate(self, messages):
        """Calcula taxa de mensagens com latência aceitável"""
        total = messages.count()
        if total == 0:
            return 100.0
        
        acceptable = sum(
            1 for msg in messages 
            if msg.is_latency_acceptable
        )
        
        return round((acceptable / total) * 100, 2)


class WhatsAppMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consulta de mensagens WhatsApp (somente leitura).
    
    Permite listar e visualizar mensagens enviadas e recebidas.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'direction', 'message_type', 'status', 'chat_id', 
        'is_from_me', 'session'
    ]
    search_fields = ['text_content', 'contact_number', 'contact_name']
    ordering_fields = ['created_at', 'sent_at', 'delivered_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtra mensagens do usuário autenticado ou todas se superuser"""
        queryset = WhatsAppMessage.objects.select_related('session', 'usuario')
        
        if not self.request.user.is_superuser:
            queryset = queryset.filter(usuario=self.request.user)
        
        return queryset
    
    def get_serializer_class(self):
        """Retorna serializer apropriado para a ação"""
        if self.action == 'list':
            return WhatsAppMessageListSerializer
        return WhatsAppMessageSerializer
    
    @extend_schema(
        summary="Mensagens com alta latência",
        description="Lista mensagens que excederam o limite de latência de 5 segundos"
    )
    @action(detail=False, methods=['get'], url_path='high-latency')
    def high_latency_messages(self, request):
        """Lista mensagens com latência alta (> 5s)"""
        # Filtrar manualmente, pois latency_to_sent_ms é uma propriedade
        all_messages = self.get_queryset().filter(
            direction='outbound',
            sent_at__isnull=False
        )
        
        high_latency_messages = [
            msg for msg in all_messages
            if msg.latency_to_sent_ms and msg.latency_to_sent_ms > 5000
        ]
        
        serializer = self.get_serializer(high_latency_messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        summary="Estatísticas de latência",
        description="Retorna estatísticas agregadas de latência das mensagens"
    )
    @action(detail=False, methods=['get'], url_path='latency-stats')
    def latency_stats(self, request):
        """Retorna estatísticas de latência"""
        messages = self.get_queryset()
        
        # Mensagens enviadas
        outbound = messages.filter(direction='outbound')
        
        # Calcular latências manualmente
        sent_messages = outbound.filter(sent_at__isnull=False)
        delivered_messages = outbound.filter(delivered_at__isnull=False)
        
        avg_to_sent = None
        avg_to_delivered = None
        messages_over_5s = 0
        
        if sent_messages.exists():
            latencies_sent = []
            for msg in sent_messages:
                if msg.sent_at and msg.queued_at:
                    delta_ms = (msg.sent_at - msg.queued_at).total_seconds() * 1000
                    latencies_sent.append(delta_ms)
                    if delta_ms > 5000:
                        messages_over_5s += 1
            
            if latencies_sent:
                avg_to_sent = sum(latencies_sent) / len(latencies_sent)
        
        if delivered_messages.exists():
            latencies_delivered = []
            for msg in delivered_messages:
                if msg.delivered_at and msg.queued_at:
                    delta_ms = (msg.delivered_at - msg.queued_at).total_seconds() * 1000
                    latencies_delivered.append(delta_ms)
            
            if latencies_delivered:
                avg_to_delivered = sum(latencies_delivered) / len(latencies_delivered)
        
        stats = {
            'total_messages': messages.count(),
            'outbound_messages': outbound.count(),
            'inbound_messages': messages.filter(direction='inbound').count(),
            'avg_latency_to_sent_ms': avg_to_sent,
            'avg_latency_to_delivered_ms': avg_to_delivered,
            'messages_over_5s': messages_over_5s,
            'latency_acceptable_rate': self._calculate_acceptable_rate(outbound),
        }
        
        return Response(stats, status=status.HTTP_200_OK)
    
    def _calculate_acceptable_rate(self, messages):
        """Calcula taxa de mensagens com latência aceitável"""
        total = messages.count()
        if total == 0:
            return 100.0
        
        acceptable = sum(
            1 for msg in messages 
            if msg.is_latency_acceptable
        )
        
        return round((acceptable / total) * 100, 2)


class WhatsAppSendMessageView(APIView):
    """
    View para envio de mensagens WhatsApp.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Enviar mensagem WhatsApp",
        description="Envia uma mensagem via WhatsApp",
        request=WhatsAppSendMessageSerializer,
        responses={202: WhatsAppMessageSerializer}
    )
    def post(self, request):
        """Envia uma mensagem WhatsApp"""
        serializer = WhatsAppSendMessageSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        service = get_whatsapp_session_service()
        
        try:
            # Prepara payload
            payload = {
                'type': data['type'],
                'text': data.get('text', ''),
                'media_url': data.get('media_url', ''),
            }
            
            result = async_to_sync(service.send_message)(
                user_id=request.user.id,
                to=data['to'],
                payload=payload,
                client_message_id=data.get('client_message_id')
            )
            
            return Response(result, status=status.HTTP_202_ACCEPTED)
        
        except RuntimeError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_423_LOCKED
            )
        except Exception as e:
            return Response(
                {'error': f'Erro ao enviar mensagem: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

