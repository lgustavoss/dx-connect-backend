from typing import Any, Dict

from rest_framework import serializers

from core.defaults import (
    DEFAULT_CHAT_SETTINGS,
    DEFAULT_COMPANY_DATA,
    DEFAULT_EMAIL_SETTINGS,
)
from core.models import Config
from core.serializers.chat import ChatSettingsSerializer
from core.serializers.company import CompanyDataSerializer
from core.serializers.email import EmailSettingsSerializer


class ConfigSerializer(serializers.ModelSerializer):
    company_data = CompanyDataSerializer()
    chat_settings = ChatSettingsSerializer()
    email_settings = EmailSettingsSerializer()

    class Meta:
        model = Config
        fields = [
            "id",
            "company_data",
            "chat_settings",
            "email_settings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def to_internal_value(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data = super().to_internal_value(data)
        return data

    def to_representation(self, instance: Config) -> Dict[str, Any]:
        data = super().to_representation(instance)
        email = dict(data.get("email_settings") or {})
        if "smtp_senha" in email and email.get("smtp_senha"):
            email["smtp_senha"] = "***"
        data["email_settings"] = email
        return data

    @staticmethod
    def defaults() -> Dict[str, Any]:
        return {
            "company_data": DEFAULT_COMPANY_DATA,
            "chat_settings": DEFAULT_CHAT_SETTINGS,
            "email_settings": DEFAULT_EMAIL_SETTINGS,
        }
