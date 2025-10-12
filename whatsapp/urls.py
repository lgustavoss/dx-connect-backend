from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    WhatsAppSessionViewSet,
    WhatsAppMessageViewSet,
    WhatsAppSendMessageView,
    WhatsAppWebhookView,
    WhatsAppInjectIncomingView
)

router = DefaultRouter()
router.register(r'sessions', WhatsAppSessionViewSet, basename='whatsapp-session')
router.register(r'messages', WhatsAppMessageViewSet, basename='whatsapp-message')

urlpatterns = [
    # Endpoint para envio de mensagens
    path('send/', WhatsAppSendMessageView.as_view(), name='whatsapp-send'),
    # Webhook para receber mensagens externas (Issue #44)
    path('webhook/', WhatsAppWebhookView.as_view(), name='whatsapp-webhook'),
    # Injetar mensagem de teste (apenas desenvolvimento - Issue #83)
    path('inject-incoming/', WhatsAppInjectIncomingView.as_view(), name='whatsapp-inject-incoming'),
    # Router endpoints
    path('', include(router.urls)),
]

