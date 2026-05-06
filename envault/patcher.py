"""Patch (in-place update) multiple vault keys using a mapping or file."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envault.vault import Vault, VaultError


class PatchError(Exception):
    """Raised when a patch operation fails."""


@dataclass
class PatchResult:
    updated: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


def patch_vault(
    vault_path: Path,
    password: str,
    updates: Dict[str, str],
    *,
    skip_missing: bool = False,
) -> PatchResult:
    """Apply *updates* to an existing vault, optionally skipping unknown keys.

    Args:
        vault_path: Path to the vault file.
        password: Master password for the vault.
        updates: Mapping of key -> new plaintext value.
        skip_missing: When *True*, keys that do not already exist in the vault
            are recorded in ``result.skipped`` instead of raising an error.

    Returns:
        A :class:`PatchResult` describing what happened.

    Raises:
        PatchError: If the vault cannot be opened or a key is missing and
            *skip_missing* is *False*.
    """
    if not updates:
        raise PatchError("No updates provided")

    try:
        vault = Vault(vault_path, password)
    except VaultError as exc:
        raise PatchError(f"Cannot open vault: {exc}") from exc

    existing_keys = set(vault.list_keys())
    result = PatchResult()

    for key, value in updates.items():
        if key not in existing_keys:
            if skip_missing:
                result.skipped.append(key)
                continue
            raise PatchError(
                f"Key '{key}' does not exist in vault. "
                "Use --skip-missing to ignore absent keys."
            )
        try:
            vault.set(key, value)
            result.updated.append(key)
        except VaultError as exc:
            result.errors[key] = str(exc)

    return result
