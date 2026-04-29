"""Vault snapshot: create and restore point-in-time backups of a vault."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List

from envault.vault import Vault, VaultError


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def create_snapshot(vault_path: Path, password: str, snapshots_dir: Path) -> Path:
    """Decrypt all secrets from *vault_path* and write a timestamped snapshot.

    Returns the path of the newly created snapshot file.
    """
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    vault = Vault(vault_path, password)
    keys = vault.list_keys()

    if not keys:
        raise SnapshotError("Vault is empty — nothing to snapshot.")

    data: Dict[str, str] = {}
    for key in keys:
        data[key] = vault.get(key)

    timestamp = int(time.time())
    snapshot_file = snapshots_dir / f"snapshot_{timestamp}.json"

    snapshot_file.write_text(
        json.dumps({"timestamp": timestamp, "secrets": data}, indent=2),
        encoding="utf-8",
    )
    return snapshot_file


def list_snapshots(snapshots_dir: Path) -> List[Path]:
    """Return snapshot files sorted from oldest to newest."""
    if not snapshots_dir.exists():
        return []
    return sorted(snapshots_dir.glob("snapshot_*.json"))


def restore_snapshot(snapshot_file: Path, vault_path: Path, password: str) -> List[str]:
    """Restore secrets from *snapshot_file* into the vault at *vault_path*.

    Existing keys are overwritten.  Returns the list of restored key names.
    """
    if not snapshot_file.exists():
        raise SnapshotError(f"Snapshot file not found: {snapshot_file}")

    try:
        payload = json.loads(snapshot_file.read_text(encoding="utf-8"))
        secrets: Dict[str, str] = payload["secrets"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise SnapshotError(f"Invalid snapshot file: {exc}") from exc

    vault = Vault(vault_path, password)
    for key, value in secrets.items():
        vault.set(key, value)

    return list(secrets.keys())
