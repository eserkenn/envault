"""Tests for envault.cli_comparator."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_comparator import compare_group
from envault.comparator import CompareError, CompareResult


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_files(tmp_path: Path):
    left = tmp_path / "left.vault"
    right = tmp_path / "right.vault"
    left.touch()
    right.touch()
    return left, right


def _invoke(runner, left, right, result, show_same=False):
    args = ["run", str(left), str(right),
            "--left-password", "pw", "--right-password", "pw"]
    if show_same:
        args.append("--show-same")
    with patch("envault.cli_comparator.compare_vaults", return_value=result):
        return runner.invoke(compare_group, args)


class TestRunCompare:
    def test_identical_vaults_message(self, runner, vault_files):
        left, right = vault_files
        result = CompareResult(in_both_same=["KEY"])
        out = _invoke(runner, left, right, result)
        assert "identical" in out.output.lower()

    def test_shows_only_in_left(self, runner, vault_files):
        left, right = vault_files
        result = CompareResult(only_in_left=["ALPHA"], in_both_different=["X"])
        out = _invoke(runner, left, right, result)
        assert "ALPHA" in out.output
        assert "only in left" in out.output

    def test_shows_only_in_right(self, runner, vault_files):
        left, right = vault_files
        result = CompareResult(only_in_right=["BETA"], in_both_different=["X"])
        out = _invoke(runner, left, right, result)
        assert "BETA" in out.output
        assert "only in right" in out.output

    def test_shows_different_keys(self, runner, vault_files):
        left, right = vault_files
        result = CompareResult(in_both_different=["DB_PASS"])
        out = _invoke(runner, left, right, result)
        assert "DB_PASS" in out.output
        assert "value differs" in out.output

    def test_show_same_flag(self, runner, vault_files):
        left, right = vault_files
        result = CompareResult(in_both_same=["STABLE"], in_both_different=["X"])
        out = _invoke(runner, left, right, result, show_same=True)
        assert "STABLE" in out.output
        assert "identical" in out.output

    def test_compare_error_shown(self, runner, vault_files):
        left, right = vault_files
        with patch("envault.cli_comparator.compare_vaults", side_effect=CompareError("bad")):
            out = runner.invoke(
                compare_group,
                ["run", str(left), str(right), "--left-password", "pw", "--right-password", "pw"],
            )
        assert out.exit_code != 0
        assert "bad" in out.output
