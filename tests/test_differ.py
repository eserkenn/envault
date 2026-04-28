"""Tests for envault.differ module."""

from __future__ import annotations

import pytest

from unittest.mock import MagicMock, patch

from envault.differ import DiffEntry, DiffError, _compute_diff, diff_vaults


# ---------------------------------------------------------------------------
# _compute_diff unit tests
# ---------------------------------------------------------------------------

class TestComputeDiff:
    def test_added_key(self):
        entries = _compute_diff({}, {"NEW_KEY": "value"})
        assert len(entries) == 1
        assert entries[0].status == "added"
        assert entries[0].key == "NEW_KEY"
        assert entries[0].right_value == "value"

    def test_removed_key(self):
        entries = _compute_diff({"OLD_KEY": "value"}, {})
        assert len(entries) == 1
        assert entries[0].status == "removed"
        assert entries[0].left_value == "value"

    def test_changed_key(self):
        entries = _compute_diff({"KEY": "old"}, {"KEY": "new"})
        assert len(entries) == 1
        assert entries[0].status == "changed"
        assert entries[0].left_value == "old"
        assert entries[0].right_value == "new"

    def test_unchanged_key(self):
        entries = _compute_diff({"KEY": "same"}, {"KEY": "same"})
        assert len(entries) == 1
        assert entries[0].status == "unchanged"

    def test_sorted_output(self):
        left = {"ZEBRA": "1", "APPLE": "2"}
        right = {"ZEBRA": "1", "APPLE": "2"}
        entries = _compute_diff(left, right)
        assert [e.key for e in entries] == ["APPLE", "ZEBRA"]

    def test_mixed_statuses(self):
        left = {"A": "1", "B": "old"}
        right = {"B": "new", "C": "3"}
        statuses = {e.key: e.status for e in _compute_diff(left, right)}
        assert statuses["A"] == "removed"
        assert statuses["B"] == "changed"
        assert statuses["C"] == "added"


# ---------------------------------------------------------------------------
# diff_vaults integration-style tests (vault mocked)
# ---------------------------------------------------------------------------

class TestDiffVaults:
    def _make_vault(self, secrets: dict):
        vault = MagicMock()
        vault.list_keys.return_value = list(secrets.keys())
        vault.get.side_effect = lambda key, pwd: secrets[key]
        return vault

    def test_returns_diff_entries(self):
        left = self._make_vault({"KEY": "a"})
        right = self._make_vault({"KEY": "b"})
        entries = diff_vaults(left, "pass", right, "pass")
        assert len(entries) == 1
        assert entries[0].status == "changed"

    def test_empty_vaults(self):
        left = self._make_vault({})
        right = self._make_vault({})
        entries = diff_vaults(left, "pass", right, "pass")
        assert entries == []

    def test_raises_diff_error_on_vault_error(self):
        from envault.vault import VaultError
        left = MagicMock()
        left.list_keys.side_effect = VaultError("bad password")
        right = self._make_vault({})
        with pytest.raises(DiffError, match="left vault"):
            diff_vaults(left, "wrong", right, "pass")
