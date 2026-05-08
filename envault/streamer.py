"""Stream vault secrets to stdout in real-time with optional filtering."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Iterator

from envault.vault import Vault, VaultError


class StreamError(Exception):
    """Raised when streaming fails."""


@dataclass
class StreamRecord:
    key: str
    value: str
    index: int
    total: int


def stream_vault(
    vault: Vault,
    password: str,
    *,
    prefix: str | None = None,
    keys: list[str] | None = None,
) -> Iterator[StreamRecord]:
    """Yield decrypted secrets one by one from *vault*.

    Args:
        vault: An open :class:`Vault` instance.
        password: Master password used to decrypt values.
        prefix: If given, only yield keys that start with this string.
        keys: If given, only yield keys in this explicit list.

    Yields:
        :class:`StreamRecord` for each matching secret.

    Raises:
        StreamError: When decryption of any key fails.
    """
    try:
        all_keys: list[str] = vault.list_keys()
    except VaultError as exc:
        raise StreamError(f"Cannot list vault keys: {exc}") from exc

    candidates = all_keys
    if keys is not None:
        candidates = [k for k in all_keys if k in keys]
    if prefix is not None:
        candidates = [k for k in candidates if k.startswith(prefix)]

    total = len(candidates)
    for index, key in enumerate(candidates, start=1):
        try:
            value = vault.get(key, password)
        except VaultError as exc:
            raise StreamError(f"Failed to decrypt '{key}': {exc}") from exc
        yield StreamRecord(key=key, value=value, index=index, total=total)


def _render_record(record: StreamRecord, fmt: str) -> str:
    """Render a single :class:`StreamRecord` to a string."""
    if fmt == "json":
        return json.dumps({"key": record.key, "value": record.value})
    if fmt == "dotenv":
        safe = record.value.replace('"', '\\"')
        return f'{record.key}="{safe}"'
    # plain
    return f"{record.key}={record.value}"
