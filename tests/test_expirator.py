"""Tests for envault.expirator."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from envault.expirator import (
    ExpirationError,
    ExpirationEntry,
    check_expirations,
    list_expirations,
    remove_expiration,
    set_expiration,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.vault"
    path.write_text("{}")
    return path


class TestSetExpiration:
    def test_creates_expiry_file(self, vault_file: Path) -> None:
        set_expiration(vault_file, "API_KEY", date(2030, 1, 1))
        expiry = vault_file.with_suffix(".expiry.json")
        assert expiry.exists()

    def test_expiry_contains_key(self, vault_file: Path) -> None:
        set_expiration(vault_file, "API_KEY", date(2030, 6, 15))
        data = json.loads(vault_file.with_suffix(".expiry.json").read_text())
        assert data["API_KEY"] == "2030-06-15"

    def test_overwrite_existing_expiry(self, vault_file: Path) -> None:
        set_expiration(vault_file, "API_KEY", date(2030, 1, 1))
        set_expiration(vault_file, "API_KEY", date(2031, 3, 20))
        data = json.loads(vault_file.with_suffix(".expiry.json").read_text())
        assert data["API_KEY"] == "2031-03-20"

    def test_raises_when_vault_missing(self, tmp_path: Path) -> None:
        with pytest.raises(ExpirationError):
            set_expiration(tmp_path / "missing.vault", "KEY", date(2030, 1, 1))


class TestRemoveExpiration:
    def test_returns_true_when_removed(self, vault_file: Path) -> None:
        set_expiration(vault_file, "API_KEY", date(2030, 1, 1))
        assert remove_expiration(vault_file, "API_KEY") is True

    def test_returns_false_when_not_set(self, vault_file: Path) -> None:
        assert remove_expiration(vault_file, "MISSING") is False

    def test_key_absent_after_removal(self, vault_file: Path) -> None:
        set_expiration(vault_file, "API_KEY", date(2030, 1, 1))
        remove_expiration(vault_file, "API_KEY")
        data = json.loads(vault_file.with_suffix(".expiry.json").read_text())
        assert "API_KEY" not in data


class TestCheckExpirations:
    def test_expired_key_included(self, vault_file: Path) -> None:
        yesterday = date.today() - timedelta(days=1)
        set_expiration(vault_file, "OLD_KEY", yesterday)
        entries = check_expirations(vault_file, warn_within_days=7)
        assert any(e.key == "OLD_KEY" and e.is_expired for e in entries)

    def test_future_key_excluded(self, vault_file: Path) -> None:
        far_future = date.today() + timedelta(days=30)
        set_expiration(vault_file, "FUTURE_KEY", far_future)
        entries = check_expirations(vault_file, warn_within_days=7)
        assert not any(e.key == "FUTURE_KEY" for e in entries)

    def test_soon_expiring_key_included(self, vault_file: Path) -> None:
        soon = date.today() + timedelta(days=3)
        set_expiration(vault_file, "SOON_KEY", soon)
        entries = check_expirations(vault_file, warn_within_days=7)
        assert any(e.key == "SOON_KEY" for e in entries)

    def test_results_sorted_by_date(self, vault_file: Path) -> None:
        today = date.today()
        set_expiration(vault_file, "B", today + timedelta(days=5))
        set_expiration(vault_file, "A", today + timedelta(days=2))
        entries = check_expirations(vault_file, warn_within_days=10)
        keys = [e.key for e in entries]
        assert keys == sorted(keys, key=lambda k: next(e.expires_on for e in entries if e.key == k))


class TestListExpirations:
    def test_returns_all_entries(self, vault_file: Path) -> None:
        set_expiration(vault_file, "K1", date(2035, 1, 1))
        set_expiration(vault_file, "K2", date(2036, 6, 1))
        entries = list_expirations(vault_file)
        assert len(entries) == 2

    def test_empty_when_no_expirations(self, vault_file: Path) -> None:
        assert list_expirations(vault_file) == []
