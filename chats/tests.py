"""
Testes para API de Chats (Issue #85).
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
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


class ChatAttendTests(TestCase):
    """Testes específicos para endpoint POST /chats/{chat_id}/attend/"""
    
    def setUp(self):
        """Configuração inicial"""
        self.client = APIClient()
        
        # Criar usuários
        self.agente1 = User.objects.create_user(
            username='agente1',
            password='pass123',
            display_name='Agente 1'
        )
        self.agente2 = User.objects.create_user(
            username='agente2',
            password='pass123',
            display_name='Agente 2'
        )
        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            is_superuser=True,
            display_name='Admin'
        )
        
        # Criar departamento
        self.departamento = Departamento.objects.create(
            nome='Suporte',
            cor='#3B82F6',
            ativo=True
        )
        self.departamento.atendentes.add(self.agente1, self.agente2)
        
        # Criar cliente
        self.cliente = Cliente.objects.create(
            razao_social='Cliente Teste',
            cnpj='12.345.678/0001-90',
            telefone_principal='5511999999999',
            status='ativo'
        )
        
        self.client.force_authenticate(user=self.agente1)
    
    def test_attend_chat_success(self):
        """Cenário 1: Atendimento bem-sucedido"""
        # Criar chat aguardando
        atendimento = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            chat_id='5511999999999',
            numero_whatsapp='5511999999999',
            status='aguardando'
        )
        
        # Tentar assumir o chat
        response = self.client.post(f'/api/v1/chats/{atendimento.chat_id}/attend/')
        
        # Verificar resposta
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Chat atendido com sucesso')
        self.assertEqual(response.data['chat_id'], '5511999999999')
        self.assertEqual(response.data['assigned_agent'], self.agente1.id)
        self.assertEqual(response.data['status'], 'em_atendimento')
        self.assertIsNotNone(response.data['assigned_at'])
        
        # Verificar mudanças no banco
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.status, 'em_atendimento')
        self.assertEqual(atendimento.atendente, self.agente1)
        self.assertIsNotNone(atendimento.iniciado_em)
        
        # Verificar que foi removido da fila
        fila_count = FilaAtendimento.objects.filter(chat_id=atendimento.chat_id).count()
        self.assertEqual(fila_count, 0)
    
    def test_attend_chat_already_attended(self):
        """Cenário 2: Chat já atendido"""
        # Criar chat já atendido
        atendimento = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            atendente=self.agente2,
            chat_id='5511999999999',
            numero_whatsapp='5511999999999',
            status='em_atendimento'
        )
        
        # Tentar assumir o chat
        response = self.client.post(f'/api/v1/chats/{atendimento.chat_id}/attend/')
        
        # Verificar resposta de erro
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Chat não está disponível para atendimento')
        self.assertEqual(response.data['current_status'], 'em_atendimento')
        
        # Verificar que não mudou nada
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.status, 'em_atendimento')
        self.assertEqual(atendimento.atendente, self.agente2)
    
    def test_attend_chat_not_found(self):
        """Cenário 3: Chat inexistente"""
        response = self.client.post('/api/v1/chats/9999999999999/attend/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Chat não encontrado')
    
    def test_attend_chat_invalid_token(self):
        """Cenário 4: Token inválido"""
        # Remover autenticação
        self.client.force_authenticate(user=None)
        
        atendimento = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            chat_id='5511999999999',
            numero_whatsapp='5511999999999',
            status='aguardando'
        )
        
        response = self.client.post(f'/api/v1/chats/{atendimento.chat_id}/attend/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
    
    def test_attend_chat_finalizado_status(self):
        """Testa tentativa de assumir chat finalizado"""
        atendimento = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            chat_id='5511999999999',
            numero_whatsapp='5511999999999',
            status='finalizado'
        )
        
        response = self.client.post(f'/api/v1/chats/{atendimento.chat_id}/attend/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Chat não está disponível para atendimento')
        self.assertEqual(response.data['current_status'], 'finalizado')
    
    def test_attend_chat_pending_status(self):
        """Testa assumir chat com status 'pending' (compatibilidade)"""
        atendimento = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            chat_id='5511999999999',
            numero_whatsapp='5511999999999',
            status='pending'  # Status alternativo
        )
        
        response = self.client.post(f'/api/v1/chats/{atendimento.chat_id}/attend/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.status, 'em_atendimento')
        self.assertEqual(atendimento.atendente, self.agente1)
    
    def test_attend_multiple_chats_same_agent(self):
        """Testa agente assumindo múltiplos chats (deve ser permitido)"""
        # Criar dois chats aguardando
        atendimento1 = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            chat_id='5511111111111',
            numero_whatsapp='5511111111111',
            status='aguardando'
        )
        
        atendimento2 = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            chat_id='5511222222222',
            numero_whatsapp='5511222222222',
            status='aguardando'
        )
        
        # Assumir primeiro chat
        response1 = self.client.post(f'/api/v1/chats/{atendimento1.chat_id}/attend/')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Assumir segundo chat (deve funcionar)
        response2 = self.client.post(f'/api/v1/chats/{atendimento2.chat_id}/attend/')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verificar que ambos foram atribuídos
        atendimento1.refresh_from_db()
        atendimento2.refresh_from_db()
        
        self.assertEqual(atendimento1.atendente, self.agente1)
        self.assertEqual(atendimento2.atendente, self.agente1)
        self.assertEqual(atendimento1.status, 'em_atendimento')
        self.assertEqual(atendimento2.status, 'em_atendimento')
    
    def test_attend_chat_different_agents(self):
        """Testa que diferentes agentes podem assumir chats diferentes"""
        # Criar dois chats aguardando
        atendimento1 = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            chat_id='5511111111111',
            numero_whatsapp='5511111111111',
            status='aguardando'
        )
        
        atendimento2 = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            chat_id='5511222222222',
            numero_whatsapp='5511222222222',
            status='aguardando'
        )
        
        # Agente1 assume primeiro chat
        self.client.force_authenticate(user=self.agente1)
        response1 = self.client.post(f'/api/v1/chats/{atendimento1.chat_id}/attend/')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Agente2 assume segundo chat
        self.client.force_authenticate(user=self.agente2)
        response2 = self.client.post(f'/api/v1/chats/{atendimento2.chat_id}/attend/')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verificar atribuições
        atendimento1.refresh_from_db()
        atendimento2.refresh_from_db()
        
        self.assertEqual(atendimento1.atendente, self.agente1)
        self.assertEqual(atendimento2.atendente, self.agente2)
        self.assertEqual(response1.data['assigned_agent'], self.agente1.id)
        self.assertEqual(response2.data['assigned_agent'], self.agente2.id)
    
    def test_attend_chat_admin_permissions(self):
        """Testa que admin também pode assumir chats"""
        self.client.force_authenticate(user=self.admin)
        
        atendimento = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            chat_id='5511999999999',
            numero_whatsapp='5511999999999',
            status='aguardando'
        )
        
        response = self.client.post(f'/api/v1/chats/{atendimento.chat_id}/attend/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['assigned_agent'], self.admin.id)
        
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.atendente, self.admin)
    
    def test_attend_chat_no_body_required(self):
        """Testa que endpoint não requer body (opcional)"""
        atendimento = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            chat_id='5511999999998',  # ID diferente para evitar conflito
            numero_whatsapp='5511999999998',
            status='aguardando'
        )
        
        # Chamar sem body
        response = self.client.post(f'/api/v1/chats/{atendimento.chat_id}/attend/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Criar novo atendimento para segundo teste
        atendimento2 = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            chat_id='5511999999997',  # ID diferente
            numero_whatsapp='5511999999997',
            status='aguardando'
        )
        
        # Chamar com body vazio
        response = self.client.post(f'/api/v1/chats/{atendimento2.chat_id}/attend/', {})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_attend_chat_reaberto_multiple_objects(self):
        """Testa Issue #91: Atender chat reaberto com múltiplos registros"""
        # Cenário: Chat foi encerrado e reaberto (múltiplos registros de Atendimento)
        
        # Criar primeiro atendimento (encerrado)
        atendimento1 = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            atendente=self.agente1,
            chat_id='5511999999999',
            numero_whatsapp='5511999999999',
            status='finalizado',
            criado_em=timezone.now() - timezone.timedelta(hours=2)
        )
        
        # Criar segundo atendimento (reaberto)
        atendimento2 = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            chat_id='5511999999999',  # Mesmo chat_id
            numero_whatsapp='5511999999999',
            status='aguardando',
            criado_em=timezone.now()  # Mais recente
        )
        
        # Tentar assumir o chat (deve pegar o mais recente)
        response = self.client.post(f'/api/v1/chats/{atendimento2.chat_id}/attend/')
        
        # Verificar que funcionou sem erro MultipleObjectsReturned
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Chat atendido com sucesso')
        self.assertEqual(response.data['assigned_agent'], self.agente1.id)
        
        # Verificar que o atendimento correto foi atualizado (o mais recente)
        atendimento1.refresh_from_db()
        atendimento2.refresh_from_db()
        
        # Atendimento antigo deve permanecer finalizado
        self.assertEqual(atendimento1.status, 'finalizado')
        
        # Atendimento novo deve ter sido assumido
        self.assertEqual(atendimento2.status, 'em_atendimento')
        self.assertEqual(atendimento2.atendente, self.agente1)
        self.assertIsNotNone(atendimento2.iniciado_em)
    
    def test_aceitar_chat_reaberto_multiple_objects(self):
        """Testa Issue #91: Aceitar chat reaberto com múltiplos registros"""
        # Cenário: Chat foi encerrado e reaberto (múltiplos registros de Atendimento)
        
        # Criar primeiro atendimento (encerrado)
        atendimento1 = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            atendente=self.agente1,
            chat_id='5511999999998',
            numero_whatsapp='5511999999998',
            status='finalizado',
            criado_em=timezone.now() - timezone.timedelta(hours=2)
        )
        
        # Criar segundo atendimento (reaberto)
        atendimento2 = Atendimento.objects.create(
            departamento=self.departamento,
            cliente=self.cliente,
            chat_id='5511999999998',  # Mesmo chat_id
            numero_whatsapp='5511999999998',
            status='aguardando',
            criado_em=timezone.now()  # Mais recente
        )
        
        # Tentar aceitar o chat (deve pegar o mais recente)
        response = self.client.post(f'/api/v1/chats/{atendimento2.chat_id}/aceitar/')
        
        # Verificar que funcionou sem erro MultipleObjectsReturned
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que o atendimento correto foi atualizado (o mais recente)
        atendimento1.refresh_from_db()
        atendimento2.refresh_from_db()
        
        # Atendimento antigo deve permanecer finalizado
        self.assertEqual(atendimento1.status, 'finalizado')
        
        # Atendimento novo deve ter sido aceito
        self.assertEqual(atendimento2.status, 'em_atendimento')
        self.assertEqual(atendimento2.atendente, self.agente1)
