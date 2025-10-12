import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.development"))

django_asgi_app = get_asgi_application()

# Importar consumidores/middleware APÓS inicializar o Django
from core.ws import EchoConsumer, jwt_auth_middleware  # noqa: E402
from whatsapp.consumers import WhatsAppConsumer  # noqa: E402 - Consumer completo

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": jwt_auth_middleware(
        URLRouter([
            path("ws/echo/", EchoConsumer.as_asgi()),
            path("ws/whatsapp/", WhatsAppConsumer.as_asgi()),  # Consumer de whatsapp/consumers.py
        ])
    ),
})

