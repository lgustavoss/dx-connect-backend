from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    WhatsAppSessionViewSet,
    WhatsAppMessageViewSet,
    WhatsAppSendMessageView
)

router = DefaultRouter()
router.register(r'sessions', WhatsAppSessionViewSet, basename='whatsapp-session')
router.register(r'messages', WhatsAppMessageViewSet, basename='whatsapp-message')

urlpatterns = [
    # Endpoint para envio de mensagens
    path('send/', WhatsAppSendMessageView.as_view(), name='whatsapp-send'),
    # Router endpoints
    path('', include(router.urls)),
]

