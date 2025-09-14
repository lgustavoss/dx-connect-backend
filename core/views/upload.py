import os
from uuid import uuid4

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils import get_or_create_config_with_defaults


class AppearanceUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get("file")
        kind = request.data.get("kind")  # logo|favicon
        if not file or kind not in {"logo", "favicon"}:
            return Response({"detail": "file e kind={logo|favicon} são obrigatórios"}, status=400)
        ext = os.path.splitext(file.name)[1]
        name = f"appearance/{uuid4().hex}{ext}"
        path = default_storage.save(name, ContentFile(file.read()))
        url = settings.MEDIA_URL + path if settings.MEDIA_URL.endswith("/") else settings.MEDIA_URL + "/" + path
        obj, _ = get_or_create_config_with_defaults()
        if kind == "logo":
            obj.appearance_settings["login_logo_url"] = url
        else:
            obj.appearance_settings["favicon_url"] = url
        obj.save()
        return Response({"url": url})

    def delete(self, request):
        kind = request.query_params.get("kind")  # logo|favicon
        if kind not in {"logo", "favicon"}:
            return Response({"detail": "kind={logo|favicon} é obrigatório"}, status=400)
        obj, _ = get_or_create_config_with_defaults()
        key = "login_logo_url" if kind == "logo" else "favicon_url"
        url = obj.appearance_settings.get(key) or ""
        if not url:
            return Response(status=204)
        # remover arquivo físico se for local
        prefix = settings.MEDIA_URL.rstrip("/") + "/"
        if url.startswith(prefix):
            rel = url[len(prefix):]
            if default_storage.exists(rel):
                default_storage.delete(rel)
        obj.appearance_settings[key] = ""
        obj.save()
        return Response(status=204)


