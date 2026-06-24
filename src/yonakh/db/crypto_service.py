from __future__ import annotations

from yonakh.config import get_settings
from yonakh.db.encryption import FieldEncryptor


_encryptor: FieldEncryptor | None = None
_initialized = False


def _ensure_init() -> None:
    global _encryptor, _initialized
    if _initialized:
        return
    _initialized = True
    settings = get_settings()
    if settings.encryption_enabled and settings.encryption_key:
        _encryptor = FieldEncryptor.from_key_string(settings.encryption_key)


def is_enabled() -> bool:
    _ensure_init()
    return _encryptor is not None


def encrypt(plaintext: str | None) -> str | None:
    if plaintext is None:
        return None
    _ensure_init()
    if _encryptor is None:
        return plaintext
    return _encryptor.encrypt(plaintext)


def decrypt(ciphertext: str | None) -> str | None:
    if ciphertext is None:
        return None
    _ensure_init()
    if _encryptor is None:
        return ciphertext
    return _encryptor.decrypt(ciphertext)
