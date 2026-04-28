"""Tests for envault.auditor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.auditor import AuditError, record_event, read_log, AUDIT_FILE


@pytest.fixture()
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "vault.enc")


class TestRecordEvent:
    def test_creates_audit_file(self, vault_path: str, tmp_path: Path) -> None:
        record_event(vault_path, "set", keys=["DB_URL"])
        assert (tmp_path / AUDIT_FILE).exists()

    def test_entry_has_required_fields(self, vault_path: str) -> None:
        entry = record_event(vault_path, "export", keys=["API_KEY"], target="prod")
        assert entry["action"] == "export"
        assert entry["keys"] == ["API_KEY"]
        assert entry["target"] == "prod"
        assert "timestamp" in entry
        assert "actor" in entry

    def test_multiple_events_appended(self, vault_path: str, tmp_path: Path) -> None:
        record_event(vault_path, "set", keys=["A"])
        record_event(vault_path, "set", keys=["B"])
        record_event(vault_path, "rotate")

        raw = json.loads((tmp_path / AUDIT_FILE).read_text())
        assert len(raw) == 3

    def test_keys_defaults_to_empty_list(self, vault_path: str) -> None:
        entry = record_event(vault_path, "rotate")
        assert entry["keys"] == []

    def test_custom_actor(self, vault_path: str) -> None:
        entry = record_event(vault_path, "import", actor="ci-bot")
        assert entry["actor"] == "ci-bot"

    def test_raises_audit_error_on_bad_path(self) -> None:
        with pytest.raises(AuditError):
            record_event("/nonexistent/deep/path/vault.enc", "set")


class TestReadLog:
    def test_returns_empty_list_when_no_log(self, vault_path: str) -> None:
        assert read_log(vault_path) == []

    def test_returns_recorded_entries(self, vault_path: str) -> None:
        record_event(vault_path, "set", keys=["X"])
        record_event(vault_path, "export", target="staging")

        entries = read_log(vault_path)
        assert len(entries) == 2
        assert entries[0]["action"] == "set"
        assert entries[1]["action"] == "export"

    def test_raises_audit_error_on_corrupt_file(self, vault_path: str, tmp_path: Path) -> None:
        (tmp_path / AUDIT_FILE).write_text("not valid json")
        with pytest.raises(AuditError):
            read_log(vault_path)
