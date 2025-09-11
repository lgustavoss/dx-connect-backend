from django.contrib import admin
from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


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
    path("health/", health_view),
    # Auth JWT
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Me
    path("api/me/", me_view),
]

