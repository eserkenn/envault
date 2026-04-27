"""Tests for envault.importer."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from envault.importer import ImportError as EnvImportError
from envault.importer import _parse_dotenv, _parse_json, import_secrets


@pytest.fixture()
def vault_mock():
    mock = MagicMock()
    mock.has.return_value = False
    return mock


# ---------------------------------------------------------------------------
# _parse_dotenv
# ---------------------------------------------------------------------------

class TestParseDotenv:
    def test_basic_key_value(self):
        result = _parse_dotenv("FOO=bar")
        assert result == {"FOO": "bar"}

    def test_ignores_comments(self):
        result = _parse_dotenv("# comment\nKEY=value")
        assert "KEY" in result
        assert len(result) == 1

    def test_ignores_blank_lines(self):
        result = _parse_dotenv("\n\nKEY=value\n")
        assert result == {"KEY": "value"}

    def test_strips_quotes(self):
        result = _parse_dotenv('KEY="hello world"')
        assert result["KEY"] == "hello world"

    def test_strips_single_quotes(self):
        result = _parse_dotenv("KEY='hello'")
        assert result["KEY"] == "hello"

    def test_value_with_equals(self):
        result = _parse_dotenv("KEY=a=b=c")
        assert result["KEY"] == "a=b=c"


# ---------------------------------------------------------------------------
# _parse_json
# ---------------------------------------------------------------------------

class TestParseJson:
    def test_parses_flat_object(self):
        result = _parse_json(json.dumps({"A": "1", "B": "2"}))
        assert result == {"A": "1", "B": "2"}

    def test_coerces_values_to_str(self):
        result = _parse_json(json.dumps({"NUM": 42}))
        assert result["NUM"] == "42"

    def test_raises_on_invalid_json(self):
        with pytest.raises(EnvImportError, match="Invalid JSON"):
            _parse_json("not json")

    def test_raises_on_non_object(self):
        with pytest.raises(EnvImportError, match="object"):
            _parse_json(json.dumps(["a", "b"]))


# ---------------------------------------------------------------------------
# import_secrets
# ---------------------------------------------------------------------------

class TestImportSecrets:
    def test_imports_dotenv_file(self, tmp_path, vault_mock):
        src = tmp_path / ".env"
        src.write_text("FOO=bar\nBAZ=qux")
        imported = import_secrets(vault_mock, src, "dotenv")
        assert set(imported) == {"FOO", "BAZ"}

    def test_skips_existing_keys_by_default(self, tmp_path, vault_mock):
        vault_mock.has.return_value = True
        src = tmp_path / ".env"
        src.write_text("FOO=bar")
        imported = import_secrets(vault_mock, src, "dotenv", overwrite=False)
        assert imported == {}

    def test_overwrites_when_flag_set(self, tmp_path, vault_mock):
        vault_mock.has.return_value = True
        src = tmp_path / ".env"
        src.write_text("FOO=bar")
        imported = import_secrets(vault_mock, src, "dotenv", overwrite=True)
        assert "FOO" in imported

    def test_raises_when_file_missing(self, tmp_path, vault_mock):
        with pytest.raises(EnvImportError, match="not found"):
            import_secrets(vault_mock, tmp_path / "missing.env", "dotenv")

    def test_raises_on_unsupported_format(self, tmp_path, vault_mock):
        src = tmp_path / "data.txt"
        src.write_text("KEY=val")
        with pytest.raises(EnvImportError, match="Unsupported"):
            import_secrets(vault_mock, src, "yaml")
