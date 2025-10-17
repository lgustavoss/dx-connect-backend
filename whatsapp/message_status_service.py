"""
Serviço para gerenciar status de mensagens WhatsApp
"""
import logging
from typing import Optional, List
from django.utils import timezone
from django.db import transaction
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from .models import WhatsAppMessage

logger = logging.getLogger(__name__)


class MessageStatusService:
    """Serviço para gerenciar status de mensagens"""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    async def update_message_status(
        self, 
        message_id: str, 
        status: str, 
        error_message: str = '',
        failure_reason: str = ''
    ) -> Optional[WhatsAppMessage]:
        """
        Atualiza status de uma mensagem e notifica via WebSocket
        
        Args:
            message_id: ID da mensagem
            status: Novo status ('sending', 'sent', 'delivered', 'read', 'failed', 'error')
            error_message: Mensagem de erro (se aplicável)
            failure_reason: Motivo da falha (se aplicável)
            
        Returns:
            WhatsAppMessage atualizada ou None se não encontrada
        """
        try:
            message = await sync_to_async(WhatsAppMessage.objects.get)(
                message_id=message_id
            )
            
            # Atualizar status baseado no tipo
            if status == 'sending':
                message.mark_as_sending()
            elif status == 'sent':
                message.mark_as_sent()
            elif status == 'delivered':
                message.mark_as_delivered()
            elif status == 'read':
                message.mark_as_read()
            elif status == 'failed':
                message.mark_as_failed(error_message, failure_reason)
            elif status == 'error':
                message.mark_as_error(error_message, failure_reason)
            
            # Notificar via WebSocket
            await self._notify_status_change(message)
            
            logger.info(f"Status da mensagem {message_id} atualizado para {status}")
            return message
            
        except WhatsAppMessage.DoesNotExist:
            logger.error(f"Mensagem {message_id} não encontrada")
            return None
        except Exception as e:
            logger.error(f"Erro ao atualizar status da mensagem {message_id}: {e}")
            return None
    
    async def mark_as_read_by_chat(self, chat_id: str) -> int:
        """
        Marca todas as mensagens não lidas de um chat como lidas
        
        Args:
            chat_id: ID do chat
            
        Returns:
            Número de mensagens marcadas como lidas
        """
        try:
            # Buscar mensagens não lidas do agente neste chat
            messages = await sync_to_async(list)(
                WhatsAppMessage.objects.filter(
                    chat_id=chat_id,
                    direction='outbound',
                    status__in=['sent', 'delivered']
                )
            )
            
            count = 0
            for message in messages:
                message.mark_as_read()
                await self._notify_status_change(message)
                count += 1
            
            logger.info(f"{count} mensagens marcadas como lidas no chat {chat_id}")
            return count
            
        except Exception as e:
            logger.error(f"Erro ao marcar mensagens como lidas no chat {chat_id}: {e}")
            return 0
    
    async def retry_failed_messages(self) -> int:
        """
        Tenta reenviar mensagens que falharam
        
        Returns:
            Número de mensagens que serão reenviadas
        """
        try:
            # Buscar mensagens que precisam de retry
            messages = await sync_to_async(list)(
                WhatsAppMessage.objects.filter(
                    status__in=['failed', 'error'],
                    retry_count__lt=models.F('max_retries')
                )
            )
            
            count = 0
            for message in messages:
                if message.needs_retry:
                    message.increment_retry()
                    await self._notify_status_change(message)
                    count += 1
                    
                    # Aqui você pode adicionar lógica para reenviar a mensagem
                    # Por exemplo, chamar o serviço de envio do WhatsApp
                    await self._retry_send_message(message)
            
            logger.info(f"{count} mensagens marcadas para retry")
            return count
            
        except Exception as e:
            logger.error(f"Erro ao processar retry de mensagens: {e}")
            return 0
    
    async def get_message_stats(self, user_id: int = None) -> dict:
        """
        Obtém estatísticas de mensagens
        
        Args:
            user_id: ID do usuário (opcional, filtra por usuário)
            
        Returns:
            Dicionário com estatísticas
        """
        try:
            from django.db.models import Count, Q
            
            queryset = WhatsAppMessage.objects.all()
            if user_id:
                queryset = queryset.filter(usuario_id=user_id)
            
            stats = await sync_to_async(queryset.aggregate)(
                total=Count('id'),
                sent=Count('id', filter=Q(status='sent')),
                delivered=Count('id', filter=Q(status='delivered')),
                read=Count('id', filter=Q(status='read')),
                failed=Count('id', filter=Q(status='failed')),
                error=Count('id', filter=Q(status='error')),
                queued=Count('id', filter=Q(status='queued')),
                sending=Count('id', filter=Q(status='sending')),
                retrying=Count('id', filter=Q(status='retrying')),
            )
            
            # Calcular taxas
            total = stats['total']
            if total > 0:
                stats['delivery_rate'] = round((stats['delivered'] / total) * 100, 2)
                stats['read_rate'] = round((stats['read'] / total) * 100, 2)
                stats['failure_rate'] = round(((stats['failed'] + stats['error']) / total) * 100, 2)
            else:
                stats['delivery_rate'] = 0
                stats['read_rate'] = 0
                stats['failure_rate'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de mensagens: {e}")
            return {}
    
    async def _notify_status_change(self, message: WhatsAppMessage) -> None:
        """
        Notifica mudança de status via WebSocket
        
        Args:
            message: Mensagem com status atualizado
        """
        try:
            # Preparar dados da notificação
            notification_data = {
                'type': 'message_status_update',
                'message_id': message.message_id,
                'chat_id': message.chat_id,
                'status': message.status,
                'status_display': message.get_status_display(),
                'timestamp': message.updated_at.isoformat(),
                'retry_count': message.retry_count,
                'error_message': message.error_message,
                'failure_reason': message.failure_reason,
            }
            
            # Enviar para o grupo do usuário
            user_group = f"user_{message.usuario_id}_whatsapp"
            await self.channel_layer.group_send(
                user_group,
                {
                    'type': 'whatsapp_message_status',
                    'data': notification_data
                }
            )
            
            # Enviar para o grupo específico do chat (se houver atendimento ativo)
            chat_group = f"chat_{message.chat_id}"
            await self.channel_layer.group_send(
                chat_group,
                {
                    'type': 'whatsapp_message_status',
                    'data': notification_data
                }
            )
            
        except Exception as e:
            logger.error(f"Erro ao notificar mudança de status: {e}")
    
    async def _retry_send_message(self, message: WhatsAppMessage) -> None:
        """
        Tenta reenviar uma mensagem (placeholder para integração com WhatsApp)
        
        Args:
            message: Mensagem para reenviar
        """
        try:
            # Aqui você implementaria a lógica de reenvio
            # Por exemplo, chamar o serviço de envio do WhatsApp
            logger.info(f"Tentando reenviar mensagem {message.message_id}")
            
            # Placeholder - implementar integração com WhatsApp
            # await whatsapp_service.send_message(message)
            
        except Exception as e:
            logger.error(f"Erro ao reenviar mensagem {message.message_id}: {e}")


# Instância global do serviço
_message_status_service = MessageStatusService()


def get_message_status_service() -> MessageStatusService:
    """Retorna a instância global do serviço de status"""
    return _message_status_service
