"""Criptografia do token WhatsApp em repouso (Fernet)."""
import base64
import hashlib
import os


def _get_key():
    secret = os.environ.get("PLATFORM_WHATSAPP_ENCRYPT_KEY", "").strip() or os.environ.get("PLATFORM_JWT_SECRET", "change-me")
    raw = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(raw)


def encrypt_token(token: str) -> str:
    from cryptography.fernet import Fernet
    return Fernet(_get_key()).encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    from cryptography.fernet import Fernet
    return Fernet(_get_key()).decrypt(encrypted.encode()).decode()
