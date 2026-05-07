"""Vault inspector: surface metadata and health info about a vault file."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.vault import Vault, VaultError


class InspectError(Exception):
    """Raised when inspection fails."""


@dataclass
class InspectResult:
    vault_path: Path
    total_keys: int
    file_size_bytes: int
    has_targets: bool
    has_audit_log: bool
    key_names: List[str] = field(default_factory=list)
    longest_key: Optional[str] = None
    shortest_key: Optional[str] = None

    @property
    def avg_key_length(self) -> float:
        if not self.key_names:
            return 0.0
        return sum(len(k) for k in self.key_names) / len(self.key_names)


def inspect_vault(vault_path: Path, password: str) -> InspectResult:
    """Inspect a vault and return a structured summary of its metadata."""
    if not vault_path.exists():
        raise InspectError(f"Vault file not found: {vault_path}")

    try:
        vault = Vault(vault_path, password)
    except VaultError as exc:
        raise InspectError(str(exc)) from exc

    keys = vault.list_keys()
    file_size = vault_path.stat().st_size

    targets_path = vault_path.with_suffix(".targets.json")
    audit_path = vault_path.with_suffix(".audit.jsonl")

    longest = max(keys, key=len, default=None)
    shortest = min(keys, key=len, default=None)

    return InspectResult(
        vault_path=vault_path,
        total_keys=len(keys),
        file_size_bytes=file_size,
        has_targets=targets_path.exists(),
        has_audit_log=audit_path.exists(),
        key_names=sorted(keys),
        longest_key=longest,
        shortest_key=shortest,
    )
