from __future__ import annotations

from typing import Any, Dict, Optional

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .crypto import decrypt_string, encrypt_string
from .validators import validate_chat_settings, validate_company_data, validate_email_settings


class Config(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    company_data = models.JSONField(default=dict, blank=True)
    chat_settings = models.JSONField(default=dict, blank=True)
    email_settings = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Configuração")
        verbose_name_plural = _("Configurações")
        constraints = [
            models.UniqueConstraint(models.Value(1), name="config_singleton", violation_error_message="Apenas uma configuração é permitida.")
        ]

    def clean(self) -> None:
        errors: Dict[str, Any] = {}
        try:
            validate_company_data(self.company_data or {})
        except ValidationError as exc:
            errors.update(exc.message_dict)
        try:
            validate_chat_settings(self.chat_settings or {})
        except ValidationError as exc:
            errors.update(exc.message_dict)
        try:
            validate_email_settings(self.email_settings or {})
        except ValidationError as exc:
            errors.update(exc.message_dict)
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs) -> None:
        # criptografar smtp_senha se estiver em plain-text
        email = dict(self.email_settings or {})
        smtp_senha: Optional[str] = email.get("smtp_senha")
        if smtp_senha and not (smtp_senha.startswith("gAAAA") or smtp_senha.startswith("eyJ")):
            email["smtp_senha"] = encrypt_string(smtp_senha)
            self.email_settings = email
        super().save(*args, **kwargs)

    def get_decrypted_email_settings(self) -> Dict[str, Any]:
        email = dict(self.email_settings or {})
        token = email.get("smtp_senha")
        if token:
            plain = decrypt_string(str(token))
            if plain is not None:
                email["smtp_senha"] = plain
        return email
