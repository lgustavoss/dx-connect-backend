import base64
import hashlib
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


def _get_fernet() -> Fernet:
    key: Optional[str] = os.getenv("CONFIG_CRYPTO_KEY")
    if key:
        raw = key.encode("utf-8")
    else:
        # Deriva uma chave a partir do SECRET_KEY quando não houver chave própria
        secret = os.getenv("DJANGO_SECRET_KEY", "dev-secret").encode("utf-8")
        raw = hashlib.sha256(secret).digest()
    # Fernet espera key base64-url de 32 bytes
    b32 = base64.urlsafe_b64encode(raw[:32])
    return Fernet(b32)


def encrypt_string(plaintext: str) -> str:
    f = _get_fernet()
    token = f.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_string(token: str) -> Optional[str]:
    f = _get_fernet()
    try:
        value = f.decrypt(token.encode("utf-8"))
        return value.decode("utf-8")
    except (InvalidToken, ValueError):
        return None
