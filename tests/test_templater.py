"""Tests for envault.templater."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from envault.templater import RenderResult, TemplateError, render_file, render_template


@pytest.fixture()
def vault_mock():
    vault = MagicMock()
    vault.get.side_effect = lambda key, _pw: {"DB_HOST": "localhost", "DB_PORT": "5432"}.get(
        key, (_ for _ in ()).throw(KeyError(key))
    )
    return vault


class TestRenderTemplate:
    def test_replaces_known_placeholder(self, vault_mock):
        result = render_template("host={{ DB_HOST }}", vault_mock, "pw")
        assert result.output == "host=localhost"

    def test_resolved_list_populated(self, vault_mock):
        result = render_template("{{ DB_HOST }}:{{ DB_PORT }}", vault_mock, "pw")
        assert sorted(result.resolved) == ["DB_HOST", "DB_PORT"]

    def test_missing_placeholder_kept_verbatim(self, vault_mock):
        result = render_template("{{ UNKNOWN }}", vault_mock, "pw")
        assert result.output == "{{ UNKNOWN }}"

    def test_missing_list_populated(self, vault_mock):
        result = render_template("{{ UNKNOWN }}", vault_mock, "pw")
        assert result.missing == ["UNKNOWN"]

    def test_has_missing_property(self, vault_mock):
        result = render_template("{{ MISSING }}", vault_mock, "pw")
        assert result.has_missing is True

    def test_no_placeholders_unchanged(self, vault_mock):
        result = render_template("plain text", vault_mock, "pw")
        assert result.output == "plain text"
        assert result.resolved == []
        assert result.missing == []

    def test_mixed_known_and_unknown(self, vault_mock):
        result = render_template("{{ DB_HOST }} {{ GHOST }}", vault_mock, "pw")
        assert "localhost" in result.output
        assert "{{ GHOST }}" in result.output


class TestRenderFile:
    def test_writes_output_file(self, tmp_path, vault_mock):
        tpl = tmp_path / "app.conf.tpl"
        tpl.write_text("host={{ DB_HOST }}")
        out = tmp_path / "app.conf"
        render_file(tpl, out, vault_mock, "pw")
        assert out.read_text() == "host=localhost"

    def test_raises_when_template_missing(self, tmp_path, vault_mock):
        with pytest.raises(TemplateError, match="Template file not found"):
            render_file(tmp_path / "no.tpl", tmp_path / "out", vault_mock, "pw")

    def test_raises_when_output_exists_no_overwrite(self, tmp_path, vault_mock):
        tpl = tmp_path / "t.tpl"
        tpl.write_text("x")
        out = tmp_path / "out.txt"
        out.write_text("existing")
        with pytest.raises(TemplateError, match="already exists"):
            render_file(tpl, out, vault_mock, "pw")

    def test_overwrite_flag_replaces_file(self, tmp_path, vault_mock):
        tpl = tmp_path / "t.tpl"
        tpl.write_text("{{ DB_HOST }}")
        out = tmp_path / "out.txt"
        out.write_text("old")
        render_file(tpl, out, vault_mock, "pw", overwrite=True)
        assert out.read_text() == "localhost"

    def test_returns_render_result(self, tmp_path, vault_mock):
        tpl = tmp_path / "t.tpl"
        tpl.write_text("{{ DB_HOST }}")
        result = render_file(tpl, tmp_path / "out", vault_mock, "pw")
        assert isinstance(result, RenderResult)
