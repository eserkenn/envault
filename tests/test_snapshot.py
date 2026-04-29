"""Tests for envault.snapshot."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.snapshot import SnapshotError, create_snapshot, list_snapshots, restore_snapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vault_mock(keys_and_values: dict):
    mock = MagicMock()
    mock.list_keys.return_value = list(keys_and_values.keys())
    mock.get.side_effect = lambda k: keys_and_values[k]
    return mock


# ---------------------------------------------------------------------------
# create_snapshot
# ---------------------------------------------------------------------------

class TestCreateSnapshot:
    def test_creates_snapshot_file(self, tmp_path):
        vault_file = tmp_path / "vault.json"
        vault_file.touch()
        snap_dir = tmp_path / "snaps"
        secrets = {"KEY": "value"}

        with patch("envault.snapshot.Vault", return_value=_make_vault_mock(secrets)):
            result = create_snapshot(vault_file, "pass", snap_dir)

        assert result.exists()
        assert result.suffix == ".json"

    def test_snapshot_contains_secrets(self, tmp_path):
        vault_file = tmp_path / "vault.json"
        vault_file.touch()
        secrets = {"DB_URL": "postgres://localhost", "API_KEY": "abc123"}

        with patch("envault.snapshot.Vault", return_value=_make_vault_mock(secrets)):
            result = create_snapshot(vault_file, "pass", tmp_path / "snaps")

        payload = json.loads(result.read_text())
        assert payload["secrets"] == secrets

    def test_raises_on_empty_vault(self, tmp_path):
        vault_file = tmp_path / "vault.json"
        vault_file.touch()

        with patch("envault.snapshot.Vault", return_value=_make_vault_mock({})):
            with pytest.raises(SnapshotError, match="empty"):
                create_snapshot(vault_file, "pass", tmp_path / "snaps")


# ---------------------------------------------------------------------------
# list_snapshots
# ---------------------------------------------------------------------------

class TestListSnapshots:
    def test_returns_empty_list_when_dir_missing(self, tmp_path):
        assert list_snapshots(tmp_path / "nonexistent") == []

    def test_returns_sorted_snapshots(self, tmp_path):
        for name in ("snapshot_300.json", "snapshot_100.json", "snapshot_200.json"):
            (tmp_path / name).write_text("{}")
        names = [p.name for p in list_snapshots(tmp_path)]
        assert names == ["snapshot_100.json", "snapshot_200.json", "snapshot_300.json"]


# ---------------------------------------------------------------------------
# restore_snapshot
# ---------------------------------------------------------------------------

class TestRestoreSnapshot:
    def test_restores_keys(self, tmp_path):
        snap = tmp_path / "snapshot_1.json"
        snap.write_text(json.dumps({"timestamp": 1, "secrets": {"FOO": "bar"}}))
        vault_file = tmp_path / "vault.json"
        vault_file.touch()
        mock_vault = MagicMock()

        with patch("envault.snapshot.Vault", return_value=mock_vault):
            keys = restore_snapshot(snap, vault_file, "pass")

        assert keys == ["FOO"]
        mock_vault.set.assert_called_once_with("FOO", "bar")

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(SnapshotError, match="not found"):
            restore_snapshot(tmp_path / "ghost.json", tmp_path / "v.json", "p")

    def test_raises_on_invalid_json(self, tmp_path):
        snap = tmp_path / "snapshot_bad.json"
        snap.write_text("not-json")
        with pytest.raises(SnapshotError, match="Invalid"):
            restore_snapshot(snap, tmp_path / "v.json", "p")
