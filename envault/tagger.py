"""Tag management for vault secrets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envault.vault import Vault, VaultError


class TaggerError(Exception):
    """Raised when a tagging operation fails."""


@dataclass
class TagResult:
    key: str
    tags: List[str] = field(default_factory=list)


def add_tags(vault: Vault, key: str, tags: List[str]) -> TagResult:
    """Add one or more tags to a secret key."""
    if key not in vault.list_keys():
        raise TaggerError(f"Key '{key}' does not exist in vault.")
    existing = _get_tags(vault, key)
    merged = sorted(set(existing) | set(tags))
    _set_tags(vault, key, merged)
    return TagResult(key=key, tags=merged)


def remove_tags(vault: Vault, key: str, tags: List[str]) -> TagResult:
    """Remove one or more tags from a secret key."""
    if key not in vault.list_keys():
        raise TaggerError(f"Key '{key}' does not exist in vault.")
    existing = _get_tags(vault, key)
    remaining = sorted(set(existing) - set(tags))
    _set_tags(vault, key, remaining)
    return TagResult(key=key, tags=remaining)


def list_by_tag(vault: Vault, tag: str) -> List[str]:
    """Return all keys that have the given tag."""
    return sorted(
        key for key in vault.list_keys() if tag in _get_tags(vault, key)
    )


def get_tags(vault: Vault, key: str) -> TagResult:
    """Return the tags for a given key."""
    if key not in vault.list_keys():
        raise TaggerError(f"Key '{key}' does not exist in vault.")
    return TagResult(key=key, tags=_get_tags(vault, key))


def all_tags(vault: Vault) -> Dict[str, List[str]]:
    """Return a mapping of key -> tags for all keys in the vault."""
    return {key: _get_tags(vault, key) for key in vault.list_keys()}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_TAG_PREFIX = "__tags__"


def _tag_meta_key(key: str) -> str:
    return f"{_TAG_PREFIX}{key}"


def _get_tags(vault: Vault, key: str) -> List[str]:
    meta_key = _tag_meta_key(key)
    try:
        raw = vault.get(meta_key)
        return [t for t in raw.split(",") if t]
    except (VaultError, KeyError):
        return []


def _set_tags(vault: Vault, key: str, tags: List[str]) -> None:
    meta_key = _tag_meta_key(key)
    vault.set(meta_key, ",".join(tags))
