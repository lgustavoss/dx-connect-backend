from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Config
from core.serializers import ConfigSerializer
from core.serializers.chat import ChatSettingsSerializer
from core.serializers.company import CompanyDataSerializer
from core.serializers.email import EmailSettingsSerializer
from core.utils import get_or_create_config_with_defaults


class ConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self) -> Config:
        obj, _ = get_or_create_config_with_defaults()
        return obj

    def get(self, _request):
        obj = self.get_object()
        data = ConfigSerializer(obj).data
        return Response(data)

    def put(self, request):
        obj = self.get_object()
        serializer = ConfigSerializer(instance=obj, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompanyConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, _request):
        obj, _ = get_or_create_config_with_defaults()
        return Response(CompanyDataSerializer(obj.company_data).data)

    def patch(self, request):
        obj, _ = get_or_create_config_with_defaults()
        serializer = CompanyDataSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = {**obj.company_data, **serializer.validated_data}
        obj.company_data = updated
        obj.full_clean()
        obj.save()
        return Response(CompanyDataSerializer(obj.company_data).data)


class ChatConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, _request):
        obj, _ = get_or_create_config_with_defaults()
        return Response(ChatSettingsSerializer(obj.chat_settings).data)

    def patch(self, request):
        obj, _ = get_or_create_config_with_defaults()
        serializer = ChatSettingsSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = {**obj.chat_settings, **serializer.validated_data}
        obj.chat_settings = updated
        obj.full_clean()
        obj.save()
        return Response(ChatSettingsSerializer(obj.chat_settings).data)


class EmailConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, _request):
        obj, _ = get_or_create_config_with_defaults()
        data = obj.get_decrypted_email_settings()
        return Response(EmailSettingsSerializer(data).data)

    def patch(self, request):
        obj, _ = get_or_create_config_with_defaults()
        serializer = EmailSettingsSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = {**obj.get_decrypted_email_settings(), **serializer.validated_data}
        obj.email_settings = updated
        obj.full_clean()
        obj.save()
        # mascarar resposta
        masked = obj.email_settings.copy()
        if masked.get("smtp_senha"):
            masked["smtp_senha"] = "***"
        return Response(masked)
