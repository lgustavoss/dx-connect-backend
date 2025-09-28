from __future__ import annotations

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
import time
from accounts.models import Agent
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import Permission


def make_token(user: Agent) -> str:
    return str(RefreshToken.for_user(user).access_token)


@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
class WhatsAppSessionTests(TestCase):

    def test_session_flow_and_message_events(self):
        user = Agent.objects.create_user(username="u1", password="p")
        # Conceder permissão necessária para iniciar sessão e enviar mensagens
        perm = Permission.objects.get(codename="manage_config_whatsapp")
        user.user_permissions.add(perm)
        token = make_token(user)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        res = client.post("/api/v1/whatsapp/session/start")
        self.assertEqual(res.status_code, 202)

        # Aguardar até status ready via REST
        ready = False
        for _ in range(20):
            time.sleep(0.1)
            s = client.get("/api/v1/whatsapp/session/status")
            self.assertEqual(s.status_code, 200)
            if s.data.get("status") == "ready":
                ready = True
                break
        self.assertTrue(ready)

        res2 = client.post(
            "/api/v1/whatsapp/messages",
            {"to": "5599999999999", "type": "text", "text": "Ola"},
            format="json",
        )
        self.assertEqual(res2.status_code, 202)
        self.assertIn("message_id", res2.data)


