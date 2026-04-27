"""Tests for envault.targets module."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.targets import TargetManager, TargetError


@pytest.fixture
def targets_file(tmp_path: Path) -> Path:
    return tmp_path / ".envault-targets.json"


@pytest.fixture
def manager(targets_file: Path) -> TargetManager:
    return TargetManager(targets_path=targets_file)


class TestTargetAdd:
    def test_creates_targets_file(self, manager: TargetManager, targets_file: Path):
        manager.add("staging", ".envault-staging.json")
        assert targets_file.exists()

    def test_target_is_persisted(self, manager: TargetManager, targets_file: Path):
        manager.add("prod", ".envault-prod.json", description="Production")
        data = json.loads(targets_file.read_text())
        assert "prod" in data
        assert data["prod"]["vault_path"] == ".envault-prod.json"
        assert data["prod"]["description"] == "Production"

    def test_duplicate_raises(self, manager: TargetManager):
        manager.add("staging", ".envault-staging.json")
        with pytest.raises(TargetError, match="already exists"):
            manager.add("staging", ".envault-staging-2.json")


class TestTargetRemove:
    def test_removes_target(self, manager: TargetManager, targets_file: Path):
        manager.add("staging", ".envault-staging.json")
        manager.remove("staging")
        data = json.loads(targets_file.read_text())
        assert "staging" not in data

    def test_remove_nonexistent_raises(self, manager: TargetManager):
        with pytest.raises(TargetError, match="not found"):
            manager.remove("ghost")


class TestTargetGet:
    def test_get_returns_metadata(self, manager: TargetManager):
        manager.add("prod", ".envault-prod.json", description="Live")
        info = manager.get("prod")
        assert info["vault_path"] == ".envault-prod.json"
        assert info["description"] == "Live"

    def test_get_missing_raises(self, manager: TargetManager):
        with pytest.raises(TargetError, match="not found"):
            manager.get("missing")

    def test_vault_path_returns_path_object(self, manager: TargetManager):
        manager.add("staging", ".envault-staging.json")
        vp = manager.vault_path("staging")
        assert isinstance(vp, Path)
        assert vp == Path(".envault-staging.json")


class TestTargetList:
    def test_empty_list(self, manager: TargetManager):
        assert manager.list_targets() == []

    def test_lists_all_targets(self, manager: TargetManager):
        manager.add("staging", ".envault-staging.json")
        manager.add("prod", ".envault-prod.json")
        names = manager.list_targets()
        assert set(names) == {"staging", "prod"}


def test_corrupted_file_raises(tmp_path: Path):
    bad_file = tmp_path / ".envault-targets.json"
    bad_file.write_text("{not valid json")
    with pytest.raises(TargetError, match="Corrupted"):
        TargetManager(targets_path=bad_file)
