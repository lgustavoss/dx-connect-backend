"""
Testes para core/ws.py - WebSocket consumers e middleware
"""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from accounts.models import Agent
from django.test import TestCase
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import RefreshToken

from core.ws import EchoConsumer, WhatsAppConsumer, jwt_auth_middleware


class EchoConsumerTests(TestCase):
    """Testes para EchoConsumer"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.consumer = EchoConsumer()
        # Use MagicMock for scope to support both attribute and dict access
        self.consumer.scope = MagicMock()
        self.consumer.scope.__getitem__ = MagicMock(side_effect=lambda k: {"type": "websocket", "url": "ws://localhost/ws/echo/"}.get(k))
        self.consumer.channel_layer = AsyncMock()
        # Mock do channel_name
        self.consumer.channel_name = "test_channel"
    
    def test_echo_consumer_connect_authenticated(self):
        """Testa EchoConsumer.connect com usuário autenticado"""
        # Mock do usuário autenticado
        user = MagicMock()
        user.is_authenticated = True
        
        # Configure scope to support both attribute and dict access
        self.consumer.scope.user = user
        self.consumer.scope.__getitem__ = MagicMock(return_value=user)
        
        # Mock do accept
        self.consumer.accept = AsyncMock()
        
        # Executar connect
        asyncio.run(self.consumer.connect())
        
        # Verificar se accept foi chamado
        self.consumer.accept.assert_called_once()
    
    def test_echo_consumer_connect_unauthenticated(self):
        """Testa EchoConsumer.connect sem usuário autenticado"""
        # Mock do usuário não autenticado
        user = MagicMock()
        user.is_authenticated = False
        
        # Configure scope to support both attribute and dict access
        self.consumer.scope.user = user
        self.consumer.scope.__getitem__ = MagicMock(return_value=user)
        
        # Mock do close
        self.consumer.close = AsyncMock()
        
        # Executar connect
        asyncio.run(self.consumer.connect())
        
        # Verificar se close foi chamado com código 4001
        self.consumer.close.assert_called_once_with(code=4001)
    
    def test_echo_consumer_connect_no_user(self):
        """Testa EchoConsumer.connect sem usuário"""
        # Sem usuário no scope
        self.consumer.scope = {"type": "websocket"}
        
        # Mock do close
        self.consumer.close = AsyncMock()
        
        # Executar connect
        asyncio.run(self.consumer.connect())
        
        # Verificar se close foi chamado com código 4001
        self.consumer.close.assert_called_once_with(code=4001)
    
    def test_echo_consumer_receive_json_ping(self):
        """Testa EchoConsumer.receive_json com ping"""
        content = {"type": "ping"}
        
        # Mock do send_json
        self.consumer.send_json = AsyncMock()
        
        # Executar receive_json
        asyncio.run(self.consumer.receive_json(content))
        
        # Verificar se send_json foi chamado com pong
        self.consumer.send_json.assert_called_once_with({"type": "pong"})
    
    def test_echo_consumer_receive_json_echo(self):
        """Testa EchoConsumer.receive_json com echo"""
        content = {"type": "echo", "message": "Hello World"}
        
        # Mock do send_json
        self.consumer.send_json = AsyncMock()
        
        # Executar receive_json
        asyncio.run(self.consumer.receive_json(content))
        
        # Verificar se send_json foi chamado com echo
        expected = {"echo": content}
        self.consumer.send_json.assert_called_once_with(expected)
    


class WhatsAppConsumerTests(TestCase):
    """Testes para WhatsAppConsumer"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.consumer = WhatsAppConsumer()
        self.consumer.scope = MagicMock()
        self.consumer.scope.__getitem__ = MagicMock(side_effect=lambda k: {"type": "websocket", "url": "ws://localhost/ws/whatsapp/"}.get(k))
        self.consumer.scope.get = MagicMock(side_effect=lambda k, default=None: {"type": "websocket", "url": "ws://localhost/ws/whatsapp/"}.get(k, default))
        self.consumer.channel_layer = AsyncMock()
        # Mock do channel_name
        self.consumer.channel_name = "test_channel"
    
    def test_whatsapp_consumer_connect_with_authenticated_user(self):
        """Testa WhatsAppConsumer.connect com usuário autenticado"""
        # Mock do usuário autenticado
        user = MagicMock()
        user.is_authenticated = True
        user.id = 1
        
        # Configure scope to support both attribute and dict access
        self.consumer.scope.user = user
        self.consumer.scope.__getitem__ = MagicMock(return_value=user)
        
        # Mock do accept e group_add
        self.consumer.accept = AsyncMock()
        self.consumer.channel_layer.group_add = AsyncMock()
        
        # Executar connect
        asyncio.run(self.consumer.connect())
        
        # Verificar se accept foi chamado
        self.consumer.accept.assert_called_once()
        
        # Verificar se group_add foi chamado
        self.consumer.channel_layer.group_add.assert_called_once_with(
            "user_1_whatsapp", self.consumer.channel_name
        )
        
        # Verificar se group_name foi definido
        self.assertEqual(self.consumer.group_name, "user_1_whatsapp")
    
    def test_whatsapp_consumer_connect_with_token(self):
        """Testa WhatsAppConsumer.connect com token no query string"""
        # Mock do scope com query string
        self.consumer.scope = {
            "type": "websocket",
            "url": "ws://localhost/ws/whatsapp/",
            "query_string": b"token=valid_token"
        }
        
        # Mock do usuário não autenticado
        user = MagicMock()
        user.is_authenticated = False
        self.consumer.scope["user"] = user
        
        # Mock do accept e group_add
        self.consumer.accept = AsyncMock()
        self.consumer.channel_layer.group_add = AsyncMock()
        
        # Mock do AccessToken
        with patch('core.ws.AccessToken') as mock_token:
            mock_access = MagicMock()
            mock_access.get.return_value = 2
            mock_token.return_value = mock_access
            
            # Executar connect
            asyncio.run(self.consumer.connect())
        
        # Verificar se accept foi chamado
        self.consumer.accept.assert_called_once()
        
        # Verificar se group_add foi chamado
        self.consumer.channel_layer.group_add.assert_called_once_with(
            "user_2_whatsapp", self.consumer.channel_name
        )
    
    def test_whatsapp_consumer_connect_with_invalid_token(self):
        """Testa WhatsAppConsumer.connect com token inválido"""
        # Mock do scope com query string
        self.consumer.scope = {
            "type": "websocket",
            "url": "ws://localhost/ws/whatsapp/",
            "query_string": b"token=invalid_token"
        }
        
        # Mock do usuário não autenticado
        user = MagicMock()
        user.is_authenticated = False
        self.consumer.scope["user"] = user
        
        # Mock do accept
        self.consumer.accept = AsyncMock()
        
        # Executar connect
        asyncio.run(self.consumer.connect())
        
        # Verificar se accept foi chamado
        self.consumer.accept.assert_called_once()
        
        # Verificar se group_name não foi definido
        self.assertFalse(hasattr(self.consumer, 'group_name'))
    
    def test_whatsapp_consumer_connect_without_user_or_token(self):
        """Testa WhatsAppConsumer.connect sem usuário ou token"""
        # Mock do scope sem usuário
        self.consumer.scope = {
            "type": "websocket",
            "url": "ws://localhost/ws/whatsapp/"
        }
        
        # Mock do accept
        self.consumer.accept = AsyncMock()
        
        # Executar connect
        asyncio.run(self.consumer.connect())
        
        # Verificar se accept foi chamado
        self.consumer.accept.assert_called_once()
        
        # Verificar se group_name não foi definido
        self.assertFalse(hasattr(self.consumer, 'group_name'))
    
    def test_whatsapp_consumer_receive_json_ping(self):
        """Testa WhatsAppConsumer.receive_json com ping"""
        content = {"type": "ping"}
        
        # Mock do send_json
        self.consumer.send_json = AsyncMock()
        
        # Executar receive_json
        asyncio.run(self.consumer.receive_json(content))
        
        # Verificar se send_json foi chamado com pong
        self.consumer.send_json.assert_called_once_with({"type": "pong"})
    
    def test_whatsapp_consumer_receive_json_other_content(self):
        """Testa WhatsAppConsumer.receive_json com conteúdo que não é ping"""
        content = {"type": "message", "text": "Hello"}
        
        # Mock do send_json
        self.consumer.send_json = AsyncMock()
        
        # Executar receive_json
        asyncio.run(self.consumer.receive_json(content))
        
        # Verificar se send_json não foi chamado
        self.consumer.send_json.assert_not_called()
    
    def test_whatsapp_consumer_whatsapp_event_with_event(self):
        """Testa WhatsAppConsumer.whatsapp_event com evento"""
        event = {
            "event": {
                "type": "message",
                "text": "Hello World"
            }
        }
        
        # Mock do send_json
        self.consumer.send_json = AsyncMock()
        
        # Executar whatsapp_event
        asyncio.run(self.consumer.whatsapp_event(event))
        
        # Verificar se send_json foi chamado com o evento
        self.consumer.send_json.assert_called_once_with(event["event"])
    
    def test_whatsapp_consumer_whatsapp_event_no_event(self):
        """Testa WhatsAppConsumer.whatsapp_event sem evento"""
        # Mock do send_json
        self.consumer.send_json = AsyncMock()
        
        # Executar whatsapp_event sem evento
        asyncio.run(self.consumer.whatsapp_event({}))
        
        # Verificar se send_json foi chamado com payload vazio
        self.consumer.send_json.assert_called_once_with({})
    
    def test_whatsapp_consumer_disconnect_without_group(self):
        """Testa WhatsAppConsumer.disconnect sem grupo"""
        # Executar disconnect
        asyncio.run(self.consumer.disconnect(1000))
        
        # Não deve haver erros
        self.assertTrue(True)
    
    def test_whatsapp_consumer_disconnect_with_group(self):
        """Testa WhatsAppConsumer.disconnect com grupo"""
        # Mock do group_discard
        self.consumer.channel_layer.group_discard = AsyncMock()
        
        # Definir group_name
        self.consumer.group_name = "user_1_whatsapp"
        
        # Executar disconnect
        asyncio.run(self.consumer.disconnect(1000))
        
        # Verificar se group_discard foi chamado
        self.consumer.channel_layer.group_discard.assert_called_once_with(
            "user_1_whatsapp", self.consumer.channel_name
        )


