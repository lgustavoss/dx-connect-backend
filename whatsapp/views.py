"""
Views DRF para gerenciamento de sessões e mensagens WhatsApp.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
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
    
    @extend_schema(
        summary="Exportar sessão",
        description="Exporta dados da sessão para backup (Issue #47)"
    )
    @action(detail=True, methods=['get'], url_path='export')
    def export_session(self, request, pk=None):
        """Exporta dados da sessão (backup)"""
        import json
        from django.http import HttpResponse
        
        session = self.get_object()
        
        export_data = {
            'session_id': session.id,
            'usuario_id': session.usuario_id,
            'device_name': session.device_name,
            'phone_number': session.phone_number,
            'session_data': session.session_data,
            'auto_reconnect': session.auto_reconnect,
            'proxy_enabled': session.proxy_enabled,
            'proxy_url': session.proxy_url,
            'created_at': session.created_at.isoformat(),
            'connected_at': session.connected_at.isoformat() if session.connected_at else None,
            'export_timestamp': timezone.now().isoformat(),
        }
        
        # Retorna como arquivo JSON
        response = HttpResponse(
            json.dumps(export_data, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="whatsapp_session_{session.id}_backup.json"'
        
        logger.info(f"Sessão {session.id} exportada para backup")
        
        return response
    
    @extend_schema(
        summary="Importar sessão",
        description="Importa dados de sessão de um backup (Issue #47)"
    )
    @action(detail=False, methods=['post'], url_path='import')
    def import_session(self, request):
        """Importa dados de sessão de um backup"""
        import json
        
        backup_data = request.data
        
        if not backup_data:
            return Response(
                {'error': 'Dados de backup não fornecidos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Cria ou atualiza sessão
            session, created = WhatsAppSession.objects.update_or_create(
                usuario_id=request.user.id,
                defaults={
                    'device_name': backup_data.get('device_name', 'DX Connect Web'),
                    'phone_number': backup_data.get('phone_number', ''),
                    'session_data': backup_data.get('session_data', ''),
                    'auto_reconnect': backup_data.get('auto_reconnect', True),
                    'proxy_enabled': backup_data.get('proxy_enabled', False),
                    'proxy_url': backup_data.get('proxy_url', ''),
                    'status': 'disconnected',
                    'is_active': True
                }
            )
            
            action = "criada" if created else "atualizada"
            logger.info(f"Sessão {session.id} {action} a partir de backup")
            
            return Response({
                'message': f'Sessão {action} com sucesso',
                'session_id': session.id,
                'created': created
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Erro ao importar sessão: {e}", exc_info=True)
            return Response(
                {'error': f'Erro ao importar sessão: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Forçar reconexão",
        description="Força uma tentativa de reconexão manual (Issue #47)"
    )
    @action(detail=True, methods=['post'], url_path='reconnect')
    def force_reconnect(self, request, pk=None):
        """Força reconexão da sessão"""
        from whatsapp.tasks import auto_reconnect_session_task
        
        session = self.get_object()
        
        # Enfileira task de reconexão
        task = auto_reconnect_session_task.apply_async(
            kwargs={'session_id': session.id},
            countdown=0
        )
        
        logger.info(f"Reconexão forçada para sessão {session.id} (task: {task.id})")
        
        return Response({
            'message': 'Reconexão iniciada',
            'task_id': task.id,
            'session_id': session.id
        }, status=status.HTTP_202_ACCEPTED)


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
        """
        Envia uma mensagem WhatsApp via fila (Issue #45).
        
        A mensagem é enfileirada para envio assíncrono com retentativas automáticas.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        serializer = WhatsAppSendMessageSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        try:
            # Prepara payload
            payload = {
                'type': data['type'],
                'text': data.get('text', ''),
                'media_url': data.get('media_url', ''),
            }
            
            client_message_id = data.get('client_message_id')
            
            # Enfileira mensagem para envio via Celery (Issue #45)
            from whatsapp.tasks import send_whatsapp_message_task
            
            task = send_whatsapp_message_task.apply_async(
                kwargs={
                    'user_id': request.user.id,
                    'to': data['to'],
                    'payload': payload,
                    'client_message_id': client_message_id
                },
                countdown=0  # Enviar imediatamente
            )
            
            logger.info(
                f"Mensagem enfileirada para {data['to']} "
                f"(task_id: {task.id}, user: {request.user.id})"
            )
            
            return Response({
                'message': 'Mensagem enfileirada para envio',
                'task_id': task.id,
                'to': data['to'],
                'client_message_id': client_message_id,
                'status': 'queued'
            }, status=status.HTTP_202_ACCEPTED)
        
        except Exception as e:
            logger.error(f"Erro ao enfileirar mensagem: {e}", exc_info=True)
            return Response(
                {'error': f'Erro ao enfileirar mensagem: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WhatsAppWebhookView(APIView):
    """
    Webhook para receber mensagens externas do WhatsApp.
    
    Implementa a Issue #44 - recebimento de mensagens com payload bruto
    e versão do protocolo.
    """
    permission_classes = [AllowAny]  # Webhook público (validar via assinatura no futuro)
    
    @extend_schema(
        summary="Webhook para receber mensagens WhatsApp",
        description="Recebe mensagens do WhatsApp via webhook externo (formato v1)",
        responses={200: WhatsAppMessageSerializer}
    )
    def post(self, request):
        """
        Processa mensagem recebida via webhook.
        
        Formato esperado (v1):
        {
            "event": "message_received",
            "data": {
                "from": "5511999999999",
                "message": "Texto da mensagem",
                "message_id": "abc123",
                "timestamp": "2024-01-01T10:00:00Z",
                "media_url": null,
                "media_type": null
            },
            "version": "v1"
        }
        """
        import logging
        from django.utils import timezone
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        logger = logging.getLogger(__name__)
        
        # Captura timestamp de recebimento para cálculo de latência
        received_at = timezone.now()
        
        # Armazena payload bruto
        raw_payload = request.data
        
        # Extrai dados do evento
        event_type = raw_payload.get('event')
        event_data = raw_payload.get('data', {})
        protocol_version = raw_payload.get('version', 'v1')
        
        if event_type != 'message_received':
            return Response(
                {'error': f'Evento não suportado: {event_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Valida campos obrigatórios
        required_fields = ['from', 'message']
        missing_fields = [f for f in required_fields if f not in event_data]
        if missing_fields:
            return Response(
                {'error': f'Campos obrigatórios ausentes: {", ".join(missing_fields)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Extrai dados da mensagem
            from_number = event_data['from']
            message_text = event_data['message']
            message_id = event_data.get('message_id', f"webhook_{timezone.now().timestamp()}")
            timestamp_str = event_data.get('timestamp')
            media_url = event_data.get('media_url')
            media_type = event_data.get('media_type')
            
            # Determina tipo de mensagem
            if media_url:
                if media_type and media_type.startswith('image'):
                    msg_type = 'image'
                elif media_type and media_type.startswith('audio'):
                    msg_type = 'audio'
                elif media_type and media_type.startswith('video'):
                    msg_type = 'video'
                else:
                    msg_type = 'document'
            else:
                msg_type = 'text'
            
            # Prepara payload processado
            processed_payload = {
                'type': msg_type,
                'text': message_text,
                'media_url': media_url or '',
                'mime_type': media_type or '',
                'contact_name': event_data.get('contact_name', ''),
                'message_id': message_id,
            }
            
            # TODO: Determinar qual usuário/sessão deve receber a mensagem
            # Por enquanto, busca a primeira sessão ativa
            from whatsapp.models import WhatsAppSession
            active_session = WhatsAppSession.objects.filter(
                status='ready',
                is_active=True
            ).first()
            
            if not active_session:
                logger.warning("Nenhuma sessão ativa disponível para receber mensagem")
                return Response(
                    {'error': 'Nenhuma sessão ativa disponível'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            user_id = active_session.usuario_id
            chat_id = from_number
            
            # Processa a mensagem via serviço
            service = get_whatsapp_session_service()
            message = async_to_sync(service.handle_incoming_message)(
                user_id=user_id,
                from_number=from_number,
                chat_id=chat_id,
                payload=processed_payload,
                raw_payload=raw_payload,
                protocol_version=protocol_version
            )
            
            # Calcula latência
            latency_ms = (timezone.now() - received_at).total_seconds() * 1000
            
            logger.info(
                f"Mensagem webhook recebida: {message_id} de {from_number} "
                f"(latência: {latency_ms:.0f}ms, protocolo: {protocol_version})"
            )
            
            # Emite evento via WebSocket no formato v1
            channel_layer = get_channel_layer()
            if channel_layer:
                event_payload = {
                    "event": "message_received",
                    "data": {
                        "from": from_number,
                        "message": message_text,
                        "message_id": message_id,
                        "timestamp": timestamp_str or timezone.now().isoformat(),
                        "media_url": media_url,
                        "media_type": media_type,
                        "latency_ms": latency_ms,
                    },
                    "version": protocol_version
                }
                
                async_to_sync(channel_layer.group_send)(
                    f"user_{user_id}_whatsapp",
                    {"type": "whatsapp.event", "event": event_payload}
                )
            
            # Processar nova conversa (Issue #85)
            from chats.service import get_chat_service
            chat_service = get_chat_service()
            chat_service.processar_nova_mensagem_recebida(message)
            
            # Retorna mensagem criada
            serializer = WhatsAppMessageSerializer(message)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {e}", exc_info=True)
            return Response(
                {'error': f'Erro ao processar mensagem: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WhatsAppInjectIncomingView(APIView):
    """
    View para injetar mensagens de teste (apenas para desenvolvimento).
    
    Simula o recebimento de uma mensagem de um cliente, útil para:
    - Testes de integração do frontend
    - Desenvolvimento sem WhatsApp real
    - Scripts de teste automatizados
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Injetar mensagem de teste",
        description="Simula o recebimento de uma mensagem WhatsApp (apenas para testes)",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'from': {
                        'type': 'string',
                        'description': 'Número do remetente',
                        'example': '5511999999999'
                    },
                    'payload': {
                        'type': 'object',
                        'properties': {
                            'type': {'type': 'string', 'example': 'text'},
                            'text': {'type': 'string', 'example': 'Olá, preciso de ajuda!'},
                            'contact_name': {'type': 'string', 'example': 'João Silva'}
                        }
                    }
                },
                'required': ['from', 'payload']
            }
        },
        responses={200: WhatsAppMessageSerializer}
    )
    def post(self, request):
        """
        Injeta uma mensagem de entrada para testes.
        
        Esta view simula o recebimento de uma mensagem via WhatsApp,
        útil para desenvolvimento e testes sem precisar de conexão real.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Validar dados
        from_number = request.data.get('from')
        payload = request.data.get('payload', {})
        
        if not from_number:
            return Response(
                {'error': 'Campo "from" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not payload:
            return Response(
                {'error': 'Campo "payload" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar tipo de mensagem
        msg_type = payload.get('type', 'text')
        if msg_type not in ['text', 'image', 'audio', 'video', 'document']:
            return Response(
                {'error': f'Tipo de mensagem inválido: {msg_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Para mensagens de texto, validar que tem conteúdo
        if msg_type == 'text' and not payload.get('text'):
            return Response(
                {'error': 'Campo "payload.text" é obrigatório para mensagens de texto'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            service = get_whatsapp_session_service()
            chat_id = request.data.get('chat_id', from_number)
            
            # Processar mensagem via service (async)
            message = async_to_sync(service.handle_incoming_message)(
                user_id=request.user.id,
                from_number=from_number,
                chat_id=chat_id,
                payload=payload
            )
            
            logger.info(
                f"Mensagem de teste injetada: {message.message_id} "
                f"de {from_number} (user: {request.user.id})"
            )
            
            # Processar nova conversa (Issue #85)
            from chats.service import get_chat_service
            chat_service = get_chat_service()
            chat_service.processar_nova_mensagem_recebida(message)
            
            # Serializar e retornar
            from .serializers import WhatsAppMessageSerializer
            serializer = WhatsAppMessageSerializer(message)
            
            return Response({
                'message': 'Mensagem de teste injetada com sucesso',
                'message_id': message.message_id,
                'database_id': message.id,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        except RuntimeError as e:
            if 'Sessão não encontrada' in str(e):
                return Response(
                    {'error': 'Sessão WhatsApp não encontrada. Inicie uma sessão primeiro.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            raise
        
        except Exception as e:
            logger.error(f"Erro ao injetar mensagem de teste: {e}", exc_info=True)
            return Response(
                {'error': f'Erro ao injetar mensagem: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

