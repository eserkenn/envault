"""Tests for envault.cli_tagger."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_tagger import tag_group
from envault.tagger import TagResult, TaggerError


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def mock_vault(tmp_path):
    with patch("envault.cli_tagger.Vault") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        yield instance


class TestRunAdd:
    def test_outputs_tags(self, runner, mock_vault):
        with patch("envault.cli_tagger.add_tags") as mock_add:
            mock_add.return_value = TagResult(key="DB_URL", tags=["prod"])
            result = runner.invoke(tag_group, ["add", "vault.db", "pass", "DB_URL", "prod"])
        assert result.exit_code == 0
        assert "prod" in result.output

    def test_error_on_missing_key(self, runner, mock_vault):
        with patch("envault.cli_tagger.add_tags", side_effect=TaggerError("Key 'X' does not exist in vault.")):
            result = runner.invoke(tag_group, ["add", "vault.db", "pass", "X", "tag"])
        assert result.exit_code != 0
        assert "does not exist" in result.output


class TestRunRemove:
    def test_outputs_remaining_tags(self, runner, mock_vault):
        with patch("envault.cli_tagger.remove_tags") as mock_rm:
            mock_rm.return_value = TagResult(key="API_KEY", tags=["internal"])
            result = runner.invoke(tag_group, ["remove", "vault.db", "pass", "API_KEY", "prod"])
        assert result.exit_code == 0
        assert "internal" in result.output

    def test_no_tags_shows_none(self, runner, mock_vault):
        with patch("envault.cli_tagger.remove_tags") as mock_rm:
            mock_rm.return_value = TagResult(key="API_KEY", tags=[])
            result = runner.invoke(tag_group, ["remove", "vault.db", "pass", "API_KEY", "prod"])
        assert "(none)" in result.output


class TestRunList:
    def test_prints_tags(self, runner, mock_vault):
        with patch("envault.cli_tagger.get_tags") as mock_get:
            mock_get.return_value = TagResult(key="DB_URL", tags=["prod", "db"])
            result = runner.invoke(tag_group, ["list", "vault.db", "pass", "DB_URL"])
        assert "prod" in result.output
        assert "db" in result.output

    def test_no_tags_message(self, runner, mock_vault):
        with patch("envault.cli_tagger.get_tags") as mock_get:
            mock_get.return_value = TagResult(key="DB_URL", tags=[])
            result = runner.invoke(tag_group, ["list", "vault.db", "pass", "DB_URL"])
        assert "No tags" in result.output


class TestRunFind:
    def test_prints_matching_keys(self, runner, mock_vault):
        with patch("envault.cli_tagger.list_by_tag") as mock_find:
            mock_find.return_value = ["DB_URL", "REDIS_URL"]
            result = runner.invoke(tag_group, ["find", "vault.db", "pass", "prod"])
        assert "DB_URL" in result.output
        assert "REDIS_URL" in result.output

    def test_no_match_message(self, runner, mock_vault):
        with patch("envault.cli_tagger.list_by_tag") as mock_find:
            mock_find.return_value = []
            result = runner.invoke(tag_group, ["find", "vault.db", "pass", "ghost"])
        assert "No keys found" in result.output
