"""Audit log for vault operations (set, delete, rotate, import, export)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

AUDIT_FILE = ".envault_audit.json"


class AuditError(Exception):
    """Raised when an audit log operation fails."""


def _audit_path(vault_path: str) -> Path:
    base = Path(vault_path).parent
    return base / AUDIT_FILE


def record_event(
    vault_path: str,
    action: str,
    keys: Optional[List[str]] = None,
    target: Optional[str] = None,
    actor: Optional[str] = None,
) -> dict:
    """Append an audit event to the log file and return the event dict."""
    path = _audit_path(vault_path)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "keys": keys or [],
        "target": target,
        "actor": actor or os.environ.get("USER", "unknown"),
    }

    try:
        if path.exists():
            with path.open("r") as fh:
                log: List[dict] = json.load(fh)
        else:
            log = []

        log.append(entry)

        with path.open("w") as fh:
            json.dump(log, fh, indent=2)
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"Failed to write audit log: {exc}") from exc

    return entry


def read_log(vault_path: str) -> List[dict]:
    """Return all audit log entries for the given vault."""
    path = _audit_path(vault_path)
    if not path.exists():
        return []

    try:
        with path.open("r") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"Failed to read audit log: {exc}") from exc
