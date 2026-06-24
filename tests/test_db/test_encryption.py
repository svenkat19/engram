from __future__ import annotations

from yonakh.db.encryption import FieldEncryptor


def test_encrypt_decrypt():
    enc, salt = FieldEncryptor.from_passphrase("test-secret")
    plaintext = "sensitive content here"
    ciphertext = enc.encrypt(plaintext)
    assert ciphertext != plaintext
    assert enc.decrypt(ciphertext) == plaintext


def test_from_passphrase_deterministic_with_salt():
    enc1, salt = FieldEncryptor.from_passphrase("my-key")
    enc2, _ = FieldEncryptor.from_passphrase("my-key", salt=salt)
    plaintext = "hello world"
    ciphertext = enc1.encrypt(plaintext)
    assert enc2.decrypt(ciphertext) == plaintext


def test_crypto_service_disabled_by_default():
    from yonakh.db import crypto_service
    assert crypto_service.encrypt("hello") == "hello"
    assert crypto_service.decrypt("hello") == "hello"
    assert crypto_service.encrypt(None) is None
    assert crypto_service.decrypt(None) is None
