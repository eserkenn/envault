"""Integration tests: CLI commands persist and read back correctly."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_expirator import expire_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "secrets.vault"
    path.write_text("{}")
    return path


def test_set_then_list_shows_key(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(expire_group, ["set", str(vault_file), "DB_PASS", "2032-05-10"])
    result = runner.invoke(expire_group, ["list", str(vault_file)])
    assert "DB_PASS" in result.output
    assert "2032-05-10" in result.output


def test_set_then_remove_clears_key(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(expire_group, ["set", str(vault_file), "TOKEN", "2032-01-01"])
    runner.invoke(expire_group, ["remove", str(vault_file), "TOKEN"])
    expiry_file = vault_file.with_suffix(".expiry.json")
    data = json.loads(expiry_file.read_text())
    assert "TOKEN" not in data


def test_check_reports_expired_and_exits_nonzero(runner: CliRunner, vault_file: Path) -> None:
    past = (date.today() - timedelta(days=5)).isoformat()
    runner.invoke(expire_group, ["set", str(vault_file), "STALE", past])
    result = runner.invoke(expire_group, ["check", str(vault_file)])
    assert result.exit_code != 0
    assert "STALE" in result.output


def test_multiple_keys_sorted_in_list(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(expire_group, ["set", str(vault_file), "Z_KEY", "2033-12-01"])
    runner.invoke(expire_group, ["set", str(vault_file), "A_KEY", "2031-03-01"])
    result = runner.invoke(expire_group, ["list", str(vault_file)])
    idx_a = result.output.index("A_KEY")
    idx_z = result.output.index("Z_KEY")
    assert idx_a < idx_z


def test_overwrite_expiry_via_cli(runner: CliRunner, vault_file: Path) -> None:
    runner.invoke(expire_group, ["set", str(vault_file), "API_KEY", "2030-01-01"])
    runner.invoke(expire_group, ["set", str(vault_file), "API_KEY", "2035-06-30"])
    expiry_file = vault_file.with_suffix(".expiry.json")
    data = json.loads(expiry_file.read_text())
    assert data["API_KEY"] == "2035-06-30"
