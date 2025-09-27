from django.contrib import admin
from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from core.views import ConfigView
from core.views.config import AppearanceConfigView, ChatConfigView, CompanyConfigView, EmailConfigView, WhatsAppConfigView
from core.views.upload import AppearanceUploadView
from accounts.views import (
    AgentGroupsView,
    GroupDetailView,
    GroupListCreateView,
    PermissionListView,
)
from django.conf import settings
from django.conf.urls.static import static


@api_view(["GET"])
@permission_classes([AllowAny])
def health_view(_request):
    return Response({"status": "ok"})


@api_view(["GET"])
def me_view(request):
    user = request.user
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": getattr(user, "display_name", ""),
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", health_view),
    # Auth JWT (v1)
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Me (v1)
    path("api/v1/me/", me_view),
    # Config (v1)
    path("api/v1/config/", ConfigView.as_view()),
    path("api/v1/config/company/", CompanyConfigView.as_view()),
    path("api/v1/config/chat/", ChatConfigView.as_view()),
    path("api/v1/config/email/", EmailConfigView.as_view()),
    path("api/v1/config/appearance/", AppearanceConfigView.as_view()),
    path("api/v1/config/whatsapp/", WhatsAppConfigView.as_view()),
    path("api/v1/config/appearance/upload/", AppearanceUploadView.as_view()),
    # AuthZ (v1)
    path("api/v1/authz/permissions/", PermissionListView.as_view()),
    path("api/v1/authz/groups/", GroupListCreateView.as_view()),
    path("api/v1/authz/groups/<int:pk>/", GroupDetailView.as_view()),
    path("api/v1/authz/agents/<int:agent_id>/groups/", AgentGroupsView.as_view()),
    # Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

