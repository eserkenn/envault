"""Tests for envault.exporter."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envault.exporter import export_secrets, ExportError, _render
from envault.vault import VaultError


SECRETS = {
    "prod:DB_HOST": "db.prod.example.com",
    "prod:DB_PASS": "s3cr3t",
    "staging:DB_HOST": "db.staging.example.com",
    "GLOBAL_KEY": "global_value",
}


@pytest.fixture()
def vault_mock():
    mock = MagicMock()
    mock.get_all.return_value = SECRETS
    return mock


class TestRender:
    def test_dotenv_format(self):
        result = _render({"FOO": "bar", "BAZ": "qux"}, "dotenv")
        assert "FOO=bar" in result
        assert "BAZ=qux" in result
        assert result.endswith("\n")

    def test_json_format(self):
        result = _render({"FOO": "bar"}, "json")
        data = json.loads(result)
        assert data == {"FOO": "bar"}

    def test_shell_format(self):
        result = _render({"FOO": "bar"}, "shell")
        assert "export FOO=bar" in result

    def test_empty_secrets_dotenv(self):
        assert _render({}, "dotenv") == ""

    def test_unknown_format_raises(self):
        with pytest.raises(ExportError):
            _render({"K": "v"}, "xml")


class TestExportSecrets:
    def test_exports_all_secrets(self, vault_mock):
        result = export_secrets(vault_mock, "password", fmt="dotenv")
        assert "GLOBAL_KEY=global_value" in result

    def test_filters_by_target(self, vault_mock):
        result = export_secrets(vault_mock, "password", target="prod", fmt="dotenv")
        assert "DB_HOST=db.prod.example.com" in result
        assert "staging" not in result
        assert "GLOBAL_KEY" not in result

    def test_unsupported_format_raises(self, vault_mock):
        with pytest.raises(ExportError, match="Unsupported format"):
            export_secrets(vault_mock, "password", fmt="yaml")

    def test_vault_error_raises_export_error(self, vault_mock):
        vault_mock.get_all.side_effect = VaultError("bad password")
        with pytest.raises(ExportError, match="Failed to read vault"):
            export_secrets(vault_mock, "wrong")

    def test_writes_output_file(self, vault_mock, tmp_path):
        out = tmp_path / ".env"
        export_secrets(vault_mock, "password", fmt="dotenv", output_path=out)
        assert out.exists()
        assert "GLOBAL_KEY=global_value" in out.read_text()

    def test_json_export(self, vault_mock):
        result = export_secrets(vault_mock, "password", fmt="json")
        data = json.loads(result)
        assert "GLOBAL_KEY" in data
