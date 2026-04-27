"""Tests for envault.cli_export."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from envault.cli_export import export_group
from envault.exporter import ExportError


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def mock_export():
    with patch("envault.cli_export.export_secrets") as mock:
        yield mock


@pytest.fixture()
 def mock_vault():
    with patch("envault.cli_export.Vault") as mock_cls:
        yield mock_cls


class TestRunExport:
    def test_outputs_to_stdout(self, runner, mock_export, mock_vault):
        mock_export.return_value = "FOO=bar\n"
        result = runner.invoke(
            export_group, ["run", "--password", "secret"]
        )
        assert result.exit_code == 0
        assert "FOO=bar" in result.output

    def test_passes_target_option(self, runner, mock_export, mock_vault):
        mock_export.return_value = "DB_HOST=localhost\n"
        runner.invoke(
            export_group,
            ["run", "--password", "secret", "--target", "prod"],
        )
        _, kwargs = mock_export.call_args
        assert kwargs.get("target") == "prod" or mock_export.call_args[0][2] == "prod"

    def test_passes_format_option(self, runner, mock_export, mock_vault):
        mock_export.return_value = "{\"FOO\": \"bar\"}\n"
        result = runner.invoke(
            export_group,
            ["run", "--password", "secret", "--format", "json"],
        )
        assert result.exit_code == 0

    def test_writes_to_file(self, runner, mock_export, mock_vault, tmp_path):
        out_file = tmp_path / ".env"
        mock_export.return_value = "FOO=bar\n"
        result = runner.invoke(
            export_group,
            ["run", "--password", "secret", "--output", str(out_file)],
        )
        assert result.exit_code == 0
        assert "exported" in result.output

    def test_export_error_exits_nonzero(self, runner, mock_export, mock_vault):
        mock_export.side_effect = ExportError("bad password")
        result = runner.invoke(
            export_group, ["run", "--password", "wrong"]
        )
        assert result.exit_code == 1
        assert "Error" in result.output
