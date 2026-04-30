"""Merge secrets from one vault into another, with conflict resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from envault.vault import Vault, VaultError


class MergeError(Exception):
    """Raised when a merge operation fails."""


class ConflictStrategy(str, Enum):
    KEEP_SOURCE = "source"   # keep value from source vault (overwrite)
    KEEP_TARGET = "target"   # keep value already in target vault
    RAISE = "raise"          # abort on any conflict


@dataclass
class MergeResult:
    added: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)


def merge_vaults(
    source_path: str,
    source_password: str,
    target_path: str,
    target_password: str,
    strategy: ConflictStrategy = ConflictStrategy.KEEP_SOURCE,
    keys: List[str] | None = None,
) -> MergeResult:
    """Merge secrets from *source* into *target*.

    Args:
        source_path: Path to the source vault file.
        source_password: Password for the source vault.
        target_path: Path to the target vault file.
        target_password: Password for the target vault.
        strategy: How to handle keys that exist in both vaults.
        keys: Optional allowlist of keys to merge; merges all if ``None``.

    Returns:
        A :class:`MergeResult` describing what changed.

    Raises:
        MergeError: On I/O or decryption failures, or when *strategy* is
            ``RAISE`` and a conflict is detected.
    """
    try:
        source = Vault(source_path, source_password)
        target = Vault(target_path, target_password)
    except VaultError as exc:
        raise MergeError(f"Failed to open vault: {exc}") from exc

    source_keys = source.list_keys()
    if keys is not None:
        unknown = set(keys) - set(source_keys)
        if unknown:
            raise MergeError(f"Keys not found in source vault: {sorted(unknown)}")
        source_keys = [k for k in source_keys if k in keys]

    target_keys = set(target.list_keys())
    result = MergeResult()

    for key in source_keys:
        value = source.get(key)
        if key in target_keys:
            if strategy is ConflictStrategy.RAISE:
                result.conflicts.append(key)
            elif strategy is ConflictStrategy.KEEP_TARGET:
                result.skipped.append(key)
            else:  # KEEP_SOURCE
                target.set(key, value)
                result.overwritten.append(key)
        else:
            target.set(key, value)
            result.added.append(key)

    if result.has_conflicts:
        raise MergeError(
            f"Conflicts detected for keys: {result.conflicts}. "
            "Use --strategy=source or --strategy=target to resolve."
        )

    return result
