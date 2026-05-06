"""Tests for envault.comparator."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.comparator import CompareError, CompareResult, compare_vaults
from envault.vault import Vault


PASSWORD = "test-password"


@pytest.fixture()
def left_vault(tmp_path: Path) -> Path:
    path = tmp_path / "left.vault"
    v = Vault(path, PASSWORD)
    v.set("SHARED_SAME", "value1")
    v.set("SHARED_DIFF", "left-value")
    v.set("ONLY_LEFT", "secret")
    return path


@pytest.fixture()
def right_vault(tmp_path: Path) -> Path:
    path = tmp_path / "right.vault"
    v = Vault(path, PASSWORD)
    v.set("SHARED_SAME", "value1")
    v.set("SHARED_DIFF", "right-value")
    v.set("ONLY_RIGHT", "secret")
    return path


class TestCompareVaults:
    def test_only_in_left(self, left_vault: Path, right_vault: Path) -> None:
        result = compare_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
        assert "ONLY_LEFT" in result.only_in_left

    def test_only_in_right(self, left_vault: Path, right_vault: Path) -> None:
        result = compare_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
        assert "ONLY_RIGHT" in result.only_in_right

    def test_in_both_same(self, left_vault: Path, right_vault: Path) -> None:
        result = compare_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
        assert "SHARED_SAME" in result.in_both_same

    def test_in_both_different(self, left_vault: Path, right_vault: Path) -> None:
        result = compare_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
        assert "SHARED_DIFF" in result.in_both_different

    def test_is_identical_false(self, left_vault: Path, right_vault: Path) -> None:
        result = compare_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
        assert not result.is_identical

    def test_is_identical_true(self, tmp_path: Path) -> None:
        p1 = tmp_path / "a.vault"
        p2 = tmp_path / "b.vault"
        for p in (p1, p2):
            v = Vault(p, PASSWORD)
            v.set("KEY", "value")
        result = compare_vaults(p1, PASSWORD, p2, PASSWORD)
        assert result.is_identical

    def test_similarity_pct(self, left_vault: Path, right_vault: Path) -> None:
        result = compare_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
        # 1 same out of 4 unique keys
        assert result.similarity_pct == 25.0

    def test_all_keys_union(self, left_vault: Path, right_vault: Path) -> None:
        result = compare_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
        assert result.all_keys == {"SHARED_SAME", "SHARED_DIFF", "ONLY_LEFT", "ONLY_RIGHT"}

    def test_raises_compare_error_on_bad_password(self, left_vault: Path, right_vault: Path) -> None:
        with pytest.raises(CompareError):
            compare_vaults(left_vault, "wrong", right_vault, PASSWORD)


class TestCompareResult:
    def test_empty_vaults_are_identical(self) -> None:
        r = CompareResult()
        assert r.is_identical
        assert r.similarity_pct == 100.0
