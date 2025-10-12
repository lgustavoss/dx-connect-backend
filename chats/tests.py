"""
Testes para API de Chats (Issue #85).
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from atendimento.models import Atendimento, Departamento, FilaAtendimento
from clientes.models import Cliente
from whatsapp.models import WhatsAppSession, WhatsAppMessage
from chats.service import ChatService

User = get_user_model()


class ChatAPITests(TestCase):
    """Testes para endpoints de Chat"""
    
    def setUp(self):
        """Configuração inicial"""
        self.client = APIClient()
        
        # Criar usuários
        self.atendente1 = User.objects.create_user(
            username='atendente1',
            password='pass123',
            display_name='Atendente 1'
        )
        self.atendente2 = User.objects.create_user(
            username='atendente2',
            password='pass123',
            display_name='Atendente 2'
        )
        
        # Criar departamento
        self.departamento = Departamento.objects.create(
            nome='Suporte',
            cor='#3B82F6',
            ativo=True
        )
        self.departamento.atendentes.add(self.atendente1, self.atendente2)
        
        # Criar cliente
        self.cliente = Cliente.objects.create(
            razao_social='Cliente Teste',
            cnpj='12.345.678/0001-90',
            telefone_principal='5511999999999',
            status='ativo'
        )
        
        # Criar sessão WhatsApp
        self.session = WhatsAppSession.objects.create(
            usuario=self.atendente1,
            status='ready',
            is_active=True
        )
        
        self.client.force_authenticate(user=self.atendente1)
    
    def test_list_chats_empty(self):
        """Testa listagem de chats vazia"""
        response = self.client.get('/api/v1/chats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_list_chats_with_data(self):
        """Testa listagem de chats com dados"""
        # Criar atendimento
        atendimento = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            atendente=self.atendente1,
            chat_id='5511999999999',
            numero_whatsapp='5511999999999',
            status='em_atendimento'
        )
        
        # Criar mensagem
        WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.atendente1,
            message_id='msg_1',
            direction='inbound',
            message_type='text',
            chat_id='5511999999999',
            contact_number='5511999999999',
            text_content='Olá!',
            status='delivered'
        )
        
        response = self.client.get('/api/v1/chats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['chat_id'], '5511999999999')
        self.assertEqual(response.data[0]['status'], 'em_atendimento')
    
    def test_retrieve_chat(self):
        """Testa busca de um chat específico"""
        atendimento = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            atendente=self.atendente1,
            chat_id='5511999999999',
            numero_whatsapp='5511999999999',
            status='em_atendimento'
        )
        
        response = self.client.get(f'/api/v1/chats/{atendimento.chat_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['chat_id'], '5511999999999')
        self.assertEqual(response.data['cliente_nome'], 'Cliente Teste')
    
    def test_get_chat_messages(self):
        """Testa listagem de mensagens de um chat"""
        atendimento = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            atendente=self.atendente1,
            chat_id='5511999999999',
            numero_whatsapp='5511999999999',
            status='em_atendimento'
        )
        
        # Criar mensagens
        for i in range(3):
            WhatsAppMessage.objects.create(
                session=self.session,
                usuario=self.atendente1,
                message_id=f'msg_{i}',
                direction='inbound',
                message_type='text',
                chat_id='5511999999999',
                contact_number='5511999999999',
                text_content=f'Mensagem {i}',
                status='delivered'
            )
        
        response = self.client.get(f'/api/v1/chats/{atendimento.chat_id}/messages/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 3)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_aceitar_chat(self):
        """Testa aceitar um chat em espera"""
        atendimento = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            chat_id='5511999999999',
            numero_whatsapp='5511999999999',
            status='aguardando'
        )
        
        response = self.client.post(
            f'/api/v1/chats/{atendimento.chat_id}/aceitar/',
            {}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.status, 'em_atendimento')
        self.assertEqual(atendimento.atendente, self.atendente1)
        self.assertIsNotNone(atendimento.iniciado_em)
    
    def test_encerrar_chat(self):
        """Testa encerrar um chat"""
        atendimento = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            atendente=self.atendente1,
            chat_id='5511999999999',
            numero_whatsapp='5511999999999',
            status='em_atendimento'
        )
        
        response = self.client.post(
            f'/api/v1/chats/{atendimento.chat_id}/encerrar/',
            {'observacoes': 'Atendimento concluído'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.status, 'finalizado')
        self.assertIsNotNone(atendimento.finalizado_em)


class ChatServiceTests(TestCase):
    """Testes para ChatService"""
    
    def setUp(self):
        """Configuração inicial"""
        self.atendente = User.objects.create_user(
            username='atendente',
            password='pass123'
        )
        
        self.departamento = Departamento.objects.create(
            nome='Suporte',
            ativo=True
        )
        
        self.session = WhatsAppSession.objects.create(
            usuario=self.atendente,
            status='ready'
        )
        
        self.service = ChatService()
    
    def test_processar_nova_mensagem_cria_atendimento(self):
        """Testa que nova mensagem cria atendimento automaticamente"""
        # Criar mensagem
        mensagem = WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.atendente,
            message_id='msg_1',
            direction='inbound',
            message_type='text',
            chat_id='5511888888888',
            contact_number='5511888888888',
            contact_name='João Silva',
            text_content='Preciso de ajuda',
            status='delivered'
        )
        
        # Processar
        self.service.processar_nova_mensagem_recebida(mensagem)
        
        # Verificar que atendimento foi criado
        atendimento = Atendimento.objects.filter(chat_id='5511888888888').first()
        self.assertIsNotNone(atendimento)
        self.assertEqual(atendimento.status, 'aguardando')
        self.assertEqual(atendimento.numero_whatsapp, '5511888888888')
        
        # Verificar que foi adicionado à fila
        fila = FilaAtendimento.objects.filter(chat_id='5511888888888').first()
        self.assertIsNotNone(fila)
    
    def test_processar_mensagem_atendimento_existente_nao_duplica(self):
        """Testa que mensagem em chat existente não cria novo atendimento"""
        # Criar atendimento existente
        cliente = Cliente.objects.create(
            razao_social='Cliente Teste',
            cnpj='98.765.432/0001-10',
            status='ativo'
        )
        
        atendimento = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=cliente,
            chat_id='5511888888888',
            numero_whatsapp='5511888888888',
            status='em_atendimento'
        )
        
        # Criar nova mensagem no mesmo chat
        mensagem = WhatsAppMessage.objects.create(
            session=self.session,
            usuario=self.atendente,
            message_id='msg_2',
            direction='inbound',
            message_type='text',
            chat_id='5511888888888',
            contact_number='5511888888888',
            text_content='Segunda mensagem',
            status='delivered'
        )
        
        # Processar
        self.service.processar_nova_mensagem_recebida(mensagem)
        
        # Verificar que não duplicou
        count = Atendimento.objects.filter(chat_id='5511888888888').count()
        self.assertEqual(count, 1)
