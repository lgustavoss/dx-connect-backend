"""
Tarefas Celery para envio de mensagens WhatsApp (Issue #45).

Implementa fila de envio com retentativas automáticas.
"""
import logging
from typing import Dict, Optional
from celery import shared_task
from django.utils import timezone
from django.db import models
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minuto entre retentativas
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # Máximo 10 minutos
    retry_jitter=True
)
def send_whatsapp_message_task(
    self,
    user_id: int,
    to: str,
    payload: Dict,
    message_db_id: Optional[int] = None,
    client_message_id: Optional[str] = None
):
    """
    Task Celery para enviar mensagem WhatsApp com retentativas.
    
    Args:
        self: Instância da task (bind=True)
        user_id: ID do usuário que está enviando
        to: Número do destinatário
        payload: Payload da mensagem (type, text, media_url, etc)
        message_db_id: ID da mensagem no banco (para atualizar status)
        client_message_id: ID personalizado do cliente
    
    Returns:
        Dict com resultado do envio
    """
    from whatsapp.service import get_whatsapp_session_service
    from whatsapp.models import WhatsAppMessage
    
    logger.info(
        f"[Task] Enviando mensagem para {to} (usuário: {user_id}, "
        f"tentativa: {self.request.retries + 1}/{self.max_retries + 1})"
    )
    
    try:
        # Busca mensagem no banco se ID foi fornecido
        message_obj = None
        if message_db_id:
            try:
                message_obj = WhatsAppMessage.objects.get(id=message_db_id)
            except WhatsAppMessage.DoesNotExist:
                logger.warning(f"Mensagem {message_db_id} não encontrada no banco")
        
        # Envia via serviço
        service = get_whatsapp_session_service()
        result = async_to_sync(service.send_message)(
            user_id=user_id,
            to=to,
            payload=payload,
            client_message_id=client_message_id
        )
        
        # Atualiza status no banco se mensagem existe
        if message_obj:
            message_obj.status = 'queued'
            message_obj.save(update_fields=['status'])
        
        # Emite evento WebSocket de confirmação
        _emit_message_sent_event(
            user_id=user_id,
            message_id=result.get('message_id'),
            status='queued',
            to=to
        )
        
        logger.info(
            f"[Task] Mensagem enviada com sucesso: {result.get('message_id')} "
            f"(tentativa: {self.request.retries + 1})"
        )
        
        return {
            'success': True,
            'message_id': result.get('message_id'),
            'database_id': result.get('database_id'),
            'retries': self.request.retries
        }
    
    except Exception as e:
        logger.error(
            f"[Task] Erro ao enviar mensagem (tentativa {self.request.retries + 1}): {e}",
            exc_info=True
        )
        
        # Marca mensagem como erro se excedeu retentativas
        if self.request.retries >= self.max_retries:
            if message_db_id:
                try:
                    message_obj = WhatsAppMessage.objects.get(id=message_db_id)
                    message_obj.mark_as_error(f"Falha após {self.max_retries + 1} tentativas: {str(e)}")
                except WhatsAppMessage.DoesNotExist:
                    pass
            
            # Emite evento de falha
            _emit_message_sent_event(
                user_id=user_id,
                message_id=client_message_id or 'unknown',
                status='failed',
                to=to,
                error=str(e)
            )
            
            logger.error(
                f"[Task] Mensagem falhou definitivamente após {self.max_retries + 1} tentativas"
            )
        
        # Re-lança exceção para Celery fazer retry
        raise


def _emit_message_sent_event(
    user_id: int,
    message_id: str,
    status: str,
    to: str,
    error: Optional[str] = None
):
    """
    Emite evento WebSocket de confirmação de envio (Issue #45).
    
    Formato do evento:
    {
        "event": "message_sent",
        "data": {
            "message_id": "abc123",
            "status": "queued",
            "to": "5511999999999",
            "timestamp": "2025-10-11T18:00:00Z",
            "error": null
        },
        "version": "v1"
    }
    """
    channel_layer = get_channel_layer()
    
    if not channel_layer:
        logger.warning("Channel layer não disponível para emitir evento message_sent")
        return
    
    event_payload = {
        "event": "message_sent",
        "data": {
            "message_id": message_id,
            "status": status,
            "to": to,
            "timestamp": timezone.now().isoformat(),
            "error": error
        },
        "version": "v1"
    }
    
    try:
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}_whatsapp",
            {"type": "whatsapp.event", "event": event_payload}
        )
        
        logger.debug(f"Evento message_sent emitido: {message_id} (status: {status})")
    
    except Exception as e:
        logger.error(f"Erro ao emitir evento message_sent: {e}", exc_info=True)


