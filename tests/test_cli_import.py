"""Tests for envault.cli_import."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_import import run_import


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def mock_vault(tmp_path):
    with patch("envault.cli_import.Vault") as cls:
        instance = MagicMock()
        cls.return_value = instance
        yield instance


@pytest.fixture()
def mock_import():
    with patch("envault.cli_import.import_secrets") as m:
        yield m


class TestRunImport:
    def test_outputs_imported_keys(self, runner, tmp_path, mock_vault, mock_import):
        mock_import.return_value = {"FOO": "bar", "BAZ": "qux"}
        src = tmp_path / ".env"
        src.write_text("FOO=bar")
        result = runner.invoke(
            run_import,
            [str(src), "--vault-file", str(tmp_path / ".envault"), "--password", "secret"],
        )
        assert result.exit_code == 0
        assert "2 key(s)" in result.output

    def test_reports_no_new_keys(self, runner, tmp_path, mock_vault, mock_import):
        mock_import.return_value = {}
        src = tmp_path / ".env"
        src.write_text("FOO=bar")
        result = runner.invoke(
            run_import,
            [str(src), "--vault-file", str(tmp_path / ".envault"), "--password", "secret"],
        )
        assert result.exit_code == 0
        assert "No new keys" in result.output

    def test_error_shown_on_import_failure(self, runner, tmp_path, mock_vault, mock_import):
        from envault.importer import ImportError as EnvImportError
        mock_import.side_effect = EnvImportError("bad file")
        src = tmp_path / ".env"
        src.write_text("FOO=bar")
        result = runner.invoke(
            run_import,
            [str(src), "--vault-file", str(tmp_path / ".envault"), "--password", "secret"],
        )
        assert result.exit_code != 0
        assert "bad file" in result.output

    def test_passes_overwrite_flag(self, runner, tmp_path, mock_vault, mock_import):
        mock_import.return_value = {"KEY": "val"}
        src = tmp_path / ".env"
        src.write_text("KEY=val")
        runner.invoke(
            run_import,
            [str(src), "--vault-file", str(tmp_path / ".envault"), "--password", "s", "--overwrite"],
        )
        _, kwargs = mock_import.call_args
        assert kwargs.get("overwrite") is True
