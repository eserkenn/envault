"""Export vault secrets to various formats for deployment targets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from envault.vault import Vault, VaultError
from envault.targets import TargetManager, TargetError


class ExportError(Exception):
    """Raised when an export operation fails."""


SUPPORTED_FORMATS = ("dotenv", "json", "shell")


def export_secrets(
    vault: Vault,
    password: str,
    target: Optional[str] = None,
    fmt: str = "dotenv",
    output_path: Optional[Path] = None,
) -> str:
    """Decrypt and export secrets from the vault.

    Args:
        vault: An initialised Vault instance.
        password: Master password used to decrypt secrets.
        target: Optional target name to filter keys by prefix.
        fmt: Output format — one of 'dotenv', 'json', 'shell'.
        output_path: If provided, write output to this file.

    Returns:
        The exported content as a string.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ExportError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )

    try:
        secrets: Dict[str, str] = vault.get_all(password)
    except VaultError as exc:
        raise ExportError(f"Failed to read vault: {exc}") from exc

    if target is not None:
        prefix = f"{target}:"
        secrets = {
            key[len(prefix):]: value
            for key, value in secrets.items()
            if key.startswith(prefix)
        }

    content = _render(secrets, fmt)

    if output_path is not None:
        output_path.write_text(content)

    return content


def _render(secrets: Dict[str, str], fmt: str) -> str:
    if fmt == "dotenv":
        lines = [f"{key}={value}" for key, value in sorted(secrets.items())]
        return "\n".join(lines) + ("\n" if lines else "")

    if fmt == "json":
        return json.dumps(dict(sorted(secrets.items())), indent=2) + "\n"

    if fmt == "shell":
        lines = [f"export {key}={value}" for key, value in sorted(secrets.items())]
        return "\n".join(lines) + ("\n" if lines else "")

    raise ExportError(f"Unknown format: {fmt}")
