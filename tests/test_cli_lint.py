import json
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from envault.cli_lint import run_lint
from envault.linter import LintResult, LintIssue


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_vault():
    with patch("envault.cli_lint.Vault") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        yield mock_cls


@pytest.fixture
def mock_lint():
    with patch("envault.cli_lint.lint_vault") as mock_fn:
        yield mock_fn


class TestRunLint:
    def test_no_issues_prints_clean_message(self, runner, mock_vault, mock_lint):
        mock_lint.return_value = LintResult(issues=[])
        result = runner.invoke(run_lint, ["vault.enc", "--password", "secret"])
        assert result.exit_code == 0
        assert "No issues found" in result.output

    def test_errors_cause_nonzero_exit(self, runner, mock_vault, mock_lint):
        issues = [LintIssue(key="API_KEY", severity="error", message="empty value")]
        mock_lint.return_value = LintResult(issues=issues)
        result = runner.invoke(run_lint, ["vault.enc", "--password", "secret"])
        assert result.exit_code == 1

    def test_warn_only_flag_exits_zero_on_errors(self, runner, mock_vault, mock_lint):
        issues = [LintIssue(key="DB_PASS", severity="error", message="empty value")]
        mock_lint.return_value = LintResult(issues=issues)
        result = runner.invoke(
            run_lint, ["vault.enc", "--password", "secret", "--warn-only"]
        )
        assert result.exit_code == 0

    def test_json_output_format(self, runner, mock_vault, mock_lint):
        issues = [LintIssue(key="TOKEN", severity="warning", message="looks short")]
        mock_lint.return_value = LintResult(issues=issues)
        result = runner.invoke(
            run_lint, ["vault.enc", "--password", "secret", "--format", "json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["warning_count"] == 1
        assert data["issues"][0]["key"] == "TOKEN"

    def test_vault_error_shown_as_cli_error(self, runner, mock_lint):
        from envault.vault import VaultError

        with patch("envault.cli_lint.Vault", side_effect=VaultError("bad password")):
            result = runner.invoke(run_lint, ["vault.enc", "--password", "wrong"])
        assert result.exit_code != 0
        assert "bad password" in result.output
