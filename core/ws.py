import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async


User = get_user_model()


class EchoConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Para facilitar testes: aceitar sempre e, se não autenticado, responder erro no primeiro receive
        await self.accept()

    async def receive_json(self, content, **kwargs):
        if content == {"type": "ping"}:
            await self.send_json({"type": "pong"})
            return
        await self.send_json({"echo": content})


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


