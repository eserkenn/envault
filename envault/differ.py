"""Diff secrets between two targets or between a target and a local file."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from envault.vault import Vault, VaultError


class DiffError(Exception):
    """Raised when a diff operation fails."""


@dataclass
class DiffEntry:
    key: str
    status: str  # 'added', 'removed', 'changed', 'unchanged'
    left_value: Optional[str] = None
    right_value: Optional[str] = None


def diff_vaults(
    left_vault: Vault,
    left_password: str,
    right_vault: Vault,
    right_password: str,
) -> List[DiffEntry]:
    """Compare secrets in two vault instances and return a list of DiffEntry."""
    try:
        left_secrets = _read_all(left_vault, left_password)
    except VaultError as exc:
        raise DiffError(f"Failed to read left vault: {exc}") from exc

    try:
        right_secrets = _read_all(right_vault, right_password)
    except VaultError as exc:
        raise DiffError(f"Failed to read right vault: {exc}") from exc

    return _compute_diff(left_secrets, right_secrets)


def _read_all(vault: Vault, password: str) -> Dict[str, str]:
    """Decrypt and return all secrets from a vault."""
    result: Dict[str, str] = {}
    for key in vault.list_keys():
        result[key] = vault.get(key, password)
    return result


def _compute_diff(
    left: Dict[str, str],
    right: Dict[str, str],
) -> List[DiffEntry]:
    """Produce a sorted list of DiffEntry objects from two secret dicts."""
    entries: List[DiffEntry] = []
    all_keys = sorted(set(left) | set(right))

    for key in all_keys:
        if key in left and key not in right:
            entries.append(DiffEntry(key=key, status="removed", left_value=left[key]))
        elif key not in left and key in right:
            entries.append(DiffEntry(key=key, status="added", right_value=right[key]))
        elif left[key] != right[key]:
            entries.append(
                DiffEntry(
                    key=key,
                    status="changed",
                    left_value=left[key],
                    right_value=right[key],
                )
            )
        else:
            entries.append(
                DiffEntry(
                    key=key,
                    status="unchanged",
                    left_value=left[key],
                    right_value=right[key],
                )
            )

    return entries
