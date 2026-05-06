"""Tests for envault.validator."""

from __future__ import annotations

import pytest

from envault.validator import (
    ValidationSeverity,
    ValidatorError,
    validate_secrets,
)


class _FakeVault:
    def __init__(self, secrets: dict[str, str]) -> None:
        self._secrets = secrets

    def list_keys(self) -> list[str]:
        return list(self._secrets.keys())

    def get(self, key: str) -> str:
        return self._secrets[key]


@pytest.fixture()
def vault() -> _FakeVault:
    return _FakeVault({
        "DB_HOST": "localhost",
        "API_KEY": "s3cr3t",
        "bad-key": "value",
        "EMPTY_VAL": "   ",
        "PLACEHOLDER": "changeme",
        "LONG_VAL": "x" * 5000,
    })


def test_valid_key_produces_no_issues() -> None:
    v = _FakeVault({"DB_HOST": "localhost"})
    result = validate_secrets(v)
    assert not result.issues


def test_bad_key_format_is_warning(vault: _FakeVault) -> None:
    result = validate_secrets(vault, keys=["bad-key"])
    severities = [i.severity for i in result.issues]
    assert ValidationSeverity.WARNING in severities


def test_empty_value_is_warning(vault: _FakeVault) -> None:
    result = validate_secrets(vault, keys=["EMPTY_VAL"])
    assert any("empty" in i.message.lower() for i in result.issues)
    assert result.has_warnings()


def test_placeholder_value_is_error(vault: _FakeVault) -> None:
    result = validate_secrets(vault, keys=["PLACEHOLDER"])
    assert result.has_errors()
    assert any("placeholder" in i.message.lower() for i in result.issues)


def test_long_value_is_error(vault: _FakeVault) -> None:
    result = validate_secrets(vault, keys=["LONG_VAL"])
    assert result.has_errors()
    assert any("exceeds" in i.message for i in result.issues)


def test_unknown_key_raises(vault: _FakeVault) -> None:
    with pytest.raises(ValidatorError, match="not found"):
        validate_secrets(vault, keys=["DOES_NOT_EXIST"])


def test_has_errors_false_when_only_warnings(vault: _FakeVault) -> None:
    result = validate_secrets(vault, keys=["EMPTY_VAL"])
    assert not result.has_errors()
    assert result.has_warnings()


def test_all_keys_validated_by_default(vault: _FakeVault) -> None:
    result = validate_secrets(vault)
    keys_with_issues = {i.key for i in result.issues}
    assert "bad-key" in keys_with_issues
    assert "PLACEHOLDER" in keys_with_issues
