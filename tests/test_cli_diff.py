"""Tests for envault.cli_diff module."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch

from envault.cli_diff import run_diff
from envault.differ import DiffEntry


@pytest.fixture()
def runner():
    return CliRunner()


def _make_entries(*specs):
    """Helper: specs are (key, status) tuples."""
    entries = []
    for key, status in specs:
        entries.append(
            DiffEntry(
                key=key,
                status=status,
                left_value="old" if status in ("removed", "changed", "unchanged") else None,
                right_value="new" if status in ("added", "changed", "unchanged") else None,
            )
        )
    return entries


class TestRunDiff:
    @patch("envault.cli_diff.diff_vaults")
    @patch("envault.cli_diff.Vault")
    def test_shows_added_key(self, mock_vault_cls, mock_diff, runner, tmp_path):
        left = tmp_path / "left.vault"
        right = tmp_path / "right.vault"
        left.write_text("{}")
        right.write_text("{}")
        mock_diff.return_value = _make_entries(("NEW_KEY", "added"))

        result = runner.invoke(
            run_diff,
            [str(left), str(right), "--left-password", "p", "--right-password", "p"],
        )
        assert result.exit_code == 0
        assert "NEW_KEY" in result.output
        assert "+" in result.output

    @patch("envault.cli_diff.diff_vaults")
    @patch("envault.cli_diff.Vault")
    def test_hides_unchanged_by_default(self, mock_vault_cls, mock_diff, runner, tmp_path):
        left = tmp_path / "left.vault"
        right = tmp_path / "right.vault"
        left.write_text("{}")
        right.write_text("{}")
        mock_diff.return_value = _make_entries(("SAME_KEY", "unchanged"))

        result = runner.invoke(
            run_diff,
            [str(left), str(right), "--left-password", "p", "--right-password", "p"],
        )
        assert result.exit_code == 0
        assert "No differences found" in result.output

    @patch("envault.cli_diff.diff_vaults")
    @patch("envault.cli_diff.Vault")
    def test_shows_unchanged_with_flag(self, mock_vault_cls, mock_diff, runner, tmp_path):
        left = tmp_path / "left.vault"
        right = tmp_path / "right.vault"
        left.write_text("{}")
        right.write_text("{}")
        mock_diff.return_value = _make_entries(("SAME_KEY", "unchanged"))

        result = runner.invoke(
            run_diff,
            [str(left), str(right), "--left-password", "p", "--right-password", "p", "--show-unchanged"],
        )
        assert result.exit_code == 0
        assert "SAME_KEY" in result.output

    @patch("envault.cli_diff.diff_vaults")
    @patch("envault.cli_diff.Vault")
    def test_diff_error_exits_nonzero(self, mock_vault_cls, mock_diff, runner, tmp_path):
        from envault.differ import DiffError
        left = tmp_path / "left.vault"
        right = tmp_path / "right.vault"
        left.write_text("{}")
        right.write_text("{}")
        mock_diff.side_effect = DiffError("bad password")

        result = runner.invoke(
            run_diff,
            [str(left), str(right), "--left-password", "p", "--right-password", "p"],
        )
        assert result.exit_code != 0
        assert "bad password" in result.output
