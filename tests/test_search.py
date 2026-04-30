"""Tests for envault.search module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from envault.search import SearchError, SearchResult, search_vault


@pytest.fixture()
def vault_mock() -> MagicMock:
    mock = MagicMock()
    mock.list_keys.return_value = ["DB_HOST", "DB_PASSWORD", "API_KEY", "SECRET_TOKEN"]
    mock.get.side_effect = lambda key, pwd: {
        "DB_HOST": "localhost",
        "DB_PASSWORD": "s3cr3t",
        "API_KEY": "abc123",
        "SECRET_TOKEN": "tok_xyz",
    }.get(key)
    return mock


class TestSearchByKey:
    def test_glob_matches_keys(self, vault_mock: MagicMock) -> None:
        results = search_vault(vault_mock, "pass", "DB_*")
        keys = [r.key for r in results]
        assert "DB_HOST" in keys
        assert "DB_PASSWORD" in keys

    def test_no_match_returns_empty(self, vault_mock: MagicMock) -> None:
        results = search_vault(vault_mock, "pass", "NONEXISTENT_*")
        assert results == []

    def test_matched_by_is_key(self, vault_mock: MagicMock) -> None:
        results = search_vault(vault_mock, "pass", "API_KEY")
        assert len(results) == 1
        assert results[0].matched_by == "key"

    def test_regex_match(self, vault_mock: MagicMock) -> None:
        results = search_vault(vault_mock, "pass", r"^DB_", use_regex=True)
        keys = [r.key for r in results]
        assert "DB_HOST" in keys
        assert "DB_PASSWORD" in keys
        assert "API_KEY" not in keys

    def test_invalid_regex_raises(self, vault_mock: MagicMock) -> None:
        with pytest.raises(SearchError, match="Invalid regex"):
            search_vault(vault_mock, "pass", "[invalid", use_regex=True)


class TestSearchByValue:
    def test_value_match_sets_matched_by(self, vault_mock: MagicMock) -> None:
        # 'localhost' matches glob '*local*'
        results = search_vault(vault_mock, "pass", "*local*", search_values=True)
        assert any(r.key == "DB_HOST" and r.matched_by == "value" for r in results)

    def test_key_match_takes_priority_over_value(self, vault_mock: MagicMock) -> None:
        # DB_HOST matches key glob 'DB_*' — should not also appear as value match
        results = search_vault(vault_mock, "pass", "DB_*", search_values=True)
        db_host_results = [r for r in results if r.key == "DB_HOST"]
        assert len(db_host_results) == 1
        assert db_host_results[0].matched_by == "key"

    def test_vault_error_on_list_raises_search_error(self) -> None:
        mock = MagicMock()
        mock.list_keys.side_effect = Exception("disk error")
        with pytest.raises(SearchError):
            search_vault(mock, "pass", "*")

    def test_vault_error_on_get_raises_search_error(self, vault_mock: MagicMock) -> None:
        from envault.vault import VaultError
        vault_mock.get.side_effect = VaultError("bad decrypt")
        with pytest.raises(SearchError, match="Failed to decrypt"):
            search_vault(vault_mock, "wrong", "*local*", search_values=True)