class JwtAuthMiddlewareTests(TestCase):
    """Testes para jwt_auth_middleware"""
    
    def test_jwt_auth_middleware_without_token(self):
        """Testa jwt_auth_middleware sem token"""
        scope = {
            "type": "websocket",
            "url": "ws://localhost/ws/echo/"
        }
        
        # Mock da função inner
        inner = AsyncMock()
        
        # Executar middleware
        asyncio.run(jwt_auth_middleware(inner)(scope, None, None))
        
        # Verificar se inner foi chamado
        inner.assert_called_once()
    
    def test_jwt_auth_middleware_with_valid_token(self):
        """Testa jwt_auth_middleware com token válido"""
        # Criar usuário
        user = Agent.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        # Gerar token
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        scope = {
            "type": "websocket",
            "url": f"ws://localhost/ws/echo/?token={token}"
        }
        
        # Mock da função inner
        inner = AsyncMock()
        
        # Executar middleware
        asyncio.run(jwt_auth_middleware(inner)(scope, None, None))
        
        # Verificar se inner foi chamado
        inner.assert_called_once()
        
        # Verificar se usuário foi definido no scope
        self.assertIsNotNone(scope.get("user"))
    
    def test_jwt_auth_middleware_with_invalid_token(self):
        """Testa jwt_auth_middleware com token inválido"""
        scope = {
            "type": "websocket",
            "url": "ws://localhost/ws/echo/?token=invalid_token"
        }
        
        # Mock da função inner
        inner = AsyncMock()
        
        # Executar middleware
        asyncio.run(jwt_auth_middleware(inner)(scope, None, None))
        
        # Verificar se inner foi chamado
        inner.assert_called_once()
    
    def test_jwt_auth_middleware_with_nonexistent_user(self):
        """Testa jwt_auth_middleware com usuário inexistente"""
        # Gerar token para usuário que não existe
        refresh = RefreshToken()
        refresh["user_id"] = 99999  # ID que não existe
        token = str(refresh.access_token)
        
        scope = {
            "type": "websocket",
            "url": f"ws://localhost/ws/echo/?token={token}"
        }
        
        # Mock da função inner
        inner = AsyncMock()
        
        # Executar middleware
        asyncio.run(jwt_auth_middleware(inner)(scope, None, None))
        
        # Verificar se inner foi chamado
        inner.assert_called_once()
    
    def test_jwt_auth_middleware_with_token_exception(self):
        """Testa jwt_auth_middleware com exceção no token"""
        scope = {
            "type": "websocket",
            "url": "ws://localhost/ws/echo/?token=malformed_token"
        }
        
        # Mock da função inner
        inner = AsyncMock()
        
        # Executar middleware
        asyncio.run(jwt_auth_middleware(inner)(scope, None, None))
        
        # Verificar se inner foi chamado
        inner.assert_called_once()
    
    def test_jwt_auth_middleware_with_user_id_none(self):
        """Testa jwt_auth_middleware com user_id None no token"""
        # Gerar token sem user_id
        refresh = RefreshToken()
        token = str(refresh.access_token)
        
        scope = {
            "type": "websocket",
            "url": f"ws://localhost/ws/echo/?token={token}"
        }
        
        # Mock da função inner
        inner = AsyncMock()
        
        # Executar middleware
        asyncio.run(jwt_auth_middleware(inner)(scope, None, None))
        
        # Verificar se inner foi chamado
        inner.assert_called_once()
    
    def test_jwt_auth_middleware_calls_inner(self):
        """Testa se jwt_auth_middleware chama a função inner"""
        scope = {
            "type": "websocket",
            "url": "ws://localhost/ws/echo/"
        }
        
        # Mock da função inner
        inner = AsyncMock()
        
        # Executar middleware
        asyncio.run(jwt_auth_middleware(inner)(scope, None, None))
        
        # Verificar se inner foi chamado
        inner.assert_called_once()
    
    def test_jwt_auth_middleware_sync_wrappers(self):
        """Testa wrappers síncronos para compatibilidade com TestCase"""
        scope = {
            "type": "websocket",
            "url": "ws://localhost/ws/echo/"
        }
        
        # Mock da função inner
        inner = AsyncMock()
        
        # Executar middleware usando wrapper síncrono
        from asgiref.sync import async_to_sync
        async_to_sync(jwt_auth_middleware(inner))(scope, None, None)
        
        # Verificar se inner foi chamado
        inner.assert_called_once()