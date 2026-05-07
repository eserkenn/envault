"""Tests for envault.summarizer."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from envault.summarizer import SummaryError, VaultSummary, summarize_vault


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeVault:
    def __init__(self, data: dict[str, str]):
        self._data = data

    def list_keys(self) -> list[str]:
        return list(self._data.keys())

    def get(self, key: str, password: str) -> str:  # noqa: ARG002
        return self._data[key]


@pytest.fixture()
def vault_mock():
    return _FakeVault(
        {
            "SHORT": "x",
            "LONG_KEY_NAME": "supersecretvalue",
            "MID": "hello",
        }
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSummarizeVault:
    def test_total_keys(self, vault_mock):
        result = summarize_vault(vault_mock, "pass")
        assert result.total_keys == 3

    def test_longest_and_shortest_key(self, vault_mock):
        result = summarize_vault(vault_mock, "pass")
        assert result.longest_key == "LONG_KEY_NAME"
        assert result.shortest_key == "MID"

    def test_avg_value_length(self, vault_mock):
        # "x"=1, "supersecretvalue"=16, "hello"=5 → avg = 22/3 ≈ 7.33
        result = summarize_vault(vault_mock, "pass")
        assert result.avg_value_length == round((1 + 16 + 5) / 3, 2)

    def test_empty_vault_returns_default_summary(self):
        vault = _FakeVault({})
        result = summarize_vault(vault, "pass")
        assert result.total_keys == 0
        assert result.longest_key is None
        assert result.shortest_key is None
        assert result.avg_value_length == 0.0

    def test_raises_on_vault_read_error(self):
        bad_vault = MagicMock()
        bad_vault.list_keys.side_effect = RuntimeError("disk error")
        with pytest.raises(SummaryError, match="disk error"):
            summarize_vault(bad_vault, "pass")

    def test_untagged_keys_count(self, vault_mock):
        result = summarize_vault(vault_mock, "pass")
        # _FakeVault has no get_meta → all untagged
        assert result.untagged_keys == result.total_keys
        assert result.tagged_keys == 0

    def test_key_lengths_populated(self, vault_mock):
        result = summarize_vault(vault_mock, "pass")
        assert result.key_lengths["SHORT"] == len("SHORT")
        assert result.key_lengths["LONG_KEY_NAME"] == len("LONG_KEY_NAME")

    def test_vault_summary_is_dataclass(self, vault_mock):
        result = summarize_vault(vault_mock, "pass")
        assert isinstance(result, VaultSummary)
