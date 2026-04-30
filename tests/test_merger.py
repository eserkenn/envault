"""Tests for envault.merger."""

from __future__ import annotations

import pytest

from envault.merger import ConflictStrategy, MergeError, merge_vaults
from envault.vault import Vault


@pytest.fixture()
def source_vault(tmp_path):
    path = str(tmp_path / "source.vault")
    v = Vault(path, "src-pass")
    v.set("API_KEY", "abc123")
    v.set("DB_URL", "postgres://source")
    return path


@pytest.fixture()
def target_vault(tmp_path):
    path = str(tmp_path / "target.vault")
    v = Vault(path, "tgt-pass")
    v.set("DB_URL", "postgres://target")
    v.set("SECRET", "existing")
    return path


class TestMergeAdded:
    def test_new_keys_are_added(self, source_vault, target_vault):
        result = merge_vaults(source_vault, "src-pass", target_vault, "tgt-pass")
        assert "API_KEY" in result.added

    def test_added_key_readable_in_target(self, source_vault, target_vault, tmp_path):
        merge_vaults(source_vault, "src-pass", target_vault, "tgt-pass")
        v = Vault(target_vault, "tgt-pass")
        assert v.get("API_KEY") == "abc123"

    def test_existing_target_keys_preserved(self, source_vault, target_vault):
        merge_vaults(source_vault, "src-pass", target_vault, "tgt-pass")
        v = Vault(target_vault, "tgt-pass")
        assert v.get("SECRET") == "existing"


class TestConflictStrategySource:
    def test_source_strategy_overwrites(self, source_vault, target_vault):
        result = merge_vaults(
            source_vault, "src-pass", target_vault, "tgt-pass",
            strategy=ConflictStrategy.KEEP_SOURCE,
        )
        assert "DB_URL" in result.overwritten

    def test_overwritten_value_is_from_source(self, source_vault, target_vault):
        merge_vaults(
            source_vault, "src-pass", target_vault, "tgt-pass",
            strategy=ConflictStrategy.KEEP_SOURCE,
        )
        v = Vault(target_vault, "tgt-pass")
        assert v.get("DB_URL") == "postgres://source"


class TestConflictStrategyTarget:
    def test_target_strategy_skips_conflicts(self, source_vault, target_vault):
        result = merge_vaults(
            source_vault, "src-pass", target_vault, "tgt-pass",
            strategy=ConflictStrategy.KEEP_TARGET,
        )
        assert "DB_URL" in result.skipped

    def test_target_value_unchanged(self, source_vault, target_vault):
        merge_vaults(
            source_vault, "src-pass", target_vault, "tgt-pass",
            strategy=ConflictStrategy.KEEP_TARGET,
        )
        v = Vault(target_vault, "tgt-pass")
        assert v.get("DB_URL") == "postgres://target"


class TestConflictStrategyRaise:
    def test_raises_on_conflict(self, source_vault, target_vault):
        with pytest.raises(MergeError, match="Conflicts detected"):
            merge_vaults(
                source_vault, "src-pass", target_vault, "tgt-pass",
                strategy=ConflictStrategy.RAISE,
            )


class TestKeyFilter:
    def test_only_specified_keys_merged(self, source_vault, target_vault):
        result = merge_vaults(
            source_vault, "src-pass", target_vault, "tgt-pass",
            keys=["API_KEY"],
        )
        assert result.added == ["API_KEY"]
        assert result.overwritten == []

    def test_unknown_key_raises(self, source_vault, target_vault):
        with pytest.raises(MergeError, match="Keys not found"):
            merge_vaults(
                source_vault, "src-pass", target_vault, "tgt-pass",
                keys=["NONEXISTENT"],
            )
