"""Tests for envault.rotator."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from envault.rotator import RotationError, rotate_key
from envault.vault import Vault


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "test.vault")
    v = Vault(path, "old-pass")
    v.set("DB_URL", "postgres://localhost/db")
    v.set("API_KEY", "secret-key-123")
    return path


class TestRotateKey:
    def test_returns_rotated_key_names(self, vault_file):
        rotated = rotate_key(vault_file, "old-pass", "new-pass")
        assert set(rotated) == {"DB_URL", "API_KEY"}

    def test_secrets_readable_with_new_password(self, vault_file):
        rotate_key(vault_file, "old-pass", "new-pass")
        new_vault = Vault(vault_file, "new-pass")
        assert new_vault.get("DB_URL") == "postgres://localhost/db"
        assert new_vault.get("API_KEY") == "secret-key-123"

    def test_old_password_no_longer_works(self, vault_file):
        rotate_key(vault_file, "old-pass", "new-pass")
        old_vault = Vault(vault_file, "old-pass")
        with pytest.raises(Exception):
            old_vault.get("DB_URL")

    def test_empty_vault_returns_empty_list(self, tmp_path):
        path = str(tmp_path / "empty.vault")
        Vault(path, "old-pass")  # creates empty vault
        result = rotate_key(path, "old-pass", "new-pass")
        assert result == []

    def test_wrong_old_password_raises_rotation_error(self, vault_file):
        with pytest.raises(RotationError):
            rotate_key(vault_file, "wrong-pass", "new-pass")
