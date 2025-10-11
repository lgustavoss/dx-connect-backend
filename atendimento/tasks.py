"""
Tasks Celery para sistema de atendimento (Issue #40).
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task
def encerrar_atendimentos_inativos():
    """
    Task periódica para encerrar atendimentos inativos automaticamente (Issue #40).
    
    Usa configuração timeout_inatividade_minutos do chat_settings.
    """
    from atendimento.models import Atendimento
    from core.models import Config
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    logger.info("[Task] Verificando atendimentos inativos para encerramento automático")
    
    try:
        # Busca configuração de timeout
        config = Config.objects.first()
        if not config:
            logger.warning("Configuração não encontrada, usando timeout padrão de 30 minutos")
            timeout_minutos = 30
        else:
            chat_settings = config.chat_settings or {}
            timeout_minutos = chat_settings.get('timeout_inatividade_minutos', 30)
        
        # Calcula data de corte
        cutoff_time = timezone.now() - timedelta(minutes=timeout_minutos)
        
        # Busca atendimentos inativos
        atendimentos_inativos = Atendimento.objects.filter(
            status='em_atendimento',
            atualizado_em__lt=cutoff_time
        ).select_related('cliente', 'atendente')
        
        if not atendimentos_inativos.exists():
            logger.info("[Task] Nenhum atendimento inativo encontrado")
            return {'encerrados': 0}
        
        encerrados = 0
        channel_layer = get_channel_layer()
        
        for atendimento in atendimentos_inativos:
            try:
                # Calcula tempo de inatividade
                tempo_inativo_minutos = int(
                    (timezone.now() - atendimento.atualizado_em).total_seconds() / 60
                )
                
                # Mensagem de encerramento
                observacoes = (
                    f"Encerrado automaticamente por inatividade "
                    f"({tempo_inativo_minutos} minutos sem interação)"
                )
                
                # Finaliza atendimento
                atendimento.finalizar(observacoes)
                
                logger.info(
                    f"Atendimento {atendimento.id} encerrado automaticamente "
                    f"(cliente: {atendimento.cliente.razao_social}, "
                    f"inatividade: {tempo_inativo_minutos}min)"
                )
                
                # Emite evento WebSocket
                if channel_layer and atendimento.atendente:
                    event_payload = {
                        "event": "chat_auto_closed",
                        "data": {
                            "atendimento_id": atendimento.id,
                            "cliente_nome": atendimento.cliente.razao_social,
                            "chat_id": atendimento.chat_id,
                            "motivo": "inatividade",
                            "tempo_inativo_minutos": tempo_inativo_minutos,
                            "timestamp": timezone.now().isoformat()
                        },
                        "version": "v1"
                    }
                    
                    async_to_sync(channel_layer.group_send)(
                        f"user_{atendimento.atendente.id}_whatsapp",
                        {"type": "whatsapp.event", "event": event_payload}
                    )
                
                encerrados += 1
            
            except Exception as e:
                logger.error(
                    f"Erro ao encerrar atendimento {atendimento.id}: {e}",
                    exc_info=True
                )
        
        logger.info(
            f"[Task] Encerramento automático concluído: {encerrados} atendimentos encerrados "
            f"(timeout: {timeout_minutos}min)"
        )
        
        return {
            'encerrados': encerrados,
            'timeout_minutos': timeout_minutos
        }
    
    except Exception as e:
        logger.error(f"[Task] Erro no encerramento automático: {e}", exc_info=True)
        raise

