from __future__ import annotations

from typing import Any, Dict, Optional

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .crypto import decrypt_string, encrypt_string
from .validators import (
    validate_chat_settings,
    validate_company_data,
    validate_document_templates,
    validate_email_settings,
)


class Config(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    company_data = models.JSONField(default=dict, blank=True)
    chat_settings = models.JSONField(default=dict, blank=True)
    email_settings = models.JSONField(default=dict, blank=True)
    appearance_settings = models.JSONField(default=dict, blank=True)
    whatsapp_settings = models.JSONField(default=dict, blank=True)
    document_templates = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Configuração")
        verbose_name_plural = _("Configurações")
        constraints = [
            models.UniqueConstraint(models.Value(1), name="config_singleton", violation_error_message="Apenas uma configuração é permitida.")
        ]
        permissions = (
            ("manage_config_company", "Pode gerenciar Config - Company"),
            ("manage_config_chat", "Pode gerenciar Config - Chat"),
            ("manage_config_email", "Pode gerenciar Config - Email"),
            ("manage_config_appearance", "Pode gerenciar Config - Appearance"),
            ("manage_config_whatsapp", "Pode gerenciar Config - WhatsApp"),
            ("manage_config_documents", "Pode gerenciar Config - Document Templates"),
        )

    def clean(self) -> None:
        errors: Dict[str, Any] = {}
        for fn, section, value in (
            (validate_company_data, "company_data", self.company_data or {}),
            (validate_chat_settings, "chat_settings", self.chat_settings or {}),
            (validate_email_settings, "email_settings", self.email_settings or {}),
            (validate_document_templates, "document_templates", self.document_templates or {}),
        ):
            try:
                fn(value)
            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    errors.update(exc.message_dict)
                else:
                    errors[section] = exc.messages
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs) -> None:
        # criptografar smtp_senha se estiver em plain-text
        email = dict(self.email_settings or {})
        smtp_senha: Optional[str] = email.get("smtp_senha")
        if smtp_senha and not (smtp_senha.startswith("gAAAA") or smtp_senha.startswith("eyJ")):
            email["smtp_senha"] = encrypt_string(smtp_senha)
            self.email_settings = email
        # criptografar segredos do WhatsApp se em plain-text
        wa = dict(self.whatsapp_settings or {})
        for secret_key in ("session_data", "proxy_url"):
            val: Optional[str] = wa.get(secret_key)
            if val and not (str(val).startswith("gAAAA") or str(val).startswith("eyJ")):
                wa[secret_key] = encrypt_string(str(val))
        self.whatsapp_settings = wa
        super().save(*args, **kwargs)

    def get_decrypted_email_settings(self) -> Dict[str, Any]:
        email = dict(self.email_settings or {})
        token = email.get("smtp_senha")
        if token:
            plain = decrypt_string(str(token))
            if plain is not None:
                email["smtp_senha"] = plain
        return email

    def get_decrypted_whatsapp_settings(self) -> Dict[str, Any]:
        wa = dict(self.whatsapp_settings or {})
        for secret_key in ("session_data", "proxy_url"):
            token = wa.get(secret_key)
            if token:
                plain = decrypt_string(str(token))
                if plain is not None:
                    wa[secret_key] = plain
        return wa
