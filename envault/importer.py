"""Import environment variables from .env or JSON files into the vault."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from envault.vault import Vault, VaultError


class ImportError(Exception):
    """Raised when an import operation fails."""


def import_secrets(vault: Vault, source: Path, fmt: str, overwrite: bool = False) -> Dict[str, str]:
    """Import key/value pairs from *source* into *vault*.

    Returns a mapping of keys that were imported.
    Raises ImportError on parse or vault errors.
    """
    if not source.exists():
        raise ImportError(f"Source file not found: {source}")

    try:
        raw = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise ImportError(f"Cannot read source file: {exc}") from exc

    if fmt == "dotenv":
        pairs = _parse_dotenv(raw)
    elif fmt == "json":
        pairs = _parse_json(raw)
    else:
        raise ImportError(f"Unsupported import format: {fmt!r}")

    imported: Dict[str, str] = {}
    for key, value in pairs.items():
        if not overwrite and vault.has(key):
            continue
        try:
            vault.set(key, value)
            imported[key] = value
        except VaultError as exc:
            raise ImportError(f"Failed to store key {key!r}: {exc}") from exc

    return imported


def _parse_dotenv(text: str) -> Dict[str, str]:
    """Parse a .env formatted string into a dict."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            result[key] = value
    return result


def _parse_json(text: str) -> Dict[str, str]:
    """Parse a JSON object into a dict of strings."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ImportError("JSON root must be an object")
    return {str(k): str(v) for k, v in data.items()}
