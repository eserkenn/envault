"""Compare two vault files and produce a structured similarity/difference report."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

from envault.vault import Vault


class CompareError(Exception):
    """Raised when vault comparison fails."""


@dataclass
class CompareResult:
    only_in_left: List[str] = field(default_factory=list)
    only_in_right: List[str] = field(default_factory=list)
    in_both_same: List[str] = field(default_factory=list)
    in_both_different: List[str] = field(default_factory=list)

    @property
    def all_keys(self) -> Set[str]:
        return set(
            self.only_in_left
            + self.only_in_right
            + self.in_both_same
            + self.in_both_different
        )

    @property
    def is_identical(self) -> bool:
        return (
            not self.only_in_left
            and not self.only_in_right
            and not self.in_both_different
        )

    @property
    def similarity_pct(self) -> float:
        total = len(self.all_keys)
        if total == 0:
            return 100.0
        return round(len(self.in_both_same) / total * 100, 1)


def compare_vaults(
    left_path: Path,
    left_password: str,
    right_path: Path,
    right_password: str,
) -> CompareResult:
    """Compare two vaults and return a structured CompareResult."""
    try:
        left = Vault(left_path, left_password)
        right = Vault(right_path, right_password)
    except Exception as exc:
        raise CompareError(f"Failed to open vault: {exc}") from exc

    left_keys: Set[str] = set(left.list_keys())
    right_keys: Set[str] = set(right.list_keys())

    result = CompareResult()
    result.only_in_left = sorted(left_keys - right_keys)
    result.only_in_right = sorted(right_keys - left_keys)

    for key in sorted(left_keys & right_keys):
        if left.get(key) == right.get(key):
            result.in_both_same.append(key)
        else:
            result.in_both_different.append(key)

    return result
