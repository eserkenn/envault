"""Tests for envault.patcher."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.patcher import PatchError, PatchResult, patch_vault
from envault.vault import Vault


PASSWORD = "hunter2"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.vault"
    v = Vault(path, PASSWORD)
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("API_KEY", "old-key")
    return path


class TestPatchVault:
    def test_updates_existing_keys(self, vault_file: Path) -> None:
        result = patch_vault(vault_file, PASSWORD, {"API_KEY": "new-key"})
        assert "API_KEY" in result.updated

    def test_value_is_persisted(self, vault_file: Path) -> None:
        patch_vault(vault_file, PASSWORD, {"DB_HOST": "prod.db.example.com"})
        v = Vault(vault_file, PASSWORD)
        assert v.get("DB_HOST") == "prod.db.example.com"

    def test_multiple_keys_updated(self, vault_file: Path) -> None:
        updates = {"DB_HOST": "newhost", "DB_PORT": "5433"}
        result = patch_vault(vault_file, PASSWORD, updates)
        assert set(result.updated) == {"DB_HOST", "DB_PORT"}
        assert result.skipped == []
        assert not result.has_errors

    def test_raises_on_missing_key_by_default(self, vault_file: Path) -> None:
        with pytest.raises(PatchError, match="does not exist"):
            patch_vault(vault_file, PASSWORD, {"NONEXISTENT": "value"})

    def test_skip_missing_records_skipped(self, vault_file: Path) -> None:
        result = patch_vault(
            vault_file, PASSWORD, {"GHOST": "value"}, skip_missing=True
        )
        assert "GHOST" in result.skipped
        assert result.updated == []

    def test_skip_missing_still_updates_present_keys(self, vault_file: Path) -> None:
        updates = {"DB_HOST": "newhost", "MISSING": "val"}
        result = patch_vault(vault_file, PASSWORD, updates, skip_missing=True)
        assert "DB_HOST" in result.updated
        assert "MISSING" in result.skipped

    def test_raises_on_empty_updates(self, vault_file: Path) -> None:
        with pytest.raises(PatchError, match="No updates provided"):
            patch_vault(vault_file, PASSWORD, {})

    def test_raises_on_wrong_password(self, vault_file: Path) -> None:
        with pytest.raises(PatchError, match="Cannot open vault"):
            patch_vault(vault_file, "wrong-password", {"DB_HOST": "x"})

    def test_patch_result_has_errors_false_on_success(self, vault_file: Path) -> None:
        result = patch_vault(vault_file, PASSWORD, {"API_KEY": "v2"})
        assert not result.has_errors
