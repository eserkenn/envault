"""Tests for envault.cli_rename."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_rename import rename_group
from envault.renamer import RenameError, RenameResult


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def mock_rename():
    with patch("envault.cli_rename.rename_key") as m:
        m.return_value = RenameResult(old_key="OLD", new_key="NEW", success=True)
        yield m


@pytest.fixture()
def mock_vault():
    with patch("envault.cli_rename.Vault") as m:
        yield m


class TestRunRename:
    def test_outputs_success_message(self, runner, mock_vault, mock_rename) -> None:
        result = runner.invoke(
            rename_group,
            ["key", "vault.json", "OLD", "NEW", "--password", "secret"],
        )
        assert result.exit_code == 0
        assert "OLD" in result.output
        assert "NEW" in result.output

    def test_rename_error_exits_nonzero(self, runner, mock_vault, mock_rename) -> None:
        mock_rename.side_effect = RenameError("Key 'OLD' does not exist in the vault.")
        result = runner.invoke(
            rename_group,
            ["key", "vault.json", "OLD", "NEW", "--password", "secret"],
        )
        assert result.exit_code != 0
        assert "does not exist" in result.output


class TestRunBulkRename:
    def test_bulk_success_lists_all(self, runner, mock_vault) -> None:
        with patch("envault.cli_rename.bulk_rename") as mock_bulk:
            mock_bulk.return_value = [
                RenameResult(old_key="A", new_key="A2", success=True),
                RenameResult(old_key="B", new_key="B2", success=True),
            ]
            result = runner.invoke(
                rename_group,
                [
                    "bulk",
                    "vault.json",
                    "--map", "A", "A2",
                    "--map", "B", "B2",
                    "--password", "secret",
                ],
            )
        assert result.exit_code == 0
        assert "A2" in result.output
        assert "B2" in result.output

    def test_partial_failure_exits_nonzero(self, runner, mock_vault) -> None:
        with patch("envault.cli_rename.bulk_rename") as mock_bulk:
            mock_bulk.return_value = [
                RenameResult(old_key="X", new_key="Y", success=False, message="not found"),
            ]
            result = runner.invoke(
                rename_group,
                ["bulk", "vault.json", "--map", "X", "Y", "--password", "secret"],
            )
        assert result.exit_code != 0
