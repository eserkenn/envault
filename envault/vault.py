"""Vault module for storing and retrieving encrypted environment variables."""

import json
import os
from pathlib import Path
from typing import Optional

from envault.crypto import derive_key, encrypt, decrypt

DEFAULT_VAULT_FILE = ".envault"


class VaultError(Exception):
    """Raised when a vault operation fails."""


class Vault:
    """Manages encrypted environment variables stored in a JSON vault file."""

    def __init__(self, path: str = DEFAULT_VAULT_FILE, target: str = "default"):
        self.path = Path(path)
        self.target = target
        self._data: dict = {}

    def _load(self) -> None:
        """Load vault data from disk."""
        if not self.path.exists():
            self._data = {}
            return
        try:
            with open(self.path, "r") as f:
                self._data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise VaultError(f"Failed to read vault file: {e}") from e

    def _save(self) -> None:
        """Persist vault data to disk."""
        try:
            with open(self.path, "w") as f:
                json.dump(self._data, f, indent=2)
        except OSError as e:
            raise VaultError(f"Failed to write vault file: {e}") from e

    def set(self, key: str, value: str, password: str) -> None:
        """Encrypt and store an environment variable."""
        self._load()
        derived_key, salt = derive_key(password)
        token = encrypt(derived_key, value)
        self._data.setdefault(self.target, {})[key] = {
            "salt": salt.hex(),
            "token": token.hex(),
        }
        self._save()

    def get(self, key: str, password: str) -> str:
        """Retrieve and decrypt an environment variable."""
        self._load()
        target_data = self._data.get(self.target, {})
        entry = target_data.get(key)
        if entry is None:
            raise VaultError(f"Key '{key}' not found in target '{self.target}'")
        salt = bytes.fromhex(entry["salt"])
        token = bytes.fromhex(entry["token"])
        derived_key, _ = derive_key(password, salt=salt)
        return decrypt(derived_key, token)

    def delete(self, key: str) -> None:
        """Remove an environment variable from the vault."""
        self._load()
        target_data = self._data.get(self.target, {})
        if key not in target_data:
            raise VaultError(f"Key '{key}' not found in target '{self.target}'")
        del target_data[key]
        self._save()

    def list_keys(self) -> list[str]:
        """Return all stored keys for the current target."""
        self._load()
        return list(self._data.get(self.target, {}).keys())
