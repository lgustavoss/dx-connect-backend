import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from urllib.parse import parse_qs


User = get_user_model()


class EchoConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if not getattr(self.scope, "user", None) or not self.scope["user"].is_authenticated:
            await self.close(code=4001)
            return
        await self.accept()

    async def receive_json(self, content, **kwargs):
        if content == {"type": "ping"}:
            await self.send_json({"type": "pong"})
            return
        await self.send_json({"echo": content})


# DEPRECATED: Consumer legado movido para whatsapp/consumers.py
# Mantido apenas para referência histórica
# class WhatsAppConsumer(AsyncJsonWebsocketConsumer):
#     """
#     DEPRECATED - Use whatsapp.consumers.WhatsAppConsumer
#     Este consumer foi substituído por versão completa em whatsapp/consumers.py
#     """
#     pass


def jwt_auth_middleware(inner):
    async def middleware(scope, receive, send):
        # Expect token via query string ?token=...
        query = scope.get("query_string", b"").decode()
        params = parse_qs(query)
        token = (params.get("token") or [None])[0]
        user = None
        if token:
            try:
                access = AccessToken(token)
                user_id = access.get("user_id")
                if user_id:
                    user = await sync_to_async(lambda: User.objects.filter(pk=user_id).first())()
            except Exception:
                user = None
        scope["user"] = user or AnonymousUser()  # type: ignore[name-defined]
        return await inner(scope, receive, send)

    return middleware


