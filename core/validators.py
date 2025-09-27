import re
from typing import Any, Dict

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from integrations.validators import validate_cnpj, validate_uf


def _require_keys(data: Dict[str, Any], keys: Dict[str, bool], path: str = "") -> None:
    for key, required in keys.items():
        if required and key not in data:
            raise ValidationError({path + key: "Campo obrigatório ausente"})


def validate_company_data(data: Dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValidationError({"company_data": "Deve ser um objeto"})
    required = {
        "razao_social": True,
        "nome_fantasia": True,
        "cnpj": True,
        "inscricao_estadual": True,
        "inscricao_municipal": False,
        "regime_tributario": True,
        "cnae_principal": False,
        "telefone": True,
        "email": True,
        "site": False,
        "endereco": True,
    }
    _require_keys(data, required, "company_data.")

    try:
        validate_cnpj(data["cnpj"])  # validação algorítmica
    except ValidationError:
        raise ValidationError({"company_data.cnpj": "CNPJ inválido"})
    if str(data["regime_tributario"]) not in {"1", "2", "3"}:
        raise ValidationError({"company_data.regime_tributario": "Valor inválido"})

    EmailValidator()(data["email"])

    endereco = data.get("endereco", {})
    _require_keys(
        endereco,
        {
            "cep": True,
            "logradouro": True,
            "numero": True,
            "complemento": False,
            "bairro": True,
            "cidade": True,
            "uf": True,
        },
        "company_data.endereco.",
    )
    if not re.fullmatch(r"\d{8}", str(endereco["cep"])):
        raise ValidationError({"company_data.endereco.cep": "CEP deve conter 8 dígitos"})
    try:
        validate_uf(endereco["uf"])
    except ValidationError:
        raise ValidationError({"company_data.endereco.uf": "UF inválida"})


def validate_chat_settings(data: Dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValidationError({"chat_settings": "Deve ser um objeto"})
    required = {
        "mensagem_saudacao": True,
        "mensagem_fora_expediente": True,
        "mensagem_encerramento": True,
        "mensagem_inatividade": True,
        "timeout_inatividade_minutos": True,
        "limite_chats_simultaneos": True,
        "horario_funcionamento": True,
    }
    _require_keys(data, required, "chat_settings.")


def validate_email_settings(data: Dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValidationError({"email_settings": "Deve ser um objeto"})
    required = {
        "smtp_host": True,
        "smtp_port": True,
        "smtp_usuario": True,
        "smtp_senha": True,
        "smtp_ssl": True,
        "email_from": True,
    }
    _require_keys(data, required, "email_settings.")
    # Validar email apenas se houver valor (permite defaults vazios no init)
    if data.get("email_from"):
        EmailValidator()(data["email_from"])


def validate_whatsapp_settings(data: Dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValidationError({"whatsapp_settings": "Deve ser um objeto"})
    required = {
        "enabled": True,
        "device_name": True,
        "stealth_mode": True,
        "human_delays": True,
        "reconnect_backoff_seconds": True,
        # segredos opcionais
        "session_data": False,
        "proxy_url": False,
    }
    _require_keys(data, required, "whatsapp_settings.")
    # validações simples
    if int(data.get("reconnect_backoff_seconds", 0)) < 0:
        raise ValidationError({"whatsapp_settings.reconnect_backoff_seconds": "Deve ser >= 0"})