@shared_task
def cleanup_old_message_queue():
    """
    Task periódica para limpar mensagens antigas da fila.
    
    Remove mensagens com erro ou falha após 7 dias.
    """
    from whatsapp.models import WhatsAppMessage
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=7)
    
    deleted_count = WhatsAppMessage.objects.filter(
        status__in=['error', 'failed'],
        created_at__lt=cutoff_date
    ).delete()[0]
    
    if deleted_count > 0:
        logger.info(f"Limpeza: {deleted_count} mensagens antigas removidas")
    
    return {'deleted_count': deleted_count}


# ==================== TASKS DE PROCESSAMENTO DE MÍDIA (Issue #46) ====================

@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=120
)
def process_media_task(self, media_file_id: int):
    """
    Task Celery para processar mídia (download + conversão + thumbnail).
    
    Args:
        self: Instância da task (bind=True)
        media_file_id: ID do MediaFile para processar
    """
    from whatsapp.media import MediaFile
    from whatsapp.media_service import get_media_processing_service
    
    logger.info(f"[Task] Processando mídia ID {media_file_id}")
    
    try:
        media_file = MediaFile.objects.get(id=media_file_id)
        service = get_media_processing_service()
        
        # Processa mídia (thumbnail + conversão)
        success = service.process_media(media_file)
        
        if success:
            logger.info(f"[Task] Mídia {media_file_id} processada com sucesso")
            return {'success': True, 'media_file_id': media_file_id}
        else:
            logger.error(f"[Task] Falha ao processar mídia {media_file_id}")
            raise Exception("Falha no processamento")
    
    except MediaFile.DoesNotExist:
        logger.error(f"[Task] MediaFile {media_file_id} não encontrado")
        return {'success': False, 'error': 'not_found'}
    
    except Exception as e:
        logger.error(f"[Task] Erro ao processar mídia {media_file_id}: {e}", exc_info=True)
        raise


@shared_task
def cleanup_orphan_media_files():
    """
    Task periódica para limpar arquivos de mídia órfãos (Issue #46).
    
    Remove:
    - Mídias com erro após 3 dias
    - Mídias não acessadas há mais de 90 dias
    """
    from whatsapp.media import MediaFile
    from datetime import timedelta
    import os
    
    logger.info("[Task] Iniciando limpeza de mídias órfãs")
    
    cutoff_error = timezone.now() - timedelta(days=3)
    cutoff_unused = timezone.now() - timedelta(days=90)
    
    # Busca mídias para remover
    to_delete = MediaFile.objects.filter(
        models.Q(status='error', created_at__lt=cutoff_error) |
        models.Q(last_accessed_at__lt=cutoff_unused)
    )
    
    deleted_count = 0
    freed_space = 0
    
    for media in to_delete:
        # Calcula espaço antes de deletar
        if media.file_size:
            freed_space += media.file_size
        
        # Remove arquivos físicos
        try:
            if media.original_file:
                media.original_file.delete(save=False)
            if media.converted_file:
                media.converted_file.delete(save=False)
            if media.thumbnail_file:
                media.thumbnail_file.delete(save=False)
        except Exception as e:
            logger.warning(f"Erro ao remover arquivos de {media.file_id}: {e}")
        
        # Remove registro do banco
        media.delete()
        deleted_count += 1
    
    freed_space_mb = round(freed_space / (1024 * 1024), 2)
    
    if deleted_count > 0:
        logger.info(
            f"[Task] Limpeza concluída: {deleted_count} mídias removidas, "
            f"{freed_space_mb} MB liberados"
        )
    
    return {
        'deleted_count': deleted_count,
        'freed_space_mb': freed_space_mb
    }

