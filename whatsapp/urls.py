from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    WhatsAppSessionViewSet,
    WhatsAppMessageViewSet,
    WhatsAppSendMessageView,
    WhatsAppWebhookView
)

router = DefaultRouter()
router.register(r'sessions', WhatsAppSessionViewSet, basename='whatsapp-session')
router.register(r'messages', WhatsAppMessageViewSet, basename='whatsapp-message')

urlpatterns = [
    # Endpoint para envio de mensagens
    path('send/', WhatsAppSendMessageView.as_view(), name='whatsapp-send'),
    # Webhook para receber mensagens externas (Issue #44)
    path('webhook/', WhatsAppWebhookView.as_view(), name='whatsapp-webhook'),
    # Router endpoints
    path('', include(router.urls)),
]

