from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Config
from core.serializers import ConfigSerializer
from core.serializers.chat import ChatSettingsSerializer
from core.serializers.company import CompanyDataSerializer
from core.serializers.email import EmailSettingsSerializer
from core.serializers.appearance import AppearanceSettingsSerializer
from core.serializers.whatsapp import WhatsAppSettingsSerializer
from core.utils import get_or_create_config_with_defaults
from core.defaults import (
    DEFAULT_COMPANY_DATA,
    DEFAULT_CHAT_SETTINGS,
    DEFAULT_EMAIL_SETTINGS,
    DEFAULT_APPEARANCE_SETTINGS,
    DEFAULT_WHATSAPP_SETTINGS,
)
from drf_spectacular.utils import OpenApiExample, extend_schema


class ConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self) -> Config:
        obj, _ = get_or_create_config_with_defaults()
        return obj

    @extend_schema(
        operation_id="config_retrieve_all",
        summary="Obtém todas as configurações",
        responses={200: ConfigSerializer},
        examples=[
            OpenApiExample(
                "Exemplo de retorno",
                value=ConfigSerializer.defaults(),
            )
        ],
    )
    def get(self, _request):
        obj = self.get_object()
        data = ConfigSerializer(obj).data
        return Response(data)

    @extend_schema(
        operation_id="config_update_all",
        summary="Atualiza todas as configurações",
        request=ConfigSerializer,
        responses={200: ConfigSerializer},
    )
    def put(self, request):
        obj = self.get_object()
        serializer = ConfigSerializer(instance=obj, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompanyConfigView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="config_company_retrieve",
        summary="Obtém dados da empresa",
        responses={200: CompanyDataSerializer},
        examples=[OpenApiExample("Exemplo", value=DEFAULT_COMPANY_DATA)],
    )
    def get(self, _request):
        obj, _ = get_or_create_config_with_defaults()
        return Response(CompanyDataSerializer(obj.company_data).data)

    @extend_schema(
        operation_id="config_company_partial_update",
        summary="Atualiza parcialmente dados da empresa",
        request=CompanyDataSerializer,
        responses={200: CompanyDataSerializer},
        examples=[
            OpenApiExample(
                "Patch parcial",
                value={"razao_social": "Empresa X LTDA"},
            )
        ],
    )
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

    @extend_schema(
        operation_id="config_chat_retrieve",
        summary="Obtém configurações de chat",
        responses={200: ChatSettingsSerializer},
        examples=[OpenApiExample("Exemplo", value=DEFAULT_CHAT_SETTINGS)],
    )
    def get(self, _request):
        obj, _ = get_or_create_config_with_defaults()
        return Response(ChatSettingsSerializer(obj.chat_settings).data)

    @extend_schema(
        operation_id="config_chat_partial_update",
        summary="Atualiza parcialmente configurações de chat",
        request=ChatSettingsSerializer,
        responses={200: ChatSettingsSerializer},
        examples=[OpenApiExample("Patch parcial", value={"mensagem_saudacao": "Olá!"})],
    )
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

    @extend_schema(
        operation_id="config_email_retrieve",
        summary="Obtém configurações de e-mail (senha descriptografada)",
        responses={200: EmailSettingsSerializer},
        examples=[OpenApiExample("Exemplo", value=DEFAULT_EMAIL_SETTINGS)],
    )
    def get(self, _request):
        obj, _ = get_or_create_config_with_defaults()
        data = obj.get_decrypted_email_settings()
        return Response(EmailSettingsSerializer(data).data)

    @extend_schema(
        operation_id="config_email_partial_update",
        summary="Atualiza parcialmente configurações de e-mail",
        request=EmailSettingsSerializer,
        responses={200: EmailSettingsSerializer},
        examples=[OpenApiExample("Patch parcial", value={"smtp_host": "smtp.mailtrap.io"})],
    )
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


class AppearanceConfigView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="config_appearance_retrieve",
        summary="Obtém configurações de aparência",
        responses={200: AppearanceSettingsSerializer},
        examples=[OpenApiExample("Exemplo", value=DEFAULT_APPEARANCE_SETTINGS)],
    )
    def get(self, _request):
        obj, _ = get_or_create_config_with_defaults()
        return Response(AppearanceSettingsSerializer(obj.appearance_settings).data)

    @extend_schema(
        operation_id="config_appearance_partial_update",
        summary="Atualiza parcialmente configurações de aparência",
        request=AppearanceSettingsSerializer,
        responses={200: AppearanceSettingsSerializer},
        examples=[OpenApiExample("Patch parcial", value={"primary_color": "#2563eb"})],
    )
    def patch(self, request):
        obj, _ = get_or_create_config_with_defaults()
        serializer = AppearanceSettingsSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = {**obj.appearance_settings, **serializer.validated_data}
        obj.appearance_settings = updated
        obj.full_clean()
        obj.save()
        return Response(AppearanceSettingsSerializer(obj.appearance_settings).data)


class WhatsAppConfigView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="config_whatsapp_retrieve",
        summary="Obtém configurações do WhatsApp (segredos mascarados)",
        responses={200: WhatsAppSettingsSerializer},
        examples=[OpenApiExample("Exemplo", value=DEFAULT_WHATSAPP_SETTINGS)],
    )
    def get(self, _request):
        obj, _ = get_or_create_config_with_defaults()
        data = obj.get_decrypted_whatsapp_settings()
        # mascarar segredos
        masked = dict(data)
        for k in ("session_data", "proxy_url"):
            if masked.get(k):
                masked[k] = "***"
        return Response(masked)

    @extend_schema(
        operation_id="config_whatsapp_partial_update",
        summary="Atualiza parcialmente configurações do WhatsApp",
        request=WhatsAppSettingsSerializer,
        responses={200: WhatsAppSettingsSerializer},
        examples=[OpenApiExample("Patch parcial", value={"enabled": True})],
    )
    def patch(self, request):
        obj, _ = get_or_create_config_with_defaults()
        serializer = WhatsAppSettingsSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = {**obj.get_decrypted_whatsapp_settings(), **serializer.validated_data}
        obj.whatsapp_settings = updated
        obj.full_clean()
        obj.save()
        # resposta mascarada
        masked = dict(obj.whatsapp_settings)
        for k in ("session_data", "proxy_url"):
            if masked.get(k):
                masked[k] = "***"
        return Response(masked)
