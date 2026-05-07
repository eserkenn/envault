"""Tests for envault.cli_profiler."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_profiler import profile_group
from envault.profiler import Profile, ProfileResult


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "vault.enc"
    path.write_text("{}")
    return path


class TestCreateCmd:
    def test_outputs_created_message(self, runner: CliRunner, vault_file: Path) -> None:
        with patch("envault.cli_profiler.create_profile", return_value=Profile(name="prod")) as mock_create:
            result = runner.invoke(profile_group, ["create", "prod", f"--vault={vault_file}"])
        assert result.exit_code == 0
        assert "prod" in result.output
        mock_create.assert_called_once()

    def test_error_on_duplicate(self, runner: CliRunner, vault_file: Path) -> None:
        from envault.profiler import ProfileError
        with patch("envault.cli_profiler.create_profile", side_effect=ProfileError("already exists")):
            result = runner.invoke(profile_group, ["create", "prod", f"--vault={vault_file}"])
        assert result.exit_code == 1
        assert "Error" in result.output


class TestAssignCmd:
    def test_outputs_assigned_keys(self, runner: CliRunner, vault_file: Path) -> None:
        mock_vault = MagicMock()
        mock_vault.list_keys.return_value = ["DB_URL", "API_KEY"]
        result_obj = ProfileResult(profile="prod", added=["DB_URL"], missing=[])
        with patch("envault.cli_profiler.Vault", return_value=mock_vault), \
             patch("envault.cli_profiler.assign_keys", return_value=result_obj):
            result = runner.invoke(
                profile_group,
                ["assign", "prod", "DB_URL", f"--vault={vault_file}", "--password=secret"],
            )
        assert result.exit_code == 0
        assert "DB_URL" in result.output

    def test_reports_missing_keys(self, runner: CliRunner, vault_file: Path) -> None:
        mock_vault = MagicMock()
        mock_vault.list_keys.return_value = []
        result_obj = ProfileResult(profile="prod", added=[], missing=["GHOST"])
        with patch("envault.cli_profiler.Vault", return_value=mock_vault), \
             patch("envault.cli_profiler.assign_keys", return_value=result_obj):
            result = runner.invoke(
                profile_group,
                ["assign", "prod", "GHOST", f"--vault={vault_file}", "--password=secret"],
            )
        assert "GHOST" in result.output


class TestListCmd:
    def test_empty_message_when_no_profiles(self, runner: CliRunner, vault_file: Path) -> None:
        with patch("envault.cli_profiler.list_profiles", return_value=[]):
            result = runner.invoke(profile_group, ["list", f"--vault={vault_file}"])
        assert "No profiles" in result.output

    def test_shows_profile_names(self, runner: CliRunner, vault_file: Path) -> None:
        profiles = [Profile(name="prod", keys=["A", "B"]), Profile(name="dev", keys=[])]
        with patch("envault.cli_profiler.list_profiles", return_value=profiles):
            result = runner.invoke(profile_group, ["list", f"--vault={vault_file}"])
        assert "prod" in result.output
        assert "dev" in result.output
