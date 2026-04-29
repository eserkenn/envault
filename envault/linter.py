"""Lint vault secrets for common issues such as empty values, weak names, or duplicates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envault.vault import Vault


class LintError(Exception):
    """Raised when the linter cannot complete its checks."""


@dataclass
class LintIssue:
    key: str
    severity: str  # "warning" | "error"
    message: str


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)


_WEAK_PREFIXES = ("test", "tmp", "temp", "debug", "foo", "bar")


def lint_vault(vault: Vault, password: str) -> LintResult:
    """Run all lint checks against the decrypted contents of *vault*.

    Args:
        vault: An open :class:`~envault.vault.Vault` instance.
        password: Master password used to decrypt secrets.

    Returns:
        A :class:`LintResult` containing any discovered issues.
    """
    try:
        keys = vault.list_keys()
    except Exception as exc:  # pragma: no cover
        raise LintError(f"Failed to read vault: {exc}") from exc

    result = LintResult()

    for key in keys:
        value = vault.get(key, password)

        # Check for empty values
        if not value or not value.strip():
            result.issues.append(
                LintIssue(key=key, severity="error", message="Secret value is empty.")
            )
            continue

        # Check for keys that look like placeholders
        lower = key.lower()
        for prefix in _WEAK_PREFIXES:
            if lower.startswith(prefix):
                result.issues.append(
                    LintIssue(
                        key=key,
                        severity="warning",
                        message=f"Key name starts with suspicious prefix '{prefix}'.",
                    )
                )
                break

        # Check for very short values (likely placeholders)
        if len(value.strip()) < 8:
            result.issues.append(
                LintIssue(
                    key=key,
                    severity="warning",
                    message="Secret value is suspiciously short (< 8 characters).",
                )
            )

    return result
