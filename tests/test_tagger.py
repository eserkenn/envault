"""Tests for envault.tagger."""
from __future__ import annotations

import pytest

from envault.tagger import (
    TaggerError,
    TagResult,
    add_tags,
    all_tags,
    get_tags,
    list_by_tag,
    remove_tags,
)


# ---------------------------------------------------------------------------
# Minimal fake vault
# ---------------------------------------------------------------------------

class _FakeVault:
    def __init__(self, keys=None):
        self._store: dict = {}
        for k, v in (keys or {}).items():
            self._store[k] = v

    def list_keys(self):
        return [k for k in self._store if not k.startswith("__tags__")]

    def get(self, key):
        if key not in self._store:
            raise KeyError(key)
        return self._store[key]

    def set(self, key, value):
        self._store[key] = value


@pytest.fixture()
def vault():
    return _FakeVault({"DB_URL": "postgres://localhost", "API_KEY": "secret"})


class TestAddTags:
    def test_returns_tag_result(self, vault):
        result = add_tags(vault, "DB_URL", ["production"])
        assert isinstance(result, TagResult)

    def test_tag_is_stored(self, vault):
        result = add_tags(vault, "DB_URL", ["production"])
        assert "production" in result.tags

    def test_multiple_tags(self, vault):
        result = add_tags(vault, "DB_URL", ["prod", "db"])
        assert set(result.tags) == {"prod", "db"}

    def test_duplicate_tags_deduplicated(self, vault):
        add_tags(vault, "DB_URL", ["prod"])
        result = add_tags(vault, "DB_URL", ["prod", "db"])
        assert result.tags.count("prod") == 1

    def test_raises_for_missing_key(self, vault):
        with pytest.raises(TaggerError, match="does not exist"):
            add_tags(vault, "MISSING", ["tag"])


class TestRemoveTags:
    def test_tag_is_removed(self, vault):
        add_tags(vault, "API_KEY", ["internal", "prod"])
        result = remove_tags(vault, "API_KEY", ["prod"])
        assert "prod" not in result.tags
        assert "internal" in result.tags

    def test_removing_nonexistent_tag_is_safe(self, vault):
        result = remove_tags(vault, "API_KEY", ["ghost"])
        assert result.tags == []

    def test_raises_for_missing_key(self, vault):
        with pytest.raises(TaggerError):
            remove_tags(vault, "NOPE", ["x"])


class TestListByTag:
    def test_returns_matching_keys(self, vault):
        add_tags(vault, "DB_URL", ["prod"])
        add_tags(vault, "API_KEY", ["prod"])
        assert set(list_by_tag(vault, "prod")) == {"DB_URL", "API_KEY"}

    def test_returns_empty_when_no_match(self, vault):
        assert list_by_tag(vault, "nonexistent") == []

    def test_only_matching_keys_returned(self, vault):
        add_tags(vault, "DB_URL", ["prod"])
        add_tags(vault, "API_KEY", ["staging"])
        assert list_by_tag(vault, "prod") == ["DB_URL"]


class TestGetTags:
    def test_returns_empty_list_when_no_tags(self, vault):
        result = get_tags(vault, "DB_URL")
        assert result.tags == []

    def test_returns_assigned_tags(self, vault):
        add_tags(vault, "DB_URL", ["x", "y"])
        result = get_tags(vault, "DB_URL")
        assert set(result.tags) == {"x", "y"}

    def test_raises_for_missing_key(self, vault):
        with pytest.raises(TaggerError):
            get_tags(vault, "MISSING")


class TestAllTags:
    def test_returns_dict_for_all_keys(self, vault):
        add_tags(vault, "DB_URL", ["prod"])
        result = all_tags(vault)
        assert "DB_URL" in result
        assert "API_KEY" in result

    def test_untagged_keys_have_empty_list(self, vault):
        result = all_tags(vault)
        assert result["API_KEY"] == []
