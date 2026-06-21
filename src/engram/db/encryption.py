"""Application-level field encryption using Fernet (AES-256)."""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet


def derive_key(passphrase: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    if salt is None:
        salt = os.urandom(16)
    key_material = hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, 100_000)
    key = base64.urlsafe_b64encode(key_material)
    return key, salt


class FieldEncryptor:

    def __init__(self, key: bytes) -> None:
        self._fernet = Fernet(key)

    @classmethod
    def from_passphrase(cls, passphrase: str, salt: bytes | None = None) -> tuple[FieldEncryptor, bytes]:
        key, salt = derive_key(passphrase, salt)
        return cls(key), salt

    @classmethod
    def from_key_string(cls, key_string: str) -> FieldEncryptor:
        return cls(key_string.encode())

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self._fernet.decrypt(ciphertext.encode()).decode()
