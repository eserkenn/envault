"""Encryption and decryption utilities for envault using Fernet symmetric encryption."""

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


SALT_SIZE = 16
ITERATIONS = 480_000


def derive_key(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """Derive a Fernet-compatible key from a password using PBKDF2.

    Returns:
        A tuple of (key, salt) where key is base64-encoded and ready for Fernet.
    """
    if salt is None:
        salt = os.urandom(SALT_SIZE)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


def encrypt(plaintext: str, password: str) -> bytes:
    """Encrypt a plaintext string with a password.

    Returns:
        Raw bytes containing the salt prepended to the Fernet token.
    """
    key, salt = derive_key(password)
    fernet = Fernet(key)
    token = fernet.encrypt(plaintext.encode())
    return salt + token


def decrypt(ciphertext: bytes, password: str) -> str:
    """Decrypt bytes produced by :func:`encrypt`.

    Raises:
        ValueError: If the password is incorrect or the data is corrupted.
    """
    salt = ciphertext[:SALT_SIZE]
    token = ciphertext[SALT_SIZE:]

    key, _ = derive_key(password, salt=salt)
    fernet = Fernet(key)

    try:
        return fernet.decrypt(token).decode()
    except InvalidToken as exc:
        raise ValueError("Decryption failed: invalid password or corrupted data.") from exc
