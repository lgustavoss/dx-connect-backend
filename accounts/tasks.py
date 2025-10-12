"""
Tasks Celery para accounts (Issue #51).
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task
def check_agent_presence_timeout():
    """
    Task periódica para marcar agentes como offline por timeout (Issue #51).
    
    Verifica heartbeat e marca como offline se sem atividade há mais de 2 minutos.
    """
    from accounts.models_presence import AgentPresence
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    logger.info("[Task] Verificando timeout de presença de agentes")
    
    timeout_threshold = timezone.now() - timedelta(minutes=2)
    
    # Busca agentes online sem heartbeat recente
    agents_to_timeout = AgentPresence.objects.filter(
        status__in=['online', 'busy', 'away'],
        last_heartbeat__lt=timeout_threshold
    )
    
    if not agents_to_timeout.exists():
        return {'agents_marked_offline': 0}
    
    marked_offline = 0
    channel_layer = get_channel_layer()
    
    for presence in agents_to_timeout:
        old_status = presence.status
        presence.mark_as_offline()
        
        logger.info(
            f"Agente {presence.agent.username} marcado como offline por timeout "
            f"(último heartbeat: {presence.last_heartbeat})"
        )
        
        # Emite evento WebSocket
        if channel_layer:
            event_payload = {
                "event": "agent_presence_changed",
                "data": {
                    "agent_id": presence.agent.id,
                    "status": "offline",
                    "message": "Desconectado por inatividade",
                    "timestamp": timezone.now().isoformat()
                },
                "version": "v1"
            }
            
            async_to_sync(channel_layer.group_send)(
                "agents_presence",
                {"type": "whatsapp.event", "event": event_payload}
            )
        
        marked_offline += 1
    
    logger.info(f"[Task] {marked_offline} agentes marcados como offline por timeout")
    
    return {'agents_marked_offline': marked_offline}

