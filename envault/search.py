"""Search and filter secrets across a vault by key pattern or value metadata."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from typing import List, Optional

from envault.vault import Vault, VaultError


class SearchError(Exception):
    """Raised when a search operation fails."""


@dataclass
class SearchResult:
    key: str
    matched_by: str  # 'key' or 'value'


def search_vault(
    vault: Vault,
    password: str,
    pattern: str,
    search_values: bool = False,
    use_regex: bool = False,
) -> List[SearchResult]:
    """Search vault keys (and optionally values) for a given pattern.

    Args:
        vault: An open Vault instance.
        password: Password to decrypt secrets when searching values.
        pattern: Glob pattern (or regex if use_regex=True) to match against.
        search_values: If True, also decrypt and search secret values.
        use_regex: If True, treat pattern as a regular expression.

    Returns:
        List of SearchResult objects for matching entries.

    Raises:
        SearchError: On regex compilation failure or vault access error.
    """
    try:
        keys: List[str] = vault.list_keys()
    except VaultError as exc:
        raise SearchError(f"Failed to list vault keys: {exc}") from exc

    if use_regex:
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise SearchError(f"Invalid regex pattern '{pattern}': {exc}") from exc
        key_match = lambda s: bool(compiled.search(s))  # noqa: E731
    else:
        key_match = lambda s: fnmatch.fnmatch(s, pattern)  # noqa: E731

    results: List[SearchResult] = []

    for key in keys:
        if key_match(key):
            results.append(SearchResult(key=key, matched_by="key"))
            continue

        if search_values:
            try:
                value: Optional[str] = vault.get(key, password)
            except VaultError as exc:
                raise SearchError(f"Failed to decrypt '{key}': {exc}") from exc
            if value is not None and key_match(value):
                results.append(SearchResult(key=key, matched_by="value"))

    return results
