"""Tests for envault.inspector."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.inspector import InspectError, InspectResult, inspect_vault
from envault.vault import Vault


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.vault"
    v = Vault(path, "secret")
    v.set("ALPHA", "one")
    v.set("BETA_KEY", "two")
    v.set("G", "three")
    return path


class TestInspectVault:
    def test_returns_inspect_result(self, vault_file: Path) -> None:
        result = inspect_vault(vault_file, "secret")
        assert isinstance(result, InspectResult)

    def test_total_keys_correct(self, vault_file: Path) -> None:
        result = inspect_vault(vault_file, "secret")
        assert result.total_keys == 3

    def test_key_names_sorted(self, vault_file: Path) -> None:
        result = inspect_vault(vault_file, "secret")
        assert result.key_names == sorted(result.key_names)

    def test_file_size_positive(self, vault_file: Path) -> None:
        result = inspect_vault(vault_file, "secret")
        assert result.file_size_bytes > 0

    def test_longest_key(self, vault_file: Path) -> None:
        result = inspect_vault(vault_file, "secret")
        assert result.longest_key == "BETA_KEY"

    def test_shortest_key(self, vault_file: Path) -> None:
        result = inspect_vault(vault_file, "secret")
        assert result.shortest_key == "G"

    def test_avg_key_length(self, vault_file: Path) -> None:
        result = inspect_vault(vault_file, "secret")
        expected = (len("ALPHA") + len("BETA_KEY") + len("G")) / 3
        assert result.avg_key_length == pytest.approx(expected)

    def test_has_targets_false_by_default(self, vault_file: Path) -> None:
        result = inspect_vault(vault_file, "secret")
        assert result.has_targets is False

    def test_has_audit_false_by_default(self, vault_file: Path) -> None:
        result = inspect_vault(vault_file, "secret")
        assert result.has_audit_log is False

    def test_has_targets_true_when_file_present(self, vault_file: Path) -> None:
        vault_file.with_suffix(".targets.json").write_text("{}")
        result = inspect_vault(vault_file, "secret")
        assert result.has_targets is True

    def test_raises_on_missing_vault(self, tmp_path: Path) -> None:
        with pytest.raises(InspectError, match="not found"):
            inspect_vault(tmp_path / "ghost.vault", "secret")

    def test_avg_key_length_zero_when_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.vault"
        Vault(path, "pw")
        result = inspect_vault(path, "pw")
        assert result.avg_key_length == 0.0
