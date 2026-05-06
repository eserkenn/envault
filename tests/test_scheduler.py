"""Tests for envault.scheduler."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from envault.scheduler import (
    SchedulerError,
    ScheduleEntry,
    due_keys,
    load_schedule,
    remove_schedule,
    set_schedule,
)


@pytest.fixture()
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "vault.env"


class TestScheduleEntry:
    def test_next_rotation(self) -> None:
        entry = ScheduleEntry(key="DB_PASS", rotate_every_days=30,
                              last_rotated="2024-01-01T00:00:00")
        assert entry.next_rotation() == datetime(2024, 1, 31, 0, 0, 0)

    def test_is_due_when_past(self) -> None:
        past = (datetime.utcnow() - timedelta(days=91)).isoformat()
        entry = ScheduleEntry(key="KEY", rotate_every_days=90, last_rotated=past)
        assert entry.is_due() is True

    def test_not_due_when_future(self) -> None:
        recent = datetime.utcnow().isoformat()
        entry = ScheduleEntry(key="KEY", rotate_every_days=90, last_rotated=recent)
        assert entry.is_due() is False

    def test_days_until_due_zero_when_overdue(self) -> None:
        past = (datetime.utcnow() - timedelta(days=100)).isoformat()
        entry = ScheduleEntry(key="KEY", rotate_every_days=30, last_rotated=past)
        assert entry.days_until_due() == 0


class TestSetSchedule:
    def test_creates_schedule_file(self, vault_path: Path) -> None:
        set_schedule(vault_path, "API_KEY", 30)
        assert vault_path.with_suffix(".schedule.json").exists()

    def test_entry_is_persisted(self, vault_path: Path) -> None:
        set_schedule(vault_path, "API_KEY", 60)
        entries = load_schedule(vault_path)
        assert any(e.key == "API_KEY" and e.rotate_every_days == 60 for e in entries)

    def test_overwrite_existing_key(self, vault_path: Path) -> None:
        set_schedule(vault_path, "API_KEY", 30)
        set_schedule(vault_path, "API_KEY", 60)
        entries = load_schedule(vault_path)
        matching = [e for e in entries if e.key == "API_KEY"]
        assert len(matching) == 1
        assert matching[0].rotate_every_days == 60

    def test_raises_on_invalid_interval(self, vault_path: Path) -> None:
        with pytest.raises(SchedulerError):
            set_schedule(vault_path, "KEY", 0)


class TestRemoveSchedule:
    def test_removes_existing_key(self, vault_path: Path) -> None:
        set_schedule(vault_path, "TOKEN", 30)
        removed = remove_schedule(vault_path, "TOKEN")
        assert removed is True
        assert not any(e.key == "TOKEN" for e in load_schedule(vault_path))

    def test_returns_false_for_missing_key(self, vault_path: Path) -> None:
        assert remove_schedule(vault_path, "GHOST") is False


class TestDueKeys:
    def test_returns_overdue_entries(self, vault_path: Path) -> None:
        old = (datetime.utcnow() - timedelta(days=100)).isoformat()
        set_schedule(vault_path, "OLD_KEY", 30, last_rotated=old)
        set_schedule(vault_path, "NEW_KEY", 90)
        overdue = due_keys(vault_path)
        keys = [e.key for e in overdue]
        assert "OLD_KEY" in keys
        assert "NEW_KEY" not in keys

    def test_empty_when_none_due(self, vault_path: Path) -> None:
        set_schedule(vault_path, "FRESH", 90)
        assert due_keys(vault_path) == []
