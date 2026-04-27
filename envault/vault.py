"""Vault storage for encrypted environment variables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from envault.crypto import encrypt, decrypt, derive_key


class VaultError(Exception):
    """Raised when a vault operation fails."""


class Vault:
    """Manages an encrypted key/value store persisted to disk."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: Dict[str, dict] = {}
        self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text())
            except (json.JSONDecodeError, OSError) as exc:
                raise VaultError(f"Cannot read vault file: {exc}") from exc

    def _save(self) -> None:
        try:
            self.path.write_text(json.dumps(self._data, indent=2))
        except OSError as exc:
            raise VaultError(f"Cannot write vault file: {exc}") from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set(self, key: str, value: str, password: str) -> None:
        """Encrypt *value* and store it under *key*."""
        key_bytes, salt = derive_key(password)
        token = encrypt(value.encode(), key_bytes)
        self._data[key] = {"token": token, "salt": salt}
        self._save()

    def get(self, key: str, password: str) -> str:
        """Retrieve and decrypt the value stored under *key*."""
        if key not in self._data:
            raise VaultError(f"Key '{key}' not found in vault.")
        entry = self._data[key]
        key_bytes, _ = derive_key(password, salt=entry["salt"])
        try:
            return decrypt(entry["token"], key_bytes).decode()
        except Exception as exc:
            raise VaultError(f"Decryption failed for '{key}': {exc}") from exc

    def delete(self, key: str) -> None:
        """Remove *key* from the vault."""
        if key not in self._data:
            raise VaultError(f"Key '{key}' not found in vault.")
        del self._data[key]
        self._save()

    def list_keys(self) -> list[str]:
        """Return a sorted list of all stored keys."""
        return sorted(self._data.keys())

    def get_all(self, password: str) -> Dict[str, str]:
        """Decrypt and return all key/value pairs."""
        result: Dict[str, str] = {}
        for key in self._data:
            result[key] = self.get(key, password)
        return result
