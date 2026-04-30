"""Tests for envault.renamer."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from envault.renamer import RenameError, RenameResult, bulk_rename, rename_key
from envault.vault import Vault

PASSWORD = "test-password"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "vault.json"
    v = Vault(str(path))
    v.set("ALPHA", "value_a", PASSWORD)
    v.set("BETA", "value_b", PASSWORD)
    return path


class TestRenameKey:
    def test_old_key_removed(self, vault_file: Path) -> None:
        v = Vault(str(vault_file))
        rename_key(v, PASSWORD, "ALPHA", "ALPHA_NEW")
        assert "ALPHA" not in v.list_keys()

    def test_new_key_present(self, vault_file: Path) -> None:
        v = Vault(str(vault_file))
        rename_key(v, PASSWORD, "ALPHA", "ALPHA_NEW")
        assert "ALPHA_NEW" in v.list_keys()

    def test_value_preserved(self, vault_file: Path) -> None:
        v = Vault(str(vault_file))
        rename_key(v, PASSWORD, "ALPHA", "ALPHA_NEW")
        assert v.get("ALPHA_NEW", PASSWORD) == "value_a"

    def test_returns_rename_result(self, vault_file: Path) -> None:
        v = Vault(str(vault_file))
        result = rename_key(v, PASSWORD, "BETA", "BETA_RENAMED")
        assert isinstance(result, RenameResult)
        assert result.success is True
        assert result.old_key == "BETA"
        assert result.new_key == "BETA_RENAMED"

    def test_raises_on_missing_key(self, vault_file: Path) -> None:
        v = Vault(str(vault_file))
        with pytest.raises(RenameError, match="does not exist"):
            rename_key(v, PASSWORD, "MISSING", "WHATEVER")

    def test_raises_on_existing_new_key_without_overwrite(self, vault_file: Path) -> None:
        v = Vault(str(vault_file))
        with pytest.raises(RenameError, match="already exists"):
            rename_key(v, PASSWORD, "ALPHA", "BETA")

    def test_overwrite_replaces_existing_key(self, vault_file: Path) -> None:
        v = Vault(str(vault_file))
        rename_key(v, PASSWORD, "ALPHA", "BETA", overwrite=True)
        assert v.get("BETA", PASSWORD) == "value_a"
        assert "ALPHA" not in v.list_keys()


class TestBulkRename:
    def test_all_succeed(self, vault_file: Path) -> None:
        v = Vault(str(vault_file))
        results = bulk_rename(v, PASSWORD, [("ALPHA", "A2"), ("BETA", "B2")])
        assert all(r.success for r in results)
        assert set(v.list_keys()) == {"A2", "B2"}

    def test_partial_failure_continues(self, vault_file: Path) -> None:
        v = Vault(str(vault_file))
        results = bulk_rename(v, PASSWORD, [("MISSING", "X"), ("BETA", "B2")])
        assert results[0].success is False
        assert results[1].success is True

    def test_failed_result_has_message(self, vault_file: Path) -> None:
        v = Vault(str(vault_file))
        results = bulk_rename(v, PASSWORD, [("NOPE", "X")])
        assert results[0].message != ""
