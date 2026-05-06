"""Tests for envault.cli_scheduler."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.cli_scheduler import schedule_group
from envault.scheduler import ScheduleEntry, set_schedule


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "vault.env"


class TestSetCmd:
    def test_outputs_schedule_confirmation(self, runner: CliRunner, vault_path: Path) -> None:
        result = runner.invoke(schedule_group, ["set", str(vault_path), "DB_PASS", "--every", "30"])
        assert result.exit_code == 0
        assert "DB_PASS" in result.output
        assert "30 day" in result.output

    def test_invalid_interval_shows_error(self, runner: CliRunner, vault_path: Path) -> None:
        result = runner.invoke(schedule_group, ["set", str(vault_path), "KEY", "--every", "0"])
        assert result.exit_code != 0
        assert "Error" in result.output


class TestRemoveCmd:
    def test_remove_existing_key(self, runner: CliRunner, vault_path: Path) -> None:
        set_schedule(vault_path, "TOKEN", 60)
        result = runner.invoke(schedule_group, ["remove", str(vault_path), "TOKEN"])
        assert result.exit_code == 0
        assert "removed" in result.output

    def test_remove_missing_key_message(self, runner: CliRunner, vault_path: Path) -> None:
        result = runner.invoke(schedule_group, ["remove", str(vault_path), "GHOST"])
        assert result.exit_code == 0
        assert "No schedule" in result.output


class TestListCmd:
    def test_shows_all_keys(self, runner: CliRunner, vault_path: Path) -> None:
        set_schedule(vault_path, "API_KEY", 90)
        set_schedule(vault_path, "DB_PASS", 30)
        result = runner.invoke(schedule_group, ["list", str(vault_path)])
        assert "API_KEY" in result.output
        assert "DB_PASS" in result.output

    def test_empty_vault_message(self, runner: CliRunner, vault_path: Path) -> None:
        result = runner.invoke(schedule_group, ["list", str(vault_path)])
        assert "No schedules" in result.output


class TestDueCmd:
    def test_shows_overdue_keys(self, runner: CliRunner, vault_path: Path) -> None:
        old = (datetime.utcnow() - timedelta(days=100)).isoformat()
        set_schedule(vault_path, "STALE", 30, last_rotated=old)
        result = runner.invoke(schedule_group, ["due", str(vault_path)])
        assert "STALE" in result.output

    def test_no_due_keys_message(self, runner: CliRunner, vault_path: Path) -> None:
        set_schedule(vault_path, "FRESH", 90)
        result = runner.invoke(schedule_group, ["due", str(vault_path)])
        assert "No keys are due" in result.output
