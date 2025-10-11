"""
WebSocket consumers aprimorados para WhatsApp com persistência.
"""
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from urllib.parse import parse_qs

from .service import get_whatsapp_session_service

logger = logging.getLogger(__name__)
User = get_user_model()


class WhatsAppConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer para eventos WhatsApp com persistência.
    
    Responsável por:
    - Receber eventos do serviço stub
    - Persistir mensagens no banco
    - Enviar eventos para o cliente
    - Calcular métricas de latência
    """
    
    async def connect(self):
        """Conecta o WebSocket e autentica o usuário"""
        # Tenta resolver usuário via middleware ou via token no query string
        user_id = None
        
        if getattr(self.scope, "user", None) and getattr(self.scope["user"], "is_authenticated", False):
            user_id = self.scope["user"].id
        else:
            try:
                query = self.scope.get("query_string", b"").decode()
                params = parse_qs(query)
                token = (params.get("token") or [None])[0]
                if token:
                    access = AccessToken(token)
                    user_id = access.get("user_id")
            except Exception as e:
                logger.warning(f"Falha na autenticação WebSocket: {e}")
                user_id = None
        
        if user_id:
            self.user_id = user_id
            self.group_name = f"user_{user_id}_whatsapp"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            logger.info(f"WebSocket conectado para usuário {user_id}")
        else:
            logger.warning("Tentativa de conexão WebSocket sem autenticação")
        
        await self.accept()
    
    async def disconnect(self, code):
        """Desconecta o WebSocket"""
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info(f"WebSocket desconectado para usuário {self.user_id} (code: {code})")
    
    async def receive_json(self, content, **kwargs):
        """
        Recebe mensagens JSON do cliente.
        
        Suporta:
        - ping/pong para manter conexão
        - injeção de mensagens (apenas para testes)
        """
        # Ping/pong
        if content == {"type": "ping"}:
            await self.send_json({"type": "pong"})
            return
        
        # Injeção de mensagem de entrada (para testes)
        if content.get("type") == "inject_incoming" and hasattr(self, "user_id"):
            service = get_whatsapp_session_service()
            try:
                payload = content.get("payload", {})
                from_number = content.get("from", "5511999999999")
                chat_id = content.get("chat_id", from_number)
                
                message = await service.handle_incoming_message(
                    user_id=self.user_id,
                    from_number=from_number,
                    chat_id=chat_id,
                    payload=payload
                )
                
                logger.info(f"Mensagem injetada: {message.message_id}")
                
                # Envia confirmação
                await self.send_json({
                    "type": "inject_success",
                    "message_id": message.message_id
                })
            except Exception as e:
                logger.error(f"Erro ao injetar mensagem: {e}", exc_info=True)
                await self.send_json({
                    "type": "inject_error",
                    "error": str(e)
                })
    
    async def whatsapp_event(self, event):
        """
        Manipula eventos WhatsApp recebidos do channel layer.
        
        Este método é chamado quando o serviço stub emite eventos via channel layer.
        """
        payload = event.get("event") or {}
        event_type = payload.get("type")
        
        # Log do evento
        logger.debug(f"Evento WhatsApp recebido: {event_type}")
        
        # Processa eventos específicos
        if event_type == "message_received":
            await self._handle_message_received(payload)
        elif event_type == "message_status":
            await self._handle_message_status(payload)
        elif event_type == "session_status":
            await self._handle_session_status(payload)
        
        # Envia payload para o cliente
        await self.send_json(payload)
    
    async def _handle_message_received(self, payload):
        """Processa mensagem recebida e persiste no banco"""
        if not hasattr(self, "user_id"):
            return
        
        service = get_whatsapp_session_service()
        
        try:
            # Extrai dados do payload
            from_number = payload.get("from", "")
            chat_id = payload.get("chat_id", from_number)
            
            # Persiste a mensagem
            message = await service.handle_incoming_message(
                user_id=self.user_id,
                from_number=from_number,
                chat_id=chat_id,
                payload=payload.get("payload", {})
            )
            
            logger.info(
                f"Mensagem recebida persistida: {message.message_id} "
                f"(latência: {message.total_latency_ms}ms)"
            )
        
        except Exception as e:
            logger.error(
                f"Erro ao persistir mensagem recebida: {e}",
                exc_info=True
            )
    
    async def _handle_message_status(self, payload):
        """Atualiza status de mensagem no banco"""
        if not hasattr(self, "user_id"):
            return
        
        service = get_whatsapp_session_service()
        
        try:
            message_id = payload.get("message_id")
            new_status = payload.get("status")
            
            if message_id and new_status:
                await service.update_message_status(message_id, new_status)
        
        except Exception as e:
            logger.error(
                f"Erro ao atualizar status de mensagem: {e}",
                exc_info=True
            )
    
    async def _handle_session_status(self, payload):
        """Atualiza status da sessão no banco"""
        if not hasattr(self, "user_id"):
            return
        
        # O serviço já atualiza o status da sessão ao receber eventos do stub
        # Este método pode ser usado para lógica adicional no futuro
        logger.debug(f"Status da sessão atualizado: {payload.get('status')}")

