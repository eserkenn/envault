"""Clone secrets from one vault to another with optional key filtering."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.vault import Vault, VaultError


class CloneError(Exception):
    """Raised when a vault clone operation fails."""


@dataclass
class CloneResult:
    cloned: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def total_cloned(self) -> int:
        return len(self.cloned)


def clone_vault(
    source_path: Path,
    source_password: str,
    dest_path: Path,
    dest_password: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> CloneResult:
    """Copy secrets from *source_path* into *dest_path*.

    Args:
        source_path: Path to the source vault file.
        source_password: Master password for the source vault.
        dest_path: Path to the destination vault file.
        dest_password: Master password for the destination vault.
        keys: Optional explicit list of keys to clone. Clones all keys when *None*.
        overwrite: When *True*, existing keys in the destination are overwritten.

    Returns:
        A :class:`CloneResult` describing what was cloned, skipped, or errored.
    """
    try:
        src = Vault(source_path, source_password)
    except VaultError as exc:
        raise CloneError(f"Cannot open source vault: {exc}") from exc

    try:
        dst = Vault(dest_path, dest_password)
    except VaultError as exc:
        raise CloneError(f"Cannot open destination vault: {exc}") from exc

    all_keys = src.list_keys()
    target_keys = keys if keys is not None else all_keys

    result = CloneResult()

    for key in target_keys:
        if key not in all_keys:
            result.errors.append(key)
            continue

        if key in dst.list_keys() and not overwrite:
            result.skipped.append(key)
            continue

        try:
            value = src.get(key)
            dst.set(key, value)
            result.cloned.append(key)
        except VaultError as exc:
            result.errors.append(f"{key}: {exc}")

    return result
