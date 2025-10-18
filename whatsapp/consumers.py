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
            
            try:
                # Adicionar ao grupo específico do usuário
                await self.channel_layer.group_add(self.group_name, self.channel_name)
                logger.info(f"✅ Usuário {user_id} adicionado ao grupo específico: {self.group_name}")
                
                # Adicionar ao grupo geral (todos os usuários)
                await self.channel_layer.group_add("whatsapp_messages", self.channel_name)
                logger.info(f"✅ Usuário {user_id} adicionado ao grupo geral: whatsapp_messages")
                
                logger.info(f"👤 WebSocket conectado para usuário {user_id}")
                logger.info(f"🎯 Grupos WebSocket configurados com sucesso")
                
            except Exception as e:
                logger.error(f"❌ Erro ao configurar grupos WebSocket para usuário {user_id}: {e}")
                # Continuar mesmo com erro nos grupos
        else:
            logger.warning("Tentativa de conexão WebSocket sem autenticação")
        
        await self.accept()
    
    async def disconnect(self, code):
        """Desconecta o WebSocket"""
        if hasattr(self, "group_name"):
            # Remover do grupo específico do usuário
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            
            # Remover do grupo geral
            await self.channel_layer.group_discard("whatsapp_messages", self.channel_name)
            
            logger.info(f"👤 WebSocket desconectado para usuário {self.user_id} (code: {code})")
            logger.info(f"✅ Usuário {self.user_id} removido dos grupos WebSocket")
    
    async def receive_json(self, content, **kwargs):
        """
        Recebe mensagens JSON do cliente.
        
        Suporta:
        - ping/pong para manter conexão
        - injeção de mensagens (apenas para testes)
        """
        logger.info(f"📨 receive_json chamado com: {content}")
        logger.info(f"📨 Tipo da mensagem: {content.get('type')}")
        logger.info(f"📨 User ID: {getattr(self, 'user_id', 'N/A')}")
        
        # Ping/pong
        if content == {"type": "ping"}:
            await self.send_json({"type": "pong"})
            return
        
        # Log para qualquer mensagem que não seja ping
        if content.get("type") != "ping":
            logger.info(f"🔍 Mensagem não-ping recebida: {content}")
        
        # Injeção de mensagem de entrada (para testes)
        if content.get("type") == "inject_incoming" and hasattr(self, "user_id"):
            logger.info(f"🔍 Processando inject_incoming para usuário {self.user_id}")
            service = get_whatsapp_session_service()
            try:
                payload = content.get("payload", {})
                from_number = content.get("from", "5511999999999")
                chat_id = content.get("chat_id", from_number)
                
                logger.info(f"📤 Dados do inject_incoming: chat_id={chat_id}, from={from_number}, payload={payload}")
                
                message = await service.handle_incoming_message(
                    user_id=self.user_id,
                    from_number=from_number,
                    chat_id=chat_id,
                    payload=payload
                )
                
                logger.info(f"✅ Mensagem injetada via WebSocket: {message.message_id}")
                
                # Processar nova conversa (Issue #85/#87)
                from chats.service import get_chat_service
                from asgiref.sync import sync_to_async
                chat_service = get_chat_service()
                logger.info(f"🔄 Processando chat service...")
                await sync_to_async(chat_service.processar_nova_mensagem_recebida)(message)
                logger.info(f"✅ Chat service processado com sucesso")
                
                # Emitir evento message_received para todos os clientes conectados
                # (broadcast via channel layer)
                from channels.layers import get_channel_layer
                channel_layer = get_channel_layer()
                
                if channel_layer:
                    # Buscar atendimento criado para pegar dados completos
                    from atendimento.models import Atendimento
                    atendimento = await sync_to_async(
                        lambda: Atendimento.objects.filter(chat_id=chat_id).first()
                    )()
                    
                    event_payload = {
                        "type": "message_received",
                        "message_id": message.message_id,
                        "from": from_number,
                        "chat_id": chat_id,
                        "payload": {
                            "type": payload.get("type", "text"),
                            "text": payload.get("text", ""),
                            "contact_name": payload.get("contact_name", from_number),
                            "message_id": message.message_id
                        },
                        "message": {
                            "id": message.id,
                            "message_id": message.message_id,
                            "chatId": chat_id,
                            "atendimento_id": atendimento.id if atendimento else None,
                            "content": payload.get("text", ""),
                            "type": payload.get("type", "text"),
                            "from": from_number,
                            "contactName": payload.get("contact_name", from_number),
                            "isFromCustomer": True,
                            "status": message.status,
                            "createdAt": message.created_at.isoformat()
                        }
                    }
                    
                    # Broadcast para todos os usuários conectados
                    await channel_layer.group_send(
                        f'user_{self.user_id}_whatsapp',
                        {
                            'type': 'whatsapp.event',
                            'event': event_payload
                        }
                    )
                    
                    logger.info(f"Evento message_received emitido via broadcast para user_{self.user_id}")
            except Exception as e:
                logger.error(f"❌ Erro ao injetar mensagem: {e}", exc_info=True)
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
        user_info = f"usuário {getattr(self, 'user_id', 'N/A')}" if hasattr(self, 'user_id') else "usuário não autenticado"
        logger.info(f"🔔 Evento WhatsApp recebido: {event_type} para {user_info}")
        logger.info(f"🔔 Payload completo: {payload}")
        
        # Processa eventos específicos
        if event_type == "message_received":
            await self._handle_message_received(payload)
        elif event_type == "message_status":
            await self._handle_message_status(payload)
        elif event_type == "session_status":
            await self._handle_session_status(payload)
        elif event_type == "message_sent":
            await self._handle_message_sent(payload)
        elif event_type == "message_status_update":
            await self._handle_message_status_update(payload)
        
        # Envia payload para o cliente
        await self.send_json(payload)
    
    async def _handle_message_sent(self, payload):
        """Processa evento de mensagem enviada"""
        logger.info(f"📤 Evento message_sent processado: {payload}")
        # Não precisa de processamento adicional, apenas log
        pass
    
    async def _handle_message_status_update(self, payload):
        """Processa evento de mudança de status da mensagem"""
        logger.info(f"📊 Evento message_status_update processado: {payload}")
        # Não precisa de processamento adicional, apenas log
        pass
    
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
    
    async def whatsapp_message_status(self, event):
        """
        Handler para notificações de status de mensagem via WebSocket
        
        Este método é chamado quando o MessageStatusService envia uma notificação
        de mudança de status de mensagem.
        """
        try:
            data = event['data']
            logger.info(f"Enviando notificação de status: {data}")
            
            await self.send_json({
                'type': 'message_status_update',
                'data': data
            })
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de status: {e}")
    
    async def whatsapp_chat_notification(self, event):
        """
        Handler para notificações de chat via WebSocket
        
        Este método é chamado quando há notificações relacionadas ao chat
        (nova mensagem, chat assumido, etc.)
        """
        try:
            data = event['data']
            logger.info(f"Enviando notificação de chat: {data}")
            
            await self.send_json({
                'type': 'chat_notification',
                'data': data
            })
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de chat: {e}")

