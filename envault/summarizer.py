"""Vault summary and statistics reporting."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from envault.vault import Vault


class SummaryError(Exception):
    """Raised when summary generation fails."""


@dataclass
class VaultSummary:
    total_keys: int = 0
    tagged_keys: int = 0
    untagged_keys: int = 0
    unique_tags: list[str] = field(default_factory=list)
    key_lengths: dict[str, int] = field(default_factory=dict)
    longest_key: str | None = None
    shortest_key: str | None = None
    avg_value_length: float = 0.0


def summarize_vault(vault: "Vault", password: str) -> VaultSummary:
    """Generate a statistical summary of the vault contents."""
    try:
        keys = vault.list_keys()
    except Exception as exc:
        raise SummaryError(f"Failed to read vault: {exc}") from exc

    if not keys:
        return VaultSummary()

    tag_set: set[str] = set()
    tagged_count = 0
    value_lengths: list[int] = []
    key_lengths: dict[str, int] = {}

    for key in keys:
        value = vault.get(key, password)
        value_lengths.append(len(value))
        key_lengths[key] = len(key)

        meta = vault.get_meta(key) if hasattr(vault, "get_meta") else {}
        tags = meta.get("tags", []) if meta else []
        if tags:
            tagged_count += 1
            tag_set.update(tags)

    sorted_by_len = sorted(key_lengths, key=lambda k: key_lengths[k])

    return VaultSummary(
        total_keys=len(keys),
        tagged_keys=tagged_count,
        untagged_keys=len(keys) - tagged_count,
        unique_tags=sorted(tag_set),
        key_lengths=key_lengths,
        longest_key=sorted_by_len[-1] if sorted_by_len else None,
        shortest_key=sorted_by_len[0] if sorted_by_len else None,
        avg_value_length=round(sum(value_lengths) / len(value_lengths), 2),
    )
