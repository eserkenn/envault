"""Key rotation logic for envault vaults."""

from __future__ import annotations

from typing import TYPE_CHECKING

from envault.crypto import derive_key, decrypt, encrypt
from envault.vault import Vault, VaultError

if TYPE_CHECKING:
    pass


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate_key(
    vault_path: str,
    old_password: str,
    new_password: str,
) -> list[str]:
    """Re-encrypt all secrets in *vault_path* under *new_password*.

    Returns the list of rotated key names.

    Raises RotationError on any failure; the vault is left untouched.
    """
    old_vault = Vault(vault_path, old_password)
    keys = old_vault.list_keys()

    if not keys:
        return []

    # Decrypt everything with the old password first.
    plaintext: dict[str, str] = {}
    for k in keys:
        try:
            plaintext[k] = old_vault.get(k)
        except VaultError as exc:
            raise RotationError(f"Failed to decrypt '{k}' with old password: {exc}") from exc

    # Re-encrypt under the new password.
    new_vault = Vault(vault_path, new_password)
    try:
        for k, v in plaintext.items():
            new_vault.set(k, v)
    except VaultError as exc:
        raise RotationError(f"Failed to re-encrypt secrets: {exc}") from exc

    return keys
