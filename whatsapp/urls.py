from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    WhatsAppSessionViewSet,
    WhatsAppMessageViewSet,
    WhatsAppSendMessageView,
    WhatsAppWebhookView,
    WhatsAppInjectIncomingView
)
from .webhook_views import WhatsAppWebhookView as StatusWebhookView, webhook_health_check
from .status_views import (
    MessageStatsView,
    MessageStatusListView,
    RetryFailedMessagesView,
    MessageStatusUpdateView,
    ChatReadStatusView
)

router = DefaultRouter()
router.register(r'sessions', WhatsAppSessionViewSet, basename='whatsapp-session')
router.register(r'messages', WhatsAppMessageViewSet, basename='whatsapp-message')

urlpatterns = [
    # Endpoint para envio de mensagens
    path('send/', WhatsAppSendMessageView.as_view(), name='whatsapp-send'),
    # Webhook para receber mensagens externas (Issue #44)
    path('webhook/', WhatsAppWebhookView.as_view(), name='whatsapp-webhook'),
    # Webhook para status de mensagens
    path('status-webhook/', StatusWebhookView.as_view(), name='whatsapp-status-webhook'),
    # Health check do webhook
    path('webhook/health/', webhook_health_check, name='whatsapp-webhook-health'),
    # Injetar mensagem de teste (apenas desenvolvimento - Issue #83)
    path('inject-incoming/', WhatsAppInjectIncomingView.as_view(), name='whatsapp-inject-incoming'),
    
    # Endpoints de status e monitoramento
    path('stats/', MessageStatsView.as_view(), name='whatsapp-message-stats'),
    path('status/', MessageStatusListView.as_view(), name='whatsapp-message-status-list'),
    path('retry/', RetryFailedMessagesView.as_view(), name='whatsapp-retry-failed'),
    path('update-status/', MessageStatusUpdateView.as_view(), name='whatsapp-update-status'),
    path('mark-read/', ChatReadStatusView.as_view(), name='whatsapp-mark-read'),
    
    # Router endpoints
    path('', include(router.urls)),
]

