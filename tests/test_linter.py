"""Tests for envault.linter."""

from __future__ import annotations

import pytest

from envault.linter import LintIssue, LintResult, lint_vault


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeVault:
    """Minimal vault stub for linter tests."""

    def __init__(self, secrets: dict[str, str]):
        self._secrets = secrets

    def list_keys(self) -> list[str]:
        return list(self._secrets.keys())

    def get(self, key: str, password: str) -> str:  # noqa: ARG002
        return self._secrets[key]


# ---------------------------------------------------------------------------
# LintResult helpers
# ---------------------------------------------------------------------------

class TestLintResult:
    def test_has_errors_true(self):
        result = LintResult(issues=[LintIssue(key="K", severity="error", message="x")])
        assert result.has_errors is True

    def test_has_errors_false_when_only_warnings(self):
        result = LintResult(issues=[LintIssue(key="K", severity="warning", message="x")])
        assert result.has_errors is False

    def test_has_warnings_true(self):
        result = LintResult(issues=[LintIssue(key="K", severity="warning", message="x")])
        assert result.has_warnings is True

    def test_empty_result_has_no_issues(self):
        result = LintResult()
        assert not result.has_errors
        assert not result.has_warnings
        assert result.issues == []


# ---------------------------------------------------------------------------
# lint_vault checks
# ---------------------------------------------------------------------------

class TestLintVault:
    PASSWORD = "hunter2"

    def test_clean_vault_returns_no_issues(self):
        vault = _FakeVault({"DATABASE_URL": "postgres://localhost/mydb"})
        result = lint_vault(vault, self.PASSWORD)
        assert result.issues == []

    def test_empty_value_is_error(self):
        vault = _FakeVault({"API_KEY": ""})
        result = lint_vault(vault, self.PASSWORD)
        assert any(i.severity == "error" and i.key == "API_KEY" for i in result.issues)

    def test_whitespace_only_value_is_error(self):
        vault = _FakeVault({"API_KEY": "   "})
        result = lint_vault(vault, self.PASSWORD)
        assert any(i.severity == "error" for i in result.issues)

    def test_weak_key_prefix_is_warning(self):
        vault = _FakeVault({"TEST_SECRET": "supersecretvalue"})
        result = lint_vault(vault, self.PASSWORD)
        assert any(i.severity == "warning" and "prefix" in i.message for i in result.issues)

    def test_short_value_is_warning(self):
        vault = _FakeVault({"TOKEN": "abc"})
        result = lint_vault(vault, self.PASSWORD)
        assert any(i.severity == "warning" and "short" in i.message for i in result.issues)

    def test_multiple_issues_collected(self):
        vault = _FakeVault(
            {
                "TEST_KEY": "x",   # weak prefix warning + short value warning
                "EMPTY_SECRET": "",  # empty value error
            }
        )
        result = lint_vault(vault, self.PASSWORD)
        # At least one error and at least one warning should be present
        assert result.has_errors
        assert result.has_warnings
        assert len(result.issues) >= 2
