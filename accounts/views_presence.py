"""
Views para gestão de presença de atendentes (Issue #51).
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from drf_spectacular.utils import extend_schema

from .models_presence import AgentPresence, TypingIndicator
from .serializers_presence import AgentPresenceSerializer, TypingIndicatorSerializer


class AgentPresenceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar presença de agentes"""
    queryset = AgentPresence.objects.select_related('agent')
    serializer_class = AgentPresenceSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='me')
    def my_presence(self, request):
        """Obtém presença do usuário autenticado"""
        presence, created = AgentPresence.objects.get_or_create(
            agent=request.user
        )
        serializer = self.get_serializer(presence)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='set-status')
    def set_status(self, request):
        """Altera status do usuário autenticado"""
        new_status = request.data.get('status')
        message = request.data.get('message', '')
        
        if new_status not in ['online', 'offline', 'busy', 'away']:
            return Response(
                {'error': 'Status inválido. Use: online, offline, busy, away'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        presence, created = AgentPresence.objects.get_or_create(
            agent=request.user
        )
        
        old_status = presence.status
        presence.set_status(new_status, message)
        
        # Emite evento WebSocket
        self._emit_presence_event(request.user.id, new_status, message)
        
        return Response({
            'message': f'Status alterado de {old_status} para {new_status}',
            'status': new_status
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='heartbeat')
    def heartbeat(self, request):
        """Atualiza heartbeat do usuário"""
        presence, created = AgentPresence.objects.get_or_create(
            agent=request.user
        )
        
        presence.heartbeat()
        
        return Response({'message': 'Heartbeat atualizado'}, status=status.HTTP_200_OK)
    
    def _emit_presence_event(self, agent_id, new_status, message):
        """Emite evento de mudança de presença"""
        from django.utils import timezone
        
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        event_payload = {
            "event": "agent_presence_changed",
            "data": {
                "agent_id": agent_id,
                "status": new_status,
                "message": message,
                "timestamp": timezone.now().isoformat()
            },
            "version": "v1"
        }
        
        # Broadcast para todos os atendentes
        async_to_sync(channel_layer.group_send)(
            "agents_presence",
            {"type": "whatsapp.event", "event": event_payload}
        )


class TypingIndicatorView(APIView):
    """View para controlar indicadores de digitação"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(summary="Indica que está digitando")
    def post(self, request):
        """Marca que o atendente está digitando"""
        chat_id = request.data.get('chat_id')
        
        if not chat_id:
            return Response(
                {'error': 'chat_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        indicator, created = TypingIndicator.objects.update_or_create(
            agent=request.user,
            chat_id=chat_id,
            defaults={'is_typing': True}
        )
        
        # Emite evento WebSocket
        self._emit_typing_event(chat_id, request.user.username, 'typing_start')
        
        return Response({'message': 'Indicador de digitação ativado'}, status=status.HTTP_200_OK)
    
    @extend_schema(summary="Indica que parou de digitar")
    def delete(self, request):
        """Marca que o atendente parou de digitar"""
        chat_id = request.query_params.get('chat_id')
        
        if not chat_id:
            return Response(
                {'error': 'chat_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            indicator = TypingIndicator.objects.get(
                agent=request.user,
                chat_id=chat_id
            )
            indicator.is_typing = False
            indicator.save(update_fields=['is_typing', 'updated_at'])
            
            # Emite evento WebSocket
            self._emit_typing_event(chat_id, request.user.username, 'typing_stop')
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except TypingIndicator.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    
    def _emit_typing_event(self, chat_id, username, event_type):
        """Emite evento de digitação"""
        from django.utils import timezone
        
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        event_payload = {
            "event": event_type,
            "data": {
                "chat_id": chat_id,
                "from": username,
                "timestamp": timezone.now().isoformat()
            },
            "version": "v1"
        }
        
        # Broadcast para todos (outros atendentes veem quem está digitando)
        async_to_sync(channel_layer.group_send)(
            "agents_presence",
            {"type": "whatsapp.event", "event": event_payload}
        )

