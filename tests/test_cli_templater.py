"""Tests for envault.cli_templater."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_templater import template_group
from envault.templater import RenderResult, TemplateError


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / "vault.enc"
    p.write_bytes(b"dummy")
    return p


@pytest.fixture()
def template_file(tmp_path):
    p = tmp_path / "app.tpl"
    p.write_text("host={{ DB_HOST }}")
    return p


@pytest.fixture()
def mock_render():
    with patch("envault.cli_templater.render_file") as m:
        m.return_value = RenderResult(output="host=localhost", resolved=["DB_HOST"], missing=[])
        yield m


@pytest.fixture()
def mock_vault():
    with patch("envault.cli_templater.Vault") as m:
        yield m


class TestRunRender:
    def test_outputs_resolved_secrets(self, runner, tmp_path, template_file, vault_file, mock_render, mock_vault):
        out = tmp_path / "app.conf"
        result = runner.invoke(
            template_group,
            ["render", str(template_file), str(out), "--vault", str(vault_file), "--password", "secret"],
        )
        assert result.exit_code == 0
        assert "DB_HOST" in result.output

    def test_outputs_written_path(self, runner, tmp_path, template_file, vault_file, mock_render, mock_vault):
        out = tmp_path / "app.conf"
        result = runner.invoke(
            template_group,
            ["render", str(template_file), str(out), "--vault", str(vault_file), "--password", "pw"],
        )
        assert str(out) in result.output

    def test_shows_warning_for_missing(self, runner, tmp_path, template_file, vault_file, mock_vault):
        with patch("envault.cli_templater.render_file") as m:
            m.return_value = RenderResult(output="{{ GHOST }}", resolved=[], missing=["GHOST"])
            out = tmp_path / "app.conf"
            result = runner.invoke(
                template_group,
                ["render", str(template_file), str(out), "--vault", str(vault_file), "--password", "pw"],
            )
        assert "GHOST" in result.output
        assert "Warning" in result.output

    def test_template_error_shows_click_error(self, runner, tmp_path, template_file, vault_file, mock_vault):
        with patch("envault.cli_templater.render_file", side_effect=TemplateError("boom")):
            out = tmp_path / "app.conf"
            result = runner.invoke(
                template_group,
                ["render", str(template_file), str(out), "--vault", str(vault_file), "--password", "pw"],
            )
        assert result.exit_code != 0
        assert "boom" in result.output
