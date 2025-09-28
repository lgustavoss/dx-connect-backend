from __future__ import annotations

import asyncio

import pytest
from channels.testing import WebsocketCommunicator
from django.test import override_settings
from rest_framework.test import APIClient
from asgiref.sync import sync_to_async

from config.asgi import application
from accounts.models import Agent
from rest_framework_simplejwt.tokens import RefreshToken


def make_token(user: Agent) -> str:
    return str(RefreshToken.for_user(user).access_token)


@pytest.mark.django_db(transaction=True)
@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
async def test_session_flow_and_message_events(settings):
    user = await sync_to_async(Agent.objects.create_user)(username="u1", password="p")
    token = make_token(user)

    # Conectar WS
    communicator = WebsocketCommunicator(application, f"/ws/whatsapp/?token={token}")
    connected, _ = await communicator.connect()
    assert connected

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # Iniciar sessão
    res = await sync_to_async(client.post)("/api/v1/whatsapp/session/start")
    assert res.status_code == 202

    # Esperar status até ready
    states = []
    while len(states) < 3:  # connecting, qrcode, authenticated, ready (ao menos 3 eventos)
        event = await communicator.receive_json_from()
        if event.get("type") == "session_status":
            states.append(event["status"])
        if event.get("type") == "qrcode":
            pass
        if "ready" in states:
            break

    assert "ready" in states

    # Enviar mensagem
    res2 = await sync_to_async(client.post)("/api/v1/whatsapp/messages", {"to": "5599999999999", "type": "text", "text": "Ola"}, format="json")
    assert res2.status_code == 202
    message_id = res2.data["message_id"]

    # Receber sequência de statuses
    recv_statuses = []
    while True:
        evt = await communicator.receive_json_from()
        if evt.get("type") == "message_status" and evt.get("message_id") == message_id:
            recv_statuses.append(evt["status"])
            if evt["status"] in {"read", "failed"}:
                break

    assert recv_statuses[:2] == ["queued", "sent"]
    assert recv_statuses[-1] == "read"

    await communicator.disconnect()


