"""Scheduled rotation reminders and expiry tracking for vault secrets."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional


class SchedulerError(Exception):
    """Raised when a scheduling operation fails."""


@dataclass
class ScheduleEntry:
    key: str
    rotate_every_days: int
    last_rotated: str  # ISO 8601
    tags: List[str] = field(default_factory=list)

    def next_rotation(self) -> datetime:
        last = datetime.fromisoformat(self.last_rotated)
        return last + timedelta(days=self.rotate_every_days)

    def is_due(self, as_of: Optional[datetime] = None) -> bool:
        as_of = as_of or datetime.utcnow()
        return as_of >= self.next_rotation()

    def days_until_due(self, as_of: Optional[datetime] = None) -> int:
        as_of = as_of or datetime.utcnow()
        delta = self.next_rotation() - as_of
        return max(0, delta.days)


def _schedule_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".schedule.json")


def load_schedule(vault_path: Path) -> List[ScheduleEntry]:
    path = _schedule_path(vault_path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SchedulerError(f"Failed to parse schedule file '{path}': {exc}") from exc
    if not isinstance(data, list):
        raise SchedulerError(f"Schedule file '{path}' must contain a JSON array")
    try:
        return [ScheduleEntry(**e) for e in data]
    except (TypeError, KeyError) as exc:
        raise SchedulerError(f"Invalid schedule entry in '{path}': {exc}") from exc


def save_schedule(vault_path: Path, entries: List[ScheduleEntry]) -> None:
    path = _schedule_path(vault_path)
    path.write_text(json.dumps([asdict(e) for e in entries], indent=2))


def set_schedule(vault_path: Path, key: str, rotate_every_days: int,
                 last_rotated: Optional[str] = None,
                 tags: Optional[List[str]] = None) -> ScheduleEntry:
    if rotate_every_days < 1:
        raise SchedulerError("rotate_every_days must be at least 1")
    entries = load_schedule(vault_path)
    entries = [e for e in entries if e.key != key]
    entry = ScheduleEntry(
        key=key,
        rotate_every_days=rotate_every_days,
        last_rotated=last_rotated or datetime.utcnow().isoformat(),
        tags=tags or [],
    )
    entries.append(entry)
    save_schedule(vault_path, entries)
    return entry


def remove_schedule(vault_path: Path, key: str) -> bool:
    entries = load_schedule(vault_path)
    filtered = [e for e in entries if e.key != key]
    if len(filtered) == len(entries):
        return False
    save_schedule(vault_path, filtered)
    return True


def due_keys(vault_path: Path, as_of: Optional[datetime] = None) -> List[ScheduleEntry]:
    return [e for e in load_schedule(vault_path) if e.is_due(as_of)]
