"""Expiration tracking for vault secrets."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional


class ExpirationError(Exception):
    """Raised when expiration operations fail."""


@dataclass
class ExpirationEntry:
    key: str
    expires_on: date
    days_remaining: int
    is_expired: bool


def _expiration_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".expiry.json")


def _load_expirations(vault_path: Path) -> dict:
    path = _expiration_path(vault_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_expirations(vault_path: Path, data: dict) -> None:
    _expiration_path(vault_path).write_text(json.dumps(data, indent=2))


def set_expiration(vault_path: Path, key: str, expires_on: date) -> None:
    """Set an expiration date for a secret key."""
    if not vault_path.exists():
        raise ExpirationError(f"Vault not found: {vault_path}")
    data = _load_expirations(vault_path)
    data[key] = expires_on.isoformat()
    _save_expirations(vault_path, data)


def remove_expiration(vault_path: Path, key: str) -> bool:
    """Remove expiration for a key. Returns True if removed, False if not set."""
    data = _load_expirations(vault_path)
    if key not in data:
        return False
    del data[key]
    _save_expirations(vault_path, data)
    return True


def check_expirations(
    vault_path: Path,
    warn_within_days: int = 7,
    reference_date: Optional[date] = None,
) -> List[ExpirationEntry]:
    """Return expiration entries for keys that are expired or expiring soon."""
    today = reference_date or date.today()
    data = _load_expirations(vault_path)
    results: List[ExpirationEntry] = []
    for key, iso in data.items():
        expires_on = date.fromisoformat(iso)
        delta = (expires_on - today).days
        if delta <= warn_within_days:
            results.append(
                ExpirationEntry(
                    key=key,
                    expires_on=expires_on,
                    days_remaining=delta,
                    is_expired=delta < 0,
                )
            )
    results.sort(key=lambda e: e.expires_on)
    return results


def list_expirations(vault_path: Path) -> List[ExpirationEntry]:
    """Return all expiration entries regardless of proximity."""
    today = date.today()
    data = _load_expirations(vault_path)
    entries = [
        ExpirationEntry(
            key=key,
            expires_on=date.fromisoformat(iso),
            days_remaining=(date.fromisoformat(iso) - today).days,
            is_expired=(date.fromisoformat(iso) - today).days < 0,
        )
        for key, iso in data.items()
    ]
    entries.sort(key=lambda e: e.expires_on)
    return entries
