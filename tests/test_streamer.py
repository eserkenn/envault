"""Tests for envault.streamer."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from envault.streamer import StreamError, StreamRecord, _render_record, stream_vault
from envault.vault import VaultError


@pytest.fixture()
def vault_mock() -> MagicMock:
    mock = MagicMock()
    mock.list_keys.return_value = ["DB_HOST", "DB_PASS", "API_KEY"]
    mock.get.side_effect = lambda key, pwd: f"value_of_{key}"
    return mock


class TestStreamVault:
    def test_yields_all_keys(self, vault_mock: MagicMock) -> None:
        records = list(stream_vault(vault_mock, "secret"))
        assert len(records) == 3

    def test_record_fields_populated(self, vault_mock: MagicMock) -> None:
        records = list(stream_vault(vault_mock, "secret"))
        first = records[0]
        assert first.key == "DB_HOST"
        assert first.value == "value_of_DB_HOST"
        assert first.index == 1
        assert first.total == 3

    def test_prefix_filter(self, vault_mock: MagicMock) -> None:
        records = list(stream_vault(vault_mock, "secret", prefix="DB_"))
        keys = [r.key for r in records]
        assert keys == ["DB_HOST", "DB_PASS"]

    def test_explicit_keys_filter(self, vault_mock: MagicMock) -> None:
        records = list(stream_vault(vault_mock, "secret", keys=["API_KEY"]))
        assert len(records) == 1
        assert records[0].key == "API_KEY"

    def test_raises_stream_error_on_list_failure(self) -> None:
        bad_vault = MagicMock()
        bad_vault.list_keys.side_effect = VaultError("boom")
        with pytest.raises(StreamError, match="Cannot list vault keys"):
            list(stream_vault(bad_vault, "secret"))

    def test_raises_stream_error_on_decrypt_failure(self, vault_mock: MagicMock) -> None:
        vault_mock.get.side_effect = VaultError("bad password")
        with pytest.raises(StreamError, match="Failed to decrypt"):
            list(stream_vault(vault_mock, "wrong"))

    def test_index_and_total_are_correct(self, vault_mock: MagicMock) -> None:
        records = list(stream_vault(vault_mock, "secret"))
        for i, record in enumerate(records, start=1):
            assert record.index == i
            assert record.total == 3


class TestRenderRecord:
    def _record(self, key: str = "FOO", value: str = "bar") -> StreamRecord:
        return StreamRecord(key=key, value=value, index=1, total=1)

    def test_plain_format(self) -> None:
        assert _render_record(self._record(), "plain") == "FOO=bar"

    def test_dotenv_format(self) -> None:
        assert _render_record(self._record(), "dotenv") == 'FOO="bar"'

    def test_dotenv_escapes_quotes(self) -> None:
        r = self._record(value='say "hello"')
        assert _render_record(r, "dotenv") == 'FOO="say \\"hello\\""'

    def test_json_format(self) -> None:
        import json
        output = _render_record(self._record(), "json")
        data = json.loads(output)
        assert data == {"key": "FOO", "value": "bar"}
