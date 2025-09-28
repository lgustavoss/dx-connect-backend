from __future__ import annotations

from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient
from asgiref.sync import async_to_sync

from config.asgi import application
from accounts.models import Agent
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import Permission


def make_token(user: Agent) -> str:
    return str(RefreshToken.for_user(user).access_token)


@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
class WhatsAppSessionTests(TransactionTestCase):
    reset_sequences = True

    def test_session_flow_and_message_events(self):
        user = Agent.objects.create_user(username="u1", password="p")
        # Conceder permissão necessária para iniciar sessão e enviar mensagens
        perm = Permission.objects.get(codename="manage_config_whatsapp")
        user.user_permissions.add(perm)
        token = make_token(user)

        communicator = WebsocketCommunicator(application, f"/ws/whatsapp/?token={token}")
        connected, _ = async_to_sync(communicator.connect)()
        self.assertTrue(connected)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        res = client.post("/api/v1/whatsapp/session/start")
        self.assertEqual(res.status_code, 202)

        # Esperar até ready
        seen_ready = False
        for _ in range(10):
            event = async_to_sync(communicator.receive_json_from)()
            if event.get("type") == "session_status" and event.get("status") == "ready":
                seen_ready = True
                break
        self.assertTrue(seen_ready)

        res2 = client.post(
            "/api/v1/whatsapp/messages",
            {"to": "5599999999999", "type": "text", "text": "Ola"},
            format="json",
        )
        self.assertEqual(res2.status_code, 202)
        message_id = res2.data["message_id"]

        recv_statuses = []
        for _ in range(20):
            evt = async_to_sync(communicator.receive_json_from)()
            if evt.get("type") == "message_status" and evt.get("message_id") == message_id:
                recv_statuses.append(evt["status"])
                if evt["status"] in {"read", "failed"}:
                    break

        self.assertGreaterEqual(len(recv_statuses), 1)
        self.assertEqual(recv_statuses[0], "queued")
        self.assertIn(recv_statuses[-1], {"read", "failed"})

        async_to_sync(communicator.disconnect)()


