"""
Serviço de distribuição automática de atendimentos (Issue #37).

Implementa lógica de atribuição inteligente de atendimentos para atendentes.
"""
import logging
from typing import Optional
from django.db import transaction
from django.utils import timezone

from .models import Departamento, FilaAtendimento, Atendimento

logger = logging.getLogger(__name__)


class DistribuicaoAtendimentoService:
    """
    Serviço de distribuição automática de atendimentos.
    
    Responsabilidades:
    - Adicionar cliente à fila
    - Atribuir automaticamente ao atendente disponível
    - Balancear carga entre atendentes
    - Respeitar prioridades
    """
    
    @staticmethod
    def adicionar_na_fila(
        departamento_id: int,
        cliente_id: int,
        chat_id: str,
        numero_whatsapp: str,
        mensagem_inicial: str = '',
        prioridade: str = 'normal'
    ) -> FilaAtendimento:
        """
        Adiciona cliente na fila de atendimento.
        
        Args:
            departamento_id: ID do departamento
            cliente_id: ID do cliente
            chat_id: ID do chat no WhatsApp
            numero_whatsapp: Número do WhatsApp
            mensagem_inicial: Primeira mensagem
            prioridade: Prioridade (baixa, normal, alta, urgente)
        
        Returns:
            FilaAtendimento criado
        """
        fila = FilaAtendimento.objects.create(
            departamento_id=departamento_id,
            cliente_id=cliente_id,
            chat_id=chat_id,
            numero_whatsapp=numero_whatsapp,
            mensagem_inicial=mensagem_inicial,
            prioridade=prioridade
        )
        
        logger.info(
            f"Cliente {cliente_id} adicionado à fila do departamento {departamento_id} "
            f"(prioridade: {prioridade})"
        )
        
        # Tenta distribuir automaticamente
        DistribuicaoAtendimentoService.distribuir_automaticamente(departamento_id)
        
        return fila
    
    @staticmethod
    def distribuir_automaticamente(departamento_id: int) -> int:
        """
        Distribui atendimentos pendentes para atendentes disponíveis.
        
        Args:
            departamento_id: ID do departamento
        
        Returns:
            Número de atendimentos distribuídos
        """
        try:
            departamento = Departamento.objects.get(id=departamento_id, ativo=True)
        except Departamento.DoesNotExist:
            logger.warning(f"Departamento {departamento_id} não encontrado ou inativo")
            return 0
        
        # Busca filas pendentes (ordenadas por prioridade e FIFO)
        filas_pendentes = FilaAtendimento.objects.filter(
            departamento=departamento,
            atribuido_em__isnull=True
        ).order_by('-prioridade', 'entrou_na_fila_em')
        
        if not filas_pendentes.exists():
            return 0
        
        # Busca atendentes disponíveis
        atendentes_disponiveis = departamento.get_atendentes_disponiveis()
        
        if not atendentes_disponiveis.exists():
            logger.info(f"Nenhum atendente disponível no departamento {departamento.nome}")
            return 0
        
        distribuidos = 0
        
        # Distribui usando round-robin
        for fila in filas_pendentes:
            # Pega atendente com menos atendimentos ativos
            atendente = atendentes_disponiveis.order_by('atendimentos_ativos').first()
            
            if not atendente:
                break
            
            # Cria atendimento e atribui
            with transaction.atomic():
                atendimento = Atendimento.objects.create(
                    departamento=departamento,
                    cliente=fila.cliente,
                    chat_id=fila.chat_id,
                    numero_whatsapp=fila.numero_whatsapp,
                    prioridade=fila.prioridade,
                    status='aguardando'
                )
                
                # Atribui atendente
                atendimento.atribuir_atendente(atendente)
                
                # Marca fila como atribuída
                fila.atribuido_em = timezone.now()
                fila.save(update_fields=['atribuido_em'])
                
                distribuidos += 1
                
                logger.info(
                    f"Atendimento {atendimento.id} atribuído a {atendente.username} "
                    f"(departamento: {departamento.nome}, cliente: {fila.cliente.razao_social})"
                )
            
            # Atualiza contagem de atendentes disponíveis
            atendentes_disponiveis = departamento.get_atendentes_disponiveis()
            
            if not atendentes_disponiveis.exists():
                break
        
        if distribuidos > 0:
            logger.info(f"{distribuidos} atendimentos distribuídos no departamento {departamento.nome}")
        
        return distribuidos
    
    @staticmethod
    def atribuir_manualmente(
        fila_id: int,
        atendente_id: int
    ) -> Optional[Atendimento]:
        """
        Atribui atendimento manualmente a um atendente específico.
        
        Args:
            fila_id: ID da fila
            atendente_id: ID do atendente
        
        Returns:
            Atendimento criado ou None
        """
        try:
            fila = FilaAtendimento.objects.get(id=fila_id, atribuido_em__isnull=True)
        except FilaAtendimento.DoesNotExist:
            logger.warning(f"Fila {fila_id} não encontrada ou já atribuída")
            return None
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            atendente = User.objects.get(id=atendente_id, is_active=True)
        except User.DoesNotExist:
            logger.warning(f"Atendente {atendente_id} não encontrado ou inativo")
            return None
        
        with transaction.atomic():
            # Cria atendimento
            atendimento = Atendimento.objects.create(
                departamento=fila.departamento,
                cliente=fila.cliente,
                chat_id=fila.chat_id,
                numero_whatsapp=fila.numero_whatsapp,
                prioridade=fila.prioridade,
                status='aguardando'
            )
            
            # Atribui atendente
            atendimento.atribuir_atendente(atendente)
            
            # Marca fila como atribuída
            fila.atribuido_em = timezone.now()
            fila.save(update_fields=['atribuido_em'])
            
            logger.info(
                f"Atendimento {atendimento.id} atribuído manualmente a {atendente.username}"
            )
        
        return atendimento


def get_distribuicao_service() -> DistribuicaoAtendimentoService:
    """Retorna instância do serviço de distribuição"""
    return DistribuicaoAtendimentoService()

