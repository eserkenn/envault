"""Tests for envault.crypto encryption/decryption utilities."""

import pytest

from envault.crypto import decrypt, derive_key, encrypt, SALT_SIZE


PASSWORD = "super-secret-passphrase"
PLAINTEXT = "DATABASE_URL=postgres://user:pass@localhost/db"


class TestDeriveKey:
    def test_returns_tuple_of_key_and_salt(self):
        key, salt = derive_key(PASSWORD)
        assert isinstance(key, bytes)
        assert isinstance(salt, bytes)

    def test_salt_has_correct_length(self):
        _, salt = derive_key(PASSWORD)
        assert len(salt) == SALT_SIZE

    def test_deterministic_with_same_salt(self):
        _, salt = derive_key(PASSWORD)
        key1, _ = derive_key(PASSWORD, salt=salt)
        key2, _ = derive_key(PASSWORD, salt=salt)
        assert key1 == key2

    def test_different_salts_produce_different_keys(self):
        key1, _ = derive_key(PASSWORD)
        key2, _ = derive_key(PASSWORD)
        # Extremely unlikely to collide with random salts
        assert key1 != key2


class TestEncryptDecrypt:
    def test_roundtrip(self):
        ciphertext = encrypt(PLAINTEXT, PASSWORD)
        assert decrypt(ciphertext, PASSWORD) == PLAINTEXT

    def test_ciphertext_is_bytes(self):
        assert isinstance(encrypt(PLAINTEXT, PASSWORD), bytes)

    def test_ciphertext_differs_each_call(self):
        """Fernet uses a random IV so two encryptions should differ."""
        ct1 = encrypt(PLAINTEXT, PASSWORD)
        ct2 = encrypt(PLAINTEXT, PASSWORD)
        assert ct1 != ct2

    def test_ciphertext_length_exceeds_salt(self):
        ct = encrypt(PLAINTEXT, PASSWORD)
        assert len(ct) > SALT_SIZE

    def test_wrong_password_raises_value_error(self):
        ct = encrypt(PLAINTEXT, PASSWORD)
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt(ct, "wrong-password")

    def test_corrupted_data_raises_value_error(self):
        ct = bytearray(encrypt(PLAINTEXT, PASSWORD))
        ct[-1] ^= 0xFF  # flip last byte
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt(bytes(ct), PASSWORD)

    def test_empty_string_roundtrip(self):
        ct = encrypt("", PASSWORD)
        assert decrypt(ct, PASSWORD) == ""

    def test_unicode_plaintext_roundtrip(self):
        unicode_text = "SECRET=caf\u00e9_中文_русский"
        ct = encrypt(unicode_text, PASSWORD)
        assert decrypt(ct, PASSWORD) == unicode_text
