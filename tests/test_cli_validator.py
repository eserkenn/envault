"""Tests for envault.cli_validator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_validator import validate_group
from envault.validator import ValidationIssue, ValidationResult, ValidationSeverity


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def mock_vault(tmp_path):
    vault_file = tmp_path / "vault.env"
    vault_file.write_bytes(b"placeholder")
    with patch("envault.cli_validator.Vault") as mock:
        yield mock, str(vault_file)


@pytest.fixture()
def mock_validate():
    with patch("envault.cli_validator.validate_secrets") as mock:
        yield mock


class TestRunValidate:
    def test_clean_vault_prints_success(self, runner, mock_vault, mock_validate):
        mock_validate.return_value = ValidationResult(issues=[])
        _, path = mock_vault
        result = runner.invoke(validate_group, ["run", path, "--password", "pw"])
        assert result.exit_code == 0
        assert "passed validation" in result.output

    def test_errors_cause_nonzero_exit(self, runner, mock_vault, mock_validate):
        mock_validate.return_value = ValidationResult(issues=[
            ValidationIssue(key="FOO", message="bad value", severity=ValidationSeverity.ERROR)
        ])
        _, path = mock_vault
        result = runner.invoke(validate_group, ["run", path, "--password", "pw"])
        assert result.exit_code != 0
        assert "ERROR" in result.output

    def test_warnings_do_not_cause_exit_without_strict(self, runner, mock_vault, mock_validate):
        mock_validate.return_value = ValidationResult(issues=[
            ValidationIssue(key="FOO", message="warning msg", severity=ValidationSeverity.WARNING)
        ])
        _, path = mock_vault
        result = runner.invoke(validate_group, ["run", path, "--password", "pw"])
        assert result.exit_code == 0

    def test_warnings_cause_exit_with_strict(self, runner, mock_vault, mock_validate):
        mock_validate.return_value = ValidationResult(issues=[
            ValidationIssue(key="FOO", message="warning msg", severity=ValidationSeverity.WARNING)
        ])
        _, path = mock_vault
        result = runner.invoke(validate_group, ["run", path, "--password", "pw", "--strict"])
        assert result.exit_code != 0

    def test_validator_error_prints_message(self, runner, mock_vault, mock_validate):
        from envault.validator import ValidatorError
        mock_validate.side_effect = ValidatorError("key not found")
        _, path = mock_vault
        result = runner.invoke(validate_group, ["run", path, "--password", "pw"])
        assert result.exit_code != 0
        assert "Error" in result.output
