"""
Serviço de gestão de sessões WhatsApp com persistência.

Este serviço integra o stub do WhatsApp com os modelos de persistência,
garantindo que todas as sessões e mensagens sejam armazenadas no banco de dados
com métricas de latência.
"""
from __future__ import annotations

import logging
import uuid
from typing import Dict, Optional
from django.utils import timezone
from django.db import transaction

from integrations.whatsapp_stub import get_whatsapp_service, StubWhatsAppSessionService
from .models import WhatsAppSession, WhatsAppMessage

logger = logging.getLogger(__name__)


class WhatsAppSessionService:
    """
    Serviço de alto nível para gerenciamento de sessões WhatsApp.
    
    Responsabilidades:
    - Gerenciar ciclo de vida das sessões (start/stop/status)
    - Persistir sessões e mensagens no banco
    - Calcular e registrar métricas de latência
    - Integrar com o serviço stub do WhatsApp
    """
    
    def __init__(self):
        self.stub_service: StubWhatsAppSessionService = get_whatsapp_service()
    
    def get_or_create_session(self, user_id: int) -> WhatsAppSession:
        """
        Obtém ou cria uma sessão para o usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            WhatsAppSession: Sessão do usuário
        """
        session, created = WhatsAppSession.objects.get_or_create(
            usuario_id=user_id,
            is_active=True,
            defaults={
                'status': 'disconnected',
                'device_name': 'DX Connect Web'
            }
        )
        
        if created:
            logger.info(f"Nova sessão WhatsApp criada para usuário {user_id}")
        
        return session
    
    async def start_session(self, user_id: int) -> Dict:
        """
        Inicia uma sessão WhatsApp.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dict com status da sessão
        """
        session = await self._aget_or_create_session(user_id)
        
        # Chama o stub service
        result = await self.stub_service.start(user_id)
        
        # Atualiza a sessão no banco
        session.status = result['status']
        await self._asave_session(session, update_fields=['status', 'updated_at'])
        
        logger.info(f"Sessão WhatsApp iniciada para usuário {user_id} - Status: {result['status']}")
        
        return {
            'session_id': session.id,
            'status': session.status,
            'message': 'Sessão iniciada com sucesso'
        }
    
    async def stop_session(self, user_id: int) -> None:
        """
        Encerra uma sessão WhatsApp.
        
        Args:
            user_id: ID do usuário
        """
        session = await self._aget_session(user_id)
        
        if not session:
            logger.warning(f"Tentativa de parar sessão inexistente para usuário {user_id}")
            return
        
        # Chama o stub service
        await self.stub_service.stop(user_id)
        
        # Atualiza a sessão no banco (async-safe)
        from asgiref.sync import sync_to_async
        await sync_to_async(session.mark_as_disconnected)()
        
        logger.info(f"Sessão WhatsApp encerrada para usuário {user_id}")
    
    async def get_session_status(self, user_id: int) -> Dict:
        """
        Obtém o status atual da sessão.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dict com status e métricas da sessão
        """
        session = await self._aget_session(user_id)
        
        if not session:
            return {
                'status': 'disconnected',
                'message': 'Nenhuma sessão encontrada'
            }
        
        # Sincroniza com o stub service
        stub_status = await self.stub_service.get_status(user_id)
        
        # Atualiza status se diferente
        if session.status != stub_status['status']:
            session.status = stub_status['status']
            await self._asave_session(session, update_fields=['status', 'updated_at'])
        
        return {
            'session_id': session.id,
            'status': session.status,
            'is_connected': session.is_connected,
            'phone_number': session.phone_number,
            'device_name': session.device_name,
            'connected_at': session.connected_at.isoformat() if session.connected_at else None,
            'uptime_seconds': session.uptime_seconds,
            'total_messages_sent': session.total_messages_sent,
            'total_messages_received': session.total_messages_received,
            'last_message_at': session.last_message_at.isoformat() if session.last_message_at else None,
            'error_count': session.error_count,
        }
    
    async def send_message(
        self,
        user_id: int,
        to: str,
        payload: Dict,
        client_message_id: Optional[str] = None
    ) -> Dict:
        """
        Envia uma mensagem e persiste no banco.
        
        Args:
            user_id: ID do usuário
            to: Número do destinatário
            payload: Payload da mensagem
            client_message_id: ID personalizado (opcional)
            
        Returns:
            Dict com resultado do envio
        """
        session = await self._aget_session(user_id)
        
        if not session or not session.is_connected:
            raise RuntimeError("Sessão não está pronta para enviar mensagens")
        
        # Gera message_id se não fornecido
        if not client_message_id:
            client_message_id = str(uuid.uuid4())
        
        # Cria registro da mensagem no banco (status: queued)
        message = await self._acreate_message(
            session=session,
            message_id=client_message_id,
            direction='outbound',
            message_type=payload.get('type', 'text'),
            chat_id=to,
            contact_number=to,
            text_content=payload.get('text', ''),
            media_url=payload.get('media_url', ''),
            payload=payload,
            client_message_id=client_message_id,
            is_from_me=True,
            usuario_id=user_id
        )
        
        try:
            # Envia via stub service
            result = await self.stub_service.send_message(
                user_id, to, payload, client_message_id
            )
            
            # Atualiza contadores da sessão (async-safe)
            from asgiref.sync import sync_to_async
            await sync_to_async(session.increment_sent_messages)()
            
            logger.info(
                f"Mensagem {message.message_id} enviada para {to} "
                f"(usuário {user_id})"
            )
            
            return {
                'message_id': result['message_id'],
                'database_id': message.id,
                'status': 'queued',
                'message': 'Mensagem enfileirada para envio'
            }
        
        except Exception as e:
            # Marca mensagem como erro
            await self._amark_message_error(message, str(e))
            logger.error(
                f"Erro ao enviar mensagem {message.message_id}: {e}",
                exc_info=True
            )
            raise
    
    async def handle_incoming_message(
        self,
        user_id: int,
        from_number: str,
        chat_id: str,
        payload: Dict,
        raw_payload: Optional[Dict] = None,
        protocol_version: str = 'v1'
    ) -> WhatsAppMessage:
        """
        Processa uma mensagem recebida.
        
        Args:
            user_id: ID do usuário
            from_number: Número do remetente
            chat_id: ID do chat
            payload: Payload da mensagem
            
        Returns:
            WhatsAppMessage: Mensagem criada
        """
        session = await self._aget_session(user_id)
        
        if not session:
            raise RuntimeError(f"Sessão não encontrada para usuário {user_id}")
        
        message_id = payload.get('message_id', str(uuid.uuid4()))
        
        # Detectar se a mensagem é do agente
        is_from_agent = (
            from_number == 'agent_system' or 
            payload.get('sender_type') == 'agent' or
            payload.get('is_from_agent', False) or
            payload.get('is_from_me', False)
        )
        
        # Cria registro da mensagem no banco
        message = await self._acreate_message(
            session=session,
            message_id=message_id,
            direction='inbound',
            message_type=payload.get('type', 'text'),
            chat_id=chat_id,
            contact_number=from_number,
            contact_name=payload.get('contact_name', ''),
            text_content=payload.get('text', ''),
            media_url=payload.get('media_url', ''),
            media_mime_type=payload.get('mime_type', ''),
            media_size=payload.get('media_size'),
            payload=payload,
            raw_payload=raw_payload or payload,  # Usar raw_payload se fornecido
            protocol_version=protocol_version,
            is_from_me=is_from_agent,  # True se for do agente
            usuario_id=user_id,
            status='delivered'  # Mensagem recebida já está "delivered"
        )
        
        # Marca como entregue
        message.delivered_at = timezone.now()
        await self._asave_message(message, update_fields=['delivered_at'])
        
        # Atualiza contadores da sessão (async-safe)
        from asgiref.sync import sync_to_async
        await sync_to_async(session.increment_received_messages)()
        
        # Calcula latência
        latency_ms = message.total_latency_ms
        latency_ok = message.is_latency_acceptable
        
        logger.info(
            f"Mensagem {message_id} recebida de {from_number} "
            f"(usuário {user_id}) - Latência: {latency_ms}ms "
            f"({'OK' if latency_ok else 'ALTO'})"
        )
        
        if not latency_ok:
            logger.warning(
                f"Latência alta detectada: {latency_ms}ms > 5000ms "
                f"para mensagem {message_id}"
            )
        
        return message
    
    async def update_message_status(
        self,
        message_id: str,
        status: str
    ) -> Optional[WhatsAppMessage]:
        """
        Atualiza o status de uma mensagem.
        
        Args:
            message_id: ID da mensagem
            status: Novo status (sent, delivered, read, error)
            
        Returns:
            WhatsAppMessage ou None se não encontrada
        """
        try:
            message = await self._aget_message_by_id(message_id)
            
            if not message:
                logger.warning(f"Mensagem {message_id} não encontrada para atualizar status")
                return None
            
            # Atualiza status (async-safe)
            from asgiref.sync import sync_to_async
            if status == 'sent':
                await sync_to_async(message.mark_as_sent)()
            elif status == 'delivered':
                await sync_to_async(message.mark_as_delivered)()
            elif status == 'read':
                await sync_to_async(message.mark_as_read)()
            elif status == 'error':
                await sync_to_async(message.mark_as_error)("Erro no envio")
            else:
                message.status = status
                await self._asave_message(message, update_fields=['status'])
            
            latency_ms = message.total_latency_ms
            logger.info(
                f"Status da mensagem {message_id} atualizado para {status} "
                f"- Latência: {latency_ms}ms"
            )
            
            return message
        
        except Exception as e:
            logger.error(
                f"Erro ao atualizar status da mensagem {message_id}: {e}",
                exc_info=True
            )
            return None
    
    # Métodos auxiliares async para operações no banco
    
    async def _aget_or_create_session(self, user_id: int) -> WhatsAppSession:
        """Versão async de get_or_create_session"""
        from asgiref.sync import sync_to_async
        return await sync_to_async(self.get_or_create_session)(user_id)
    
    async def _aget_session(self, user_id: int) -> Optional[WhatsAppSession]:
        """Busca sessão ativa do usuário (async)"""
        from asgiref.sync import sync_to_async
        return await sync_to_async(
            lambda: WhatsAppSession.objects.filter(
                usuario_id=user_id, is_active=True
            ).first()
        )()
    
    async def _asave_session(self, session: WhatsAppSession, update_fields=None):
        """Salva sessão (async)"""
        from asgiref.sync import sync_to_async
        return await sync_to_async(session.save)(update_fields=update_fields)
    
    async def _acreate_message(self, **kwargs) -> WhatsAppMessage:
        """Cria mensagem (async)"""
        from asgiref.sync import sync_to_async
        return await sync_to_async(WhatsAppMessage.objects.create)(**kwargs)
    
    async def _asave_message(self, message: WhatsAppMessage, update_fields=None):
        """Salva mensagem (async)"""
        from asgiref.sync import sync_to_async
        return await sync_to_async(message.save)(update_fields=update_fields)
    
    async def _amark_message_error(self, message: WhatsAppMessage, error_msg: str):
        """Marca mensagem como erro (async)"""
        from asgiref.sync import sync_to_async
        return await sync_to_async(message.mark_as_error)(error_msg)
    
    async def _aget_message_by_id(self, message_id: str) -> Optional[WhatsAppMessage]:
        """Busca mensagem por ID (async)"""
        from asgiref.sync import sync_to_async
        return await sync_to_async(
            lambda: WhatsAppMessage.objects.filter(message_id=message_id).first()
        )()


# Instância global do serviço
_service = WhatsAppSessionService()


def get_whatsapp_session_service() -> WhatsAppSessionService:
    """Retorna a instância global do serviço"""
    return _service

