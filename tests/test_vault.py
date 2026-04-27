"""Tests for the Vault class."""

import json
import pytest
from pathlib import Path

from envault.vault import Vault, VaultError

PASSWORD = "test-password-123"


@pytest.fixture
def vault(tmp_path):
    return Vault(path=str(tmp_path / ".envault"), target="test")


class TestVaultSet:
    def test_creates_vault_file(self, vault, tmp_path):
        vault.set("API_KEY", "secret", PASSWORD)
        assert Path(vault.path).exists()

    def test_stored_value_is_encrypted(self, vault, tmp_path):
        vault.set("API_KEY", "secret", PASSWORD)
        raw = json.loads(Path(vault.path).read_text())
        assert raw["test"]["API_KEY"]["token"] != "secret"

    def test_overwrite_existing_key(self, vault):
        vault.set("DB_URL", "old_value", PASSWORD)
        vault.set("DB_URL", "new_value", PASSWORD)
        assert vault.get("DB_URL", PASSWORD) == "new_value"


class TestVaultGet:
    def test_returns_correct_value(self, vault):
        vault.set("TOKEN", "my-secret-token", PASSWORD)
        assert vault.get("TOKEN", PASSWORD) == "my-secret-token"

    def test_raises_on_missing_key(self, vault):
        with pytest.raises(VaultError, match="not found"):
            vault.get("NONEXISTENT", PASSWORD)

    def test_raises_on_wrong_password(self, vault):
        vault.set("KEY", "value", PASSWORD)
        with pytest.raises(Exception):
            vault.get("KEY", "wrong-password")

    def test_multiple_keys_independent(self, vault):
        vault.set("KEY_A", "alpha", PASSWORD)
        vault.set("KEY_B", "beta", PASSWORD)
        assert vault.get("KEY_A", PASSWORD) == "alpha"
        assert vault.get("KEY_B", PASSWORD) == "beta"


class TestVaultDelete:
    def test_removes_key(self, vault):
        vault.set("TEMP", "value", PASSWORD)
        vault.delete("TEMP")
        assert "TEMP" not in vault.list_keys()

    def test_raises_on_missing_key(self, vault):
        with pytest.raises(VaultError, match="not found"):
            vault.delete("GHOST")


class TestVaultListKeys:
    def test_empty_vault_returns_empty_list(self, vault):
        assert vault.list_keys() == []

    def test_returns_all_stored_keys(self, vault):
        vault.set("A", "1", PASSWORD)
        vault.set("B", "2", PASSWORD)
        assert sorted(vault.list_keys()) == ["A", "B"]

    def test_keys_are_target_scoped(self, tmp_path):
        vault_a = Vault(path=str(tmp_path / ".envault"), target="staging")
        vault_b = Vault(path=str(tmp_path / ".envault"), target="production")
        vault_a.set("ONLY_STAGING", "val", PASSWORD)
        assert vault_b.list_keys() == []
