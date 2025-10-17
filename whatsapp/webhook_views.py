"""
Views para webhooks do WhatsApp
"""
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
import json

from .message_status_service import get_message_status_service

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """
    Webhook para receber confirmações de status do WhatsApp
    """
    
    def post(self, request):
        """
        Processa webhook do WhatsApp
        
        Tipos de eventos suportados:
        - message_status: Confirmação de status (enviado, entregue, lido)
        - message_read: Confirmação de leitura
        - message_delivered: Confirmação de entrega
        - message_failed: Falha no envio
        """
        try:
            data = json.loads(request.body)
            event_type = data.get('type', '')
            
            logger.info(f"Webhook recebido: {event_type}")
            logger.debug(f"Dados do webhook: {data}")
            
            if event_type == 'message_status':
                return await self._handle_message_status(data)
            elif event_type == 'message_read':
                return await self._handle_message_read(data)
            elif event_type == 'message_delivered':
                return await self._handle_message_delivered(data)
            elif event_type == 'message_failed':
                return await self._handle_message_failed(data)
            else:
                logger.warning(f"Tipo de evento não suportado: {event_type}")
                return JsonResponse({'error': 'Event type not supported'}, status=400)
                
        except json.JSONDecodeError:
            logger.error("Erro ao decodificar JSON do webhook")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    async def _handle_message_status(self, data):
        """Processa confirmação de status de mensagem"""
        try:
            message_id = data.get('message_id')
            status = data.get('status')
            error_message = data.get('error_message', '')
            failure_reason = data.get('failure_reason', '')
            
            if not message_id or not status:
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            service = get_message_status_service()
            message = await service.update_message_status(
                message_id=message_id,
                status=status,
                error_message=error_message,
                failure_reason=failure_reason
            )
            
            if message:
                return JsonResponse({
                    'success': True,
                    'message_id': message_id,
                    'status': status
                })
            else:
                return JsonResponse({'error': 'Message not found'}, status=404)
                
        except Exception as e:
            logger.error(f"Erro ao processar status da mensagem: {e}")
            return JsonResponse({'error': 'Failed to update message status'}, status=500)
    
    async def _handle_message_read(self, data):
        """Processa confirmação de leitura de mensagem"""
        try:
            message_id = data.get('message_id')
            chat_id = data.get('chat_id')
            
            if not message_id and not chat_id:
                return JsonResponse({'error': 'Missing message_id or chat_id'}, status=400)
            
            service = get_message_status_service()
            
            if message_id:
                # Marcar mensagem específica como lida
                message = await service.update_message_status(
                    message_id=message_id,
                    status='read'
                )
                if not message:
                    return JsonResponse({'error': 'Message not found'}, status=404)
            else:
                # Marcar todas as mensagens do chat como lidas
                count = await service.mark_as_read_by_chat(chat_id)
                return JsonResponse({
                    'success': True,
                    'chat_id': chat_id,
                    'messages_marked_as_read': count
                })
            
            return JsonResponse({
                'success': True,
                'message_id': message_id,
                'status': 'read'
            })
            
        except Exception as e:
            logger.error(f"Erro ao processar leitura da mensagem: {e}")
            return JsonResponse({'error': 'Failed to mark message as read'}, status=500)
    
    async def _handle_message_delivered(self, data):
        """Processa confirmação de entrega de mensagem"""
        try:
            message_id = data.get('message_id')
            
            if not message_id:
                return JsonResponse({'error': 'Missing message_id'}, status=400)
            
            service = get_message_status_service()
            message = await service.update_message_status(
                message_id=message_id,
                status='delivered'
            )
            
            if message:
                return JsonResponse({
                    'success': True,
                    'message_id': message_id,
                    'status': 'delivered'
                })
            else:
                return JsonResponse({'error': 'Message not found'}, status=404)
                
        except Exception as e:
            logger.error(f"Erro ao processar entrega da mensagem: {e}")
            return JsonResponse({'error': 'Failed to mark message as delivered'}, status=500)
    
    async def _handle_message_failed(self, data):
        """Processa falha no envio de mensagem"""
        try:
            message_id = data.get('message_id')
            error_message = data.get('error_message', 'Falha no envio')
            failure_reason = data.get('failure_reason', 'unknown')
            
            if not message_id:
                return JsonResponse({'error': 'Missing message_id'}, status=400)
            
            service = get_message_status_service()
            message = await service.update_message_status(
                message_id=message_id,
                status='failed',
                error_message=error_message,
                failure_reason=failure_reason
            )
            
            if message:
                return JsonResponse({
                    'success': True,
                    'message_id': message_id,
                    'status': 'failed',
                    'retry_count': message.retry_count,
                    'can_retry': message.can_retry()
                })
            else:
                return JsonResponse({'error': 'Message not found'}, status=404)
                
        except Exception as e:
            logger.error(f"Erro ao processar falha da mensagem: {e}")
            return JsonResponse({'error': 'Failed to mark message as failed'}, status=500)


@require_http_methods(["GET"])
def webhook_health_check(request):
    """Health check para o webhook"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'whatsapp_webhook',
        'timestamp': timezone.now().isoformat()
    })
