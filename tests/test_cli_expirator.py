"""Tests for envault.cli_expirator."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.cli_expirator import expire_group
from envault.expirator import ExpirationEntry, set_expiration


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.vault"
    path.write_text("{}")
    return path


class TestSetCmd:
    def test_outputs_confirmation(self, runner: CliRunner, vault_file: Path) -> None:
        result = runner.invoke(expire_group, ["set", str(vault_file), "API_KEY", "2030-12-31"])
        assert result.exit_code == 0
        assert "API_KEY" in result.output
        assert "2030-12-31" in result.output

    def test_invalid_date_exits_nonzero(self, runner: CliRunner, vault_file: Path) -> None:
        result = runner.invoke(expire_group, ["set", str(vault_file), "KEY", "not-a-date"])
        assert result.exit_code != 0
        assert "invalid date" in result.output.lower() or "error" in result.output.lower()

    def test_missing_vault_exits_nonzero(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(expire_group, ["set", str(tmp_path / "ghost.vault"), "K", "2030-01-01"])
        assert result.exit_code != 0


class TestRemoveCmd:
    def test_outputs_removed_message(self, runner: CliRunner, vault_file: Path) -> None:
        set_expiration(vault_file, "API_KEY", date(2030, 1, 1))
        result = runner.invoke(expire_group, ["remove", str(vault_file), "API_KEY"])
        assert result.exit_code == 0
        assert "removed" in result.output.lower()

    def test_outputs_not_set_message(self, runner: CliRunner, vault_file: Path) -> None:
        result = runner.invoke(expire_group, ["remove", str(vault_file), "MISSING"])
        assert result.exit_code == 0
        assert "no expiration" in result.output.lower()


class TestListCmd:
    def test_shows_all_keys(self, runner: CliRunner, vault_file: Path) -> None:
        set_expiration(vault_file, "KEY_A", date(2035, 3, 1))
        set_expiration(vault_file, "KEY_B", date(2036, 7, 15))
        result = runner.invoke(expire_group, ["list", str(vault_file)])
        assert "KEY_A" in result.output
        assert "KEY_B" in result.output

    def test_empty_vault_message(self, runner: CliRunner, vault_file: Path) -> None:
        result = runner.invoke(expire_group, ["list", str(vault_file)])
        assert "no expiration" in result.output.lower()


class TestCheckCmd:
    def test_exits_zero_when_all_ok(self, runner: CliRunner, vault_file: Path) -> None:
        far = date.today() + timedelta(days=60)
        set_expiration(vault_file, "SAFE", far)
        result = runner.invoke(expire_group, ["check", str(vault_file), "--warn-days", "7"])
        assert result.exit_code == 0

    def test_exits_nonzero_when_expired(self, runner: CliRunner, vault_file: Path) -> None:
        past = date.today() - timedelta(days=1)
        set_expiration(vault_file, "OLD", past)
        result = runner.invoke(expire_group, ["check", str(vault_file)])
        assert result.exit_code != 0
        assert "EXPIRED" in result.output or "OLD" in result.output
