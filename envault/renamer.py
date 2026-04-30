"""Rename keys across a vault, with optional dry-run support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from envault.vault import Vault, VaultError


class RenameError(Exception):
    """Raised when a rename operation fails."""


@dataclass
class RenameResult:
    old_key: str
    new_key: str
    success: bool
    message: str = ""


def rename_key(
    vault: Vault,
    password: str,
    old_key: str,
    new_key: str,
    *,
    overwrite: bool = False,
) -> RenameResult:
    """Rename a single key inside *vault*.

    Args:
        vault: An open :class:`~envault.vault.Vault` instance.
        password: Master password used to decrypt / re-encrypt the value.
        old_key: Existing key name.
        new_key: Desired key name.
        overwrite: When *True*, silently replace *new_key* if it already exists.

    Returns:
        A :class:`RenameResult` describing the outcome.

    Raises:
        RenameError: If *old_key* does not exist or *new_key* already exists
            and *overwrite* is *False*.
    """
    keys = vault.list_keys()

    if old_key not in keys:
        raise RenameError(f"Key '{old_key}' does not exist in the vault.")

    if new_key in keys and not overwrite:
        raise RenameError(
            f"Key '{new_key}' already exists. Use --overwrite to replace it."
        )

    try:
        value = vault.get(old_key, password)
    except VaultError as exc:
        raise RenameError(f"Could not decrypt '{old_key}': {exc}") from exc

    vault.set(new_key, value, password)
    vault.delete(old_key)

    return RenameResult(old_key=old_key, new_key=new_key, success=True)


def bulk_rename(
    vault: Vault,
    password: str,
    pairs: List[tuple[str, str]],
    *,
    overwrite: bool = False,
) -> List[RenameResult]:
    """Rename multiple keys in one call.

    Processes each pair independently; a failure in one pair does not abort
    the remaining renames.
    """
    results: List[RenameResult] = []
    for old_key, new_key in pairs:
        try:
            result = rename_key(vault, password, old_key, new_key, overwrite=overwrite)
        except RenameError as exc:
            result = RenameResult(
                old_key=old_key, new_key=new_key, success=False, message=str(exc)
            )
        results.append(result)
    return results
