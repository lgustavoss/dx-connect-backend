from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


def health_view(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_view),
]

