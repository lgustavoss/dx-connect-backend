"""
Serviço para gerenciamento de chats e auto-criação de filas (Issue #85).
"""
import logging
from django.utils import timezone
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from atendimento.models import Atendimento, FilaAtendimento, Departamento
from clientes.models import Cliente, ContatoCliente
from whatsapp.models import WhatsAppMessage

logger = logging.getLogger(__name__)


class ChatService:
    """
    Serviço para gerenciar lógica de chats e conversas.
    """
    
    @staticmethod
    def processar_nova_mensagem_recebida(mensagem: WhatsAppMessage):
        """
        Processa uma nova mensagem recebida (inbound).
        
        Verifica se:
        1. Já existe atendimento ativo para este chat_id
        2. Se não existe, cria Fila + Atendimento automaticamente
        3. Emite evento WebSocket para alertar atendentes
        
        Args:
            mensagem: Instância de WhatsAppMessage
        """
        # Só processa mensagens recebidas
        if mensagem.direction != 'inbound':
            return
        
        chat_id = mensagem.chat_id
        numero = mensagem.contact_number
        
        logger.info(f"Processando nova mensagem recebida de {numero} (chat: {chat_id})")
        
        # Verificar se já existe atendimento ativo
        atendimento_existente = Atendimento.objects.filter(
            chat_id=chat_id,
            status__in=['aguardando', 'em_atendimento', 'pausado']
        ).first()
        
        if atendimento_existente:
            logger.debug(f"Chat {chat_id} já tem atendimento ativo (ID: {atendimento_existente.id})")
            # Atualizar contador de mensagens
            atendimento_existente.total_mensagens_cliente += 1
            atendimento_existente.save(update_fields=['total_mensagens_cliente', 'atualizado_em'])
            
            # Emitir evento de nova mensagem (para atualizar badge)
            ChatService._emit_new_message_event(atendimento_existente, mensagem)
            return
        
        # Nova conversa - criar atendimento
        logger.info(f"Nova conversa detectada para {numero} (chat: {chat_id})")
        
        with transaction.atomic():
            # Buscar ou criar cliente pelo número
            cliente = ChatService._get_or_create_cliente_by_numero(numero, mensagem.contact_name)
            
            # Buscar departamento padrão
            departamento = ChatService._get_departamento_padrao()
            
            # Criar atendimento
            atendimento = Atendimento.objects.create(
                departamento=departamento,
                cliente=cliente,
                chat_id=chat_id,
                numero_whatsapp=numero,
                status='aguardando',
                prioridade='normal',
                total_mensagens_cliente=1
            )
            
            # Adicionar à fila
            fila = FilaAtendimento.objects.create(
                departamento=departamento,
                cliente=cliente,
                chat_id=chat_id,
                numero_whatsapp=numero,
                mensagem_inicial=mensagem.text_content[:500] if mensagem.text_content else '',
                prioridade='normal'
            )
            
            logger.info(
                f"Atendimento criado (ID: {atendimento.id}) e adicionado à fila "
                f"(ID: {fila.id}) para chat {chat_id}"
            )
            
            # Emitir evento de NOVO CHAT (com alerta sonoro)
            ChatService._emit_new_chat_event(atendimento, mensagem)
    
    @staticmethod
    def _get_or_create_cliente_by_numero(numero: str, nome: str = None):
        """
        Busca ou cria cliente pelo número de WhatsApp.
        """
        # Buscar contato existente (ContatoCliente não tem campo telefone, apenas whatsapp)
        contato = ContatoCliente.objects.filter(whatsapp=numero).first()
        
        if contato and contato.cliente:
            return contato.cliente
        
        # Buscar cliente pelo telefone principal
        cliente = Cliente.objects.filter(telefone_principal=numero).first()
        
        if cliente:
            return cliente
        
        # Criar novo cliente "temporário"
        nome_cliente = nome or f"Cliente {numero}"
        
        # Gerar CNPJ único temporário baseado no timestamp
        import time
        timestamp = str(int(time.time() * 1000))[-11:]  # Últimos 11 dígitos
        cnpj_temp = f"{timestamp[:2]}.{timestamp[2:5]}.{timestamp[5:8]}/{timestamp[8:12]}-{timestamp[-2:]}"
        
        cliente = Cliente.objects.create(
            razao_social=nome_cliente,
            cnpj=cnpj_temp,
            telefone_principal=numero,
            status='ativo'
        )
        
        logger.info(f"Cliente temporário criado: {cliente.razao_social} (ID: {cliente.id})")
        return cliente
    
    @staticmethod
    def _get_departamento_padrao():
        """
        Retorna departamento padrão ou cria um se não existir.
        """
        departamento = Departamento.objects.filter(ativo=True).first()
        
        if not departamento:
            departamento = Departamento.objects.create(
                nome='Suporte',
                descricao='Departamento padrão',
                cor='#3B82F6',
                ativo=True
            )
            logger.info("Departamento padrão criado: Suporte")
        
        return departamento
    
    @staticmethod
    def _emit_new_chat_event(atendimento: Atendimento, mensagem: WhatsAppMessage):
        """
        Emite evento WebSocket de NOVO CHAT para todos os atendentes.
        
        Evento inclui flag de alerta sonoro.
        """
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        event_data = {
            'event': 'new_chat',
            'play_sound': True,  # Alerta sonoro!
            'data': {
                'chat_id': atendimento.chat_id,
                'atendimento_id': atendimento.id,
                'numero_whatsapp': atendimento.numero_whatsapp,
                'cliente_id': atendimento.cliente_id,
                'cliente_nome': atendimento.cliente.razao_social,
                'departamento_id': atendimento.departamento_id,
                'departamento_nome': atendimento.departamento.nome,
                'mensagem_inicial': mensagem.text_content[:200] if mensagem.text_content else '',
                'criado_em': atendimento.criado_em.isoformat(),
                'prioridade': atendimento.prioridade
            }
        }
        
        # Enviar para grupo de atendentes
        async_to_sync(channel_layer.group_send)(
            'atendentes',
            {
                'type': 'chat.event',
                **event_data
            }
        )
        
        logger.info(f"Evento 'new_chat' emitido para chat {atendimento.chat_id}")
    
    @staticmethod
    def _emit_new_message_event(atendimento: Atendimento, mensagem: WhatsAppMessage):
        """
        Emite evento WebSocket de NOVA MENSAGEM (chat existente).
        """
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        event_data = {
            'event': 'new_message',
            'play_sound': False,  # Sem alerta (chat já existe)
            'data': {
                'chat_id': atendimento.chat_id,
                'atendimento_id': atendimento.id,
                'message_id': mensagem.message_id,
                'texto': mensagem.text_content[:200] if mensagem.text_content else '',
                'tipo': mensagem.message_type,
                'de': mensagem.contact_name or mensagem.contact_number,
                'criado_em': mensagem.created_at.isoformat()
            }
        }
        
        # Enviar para atendente responsável (se houver)
        if atendimento.atendente:
            async_to_sync(channel_layer.group_send)(
                f'user_{atendimento.atendente_id}',
                {
                    'type': 'chat.event',
                    **event_data
                }
            )


# Instância global do serviço
_service = ChatService()


def get_chat_service() -> ChatService:
    """Retorna instância global do serviço"""
    return _service


# Import necessário para usar Q
from django.db.models import Q

