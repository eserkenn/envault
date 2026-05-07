"""Tests for envault.cloner."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.cloner import CloneError, CloneResult, clone_vault
from envault.vault import Vault


@pytest.fixture()
def vault_pair(tmp_path: Path):
    """Return (source_path, dest_path) with a pre-populated source vault."""
    src = tmp_path / "source.vault"
    dst = tmp_path / "dest.vault"

    source = Vault(src, "src-pass")
    source.set("DB_HOST", "localhost")
    source.set("DB_PORT", "5432")
    source.set("API_KEY", "secret-key")

    # Initialise empty destination
    Vault(dst, "dst-pass")

    return src, dst


class TestCloneVault:
    def test_clones_all_keys_by_default(self, vault_pair):
        src, dst = vault_pair
        result = clone_vault(src, "src-pass", dst, "dst-pass")
        assert set(result.cloned) == {"DB_HOST", "DB_PORT", "API_KEY"}

    def test_values_are_readable_in_destination(self, vault_pair):
        src, dst = vault_pair
        clone_vault(src, "src-pass", dst, "dst-pass")
        dest_vault = Vault(dst, "dst-pass")
        assert dest_vault.get("DB_HOST") == "localhost"
        assert dest_vault.get("API_KEY") == "secret-key"

    def test_clones_only_specified_keys(self, vault_pair):
        src, dst = vault_pair
        result = clone_vault(src, "src-pass", dst, "dst-pass", keys=["DB_HOST"])
        assert result.cloned == ["DB_HOST"]
        assert result.skipped == []

    def test_skips_existing_keys_without_overwrite(self, vault_pair):
        src, dst = vault_pair
        # Pre-populate destination with one key
        dest = Vault(dst, "dst-pass")
        dest.set("DB_HOST", "other-host")

        result = clone_vault(src, "src-pass", dst, "dst-pass", keys=["DB_HOST"])
        assert "DB_HOST" in result.skipped
        assert "DB_HOST" not in result.cloned

    def test_overwrites_when_flag_set(self, vault_pair):
        src, dst = vault_pair
        dest = Vault(dst, "dst-pass")
        dest.set("DB_HOST", "old-value")

        clone_vault(src, "src-pass", dst, "dst-pass", keys=["DB_HOST"], overwrite=True)

        dest_vault = Vault(dst, "dst-pass")
        assert dest_vault.get("DB_HOST") == "localhost"

    def test_missing_key_goes_to_errors(self, vault_pair):
        src, dst = vault_pair
        result = clone_vault(src, "src-pass", dst, "dst-pass", keys=["NONEXISTENT"])
        assert "NONEXISTENT" in result.errors
        assert result.total_cloned == 0

    def test_raises_on_bad_source_password(self, vault_pair):
        src, dst = vault_pair
        with pytest.raises(CloneError, match="source"):
            clone_vault(src, "wrong-pass", dst, "dst-pass")

    def test_clone_result_total_cloned(self):
        r = CloneResult(cloned=["A", "B"], skipped=["C"])
        assert r.total_cloned == 2
