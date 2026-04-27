"""Tests for envault.cli_rotate."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.cli_rotate import rotate_group
from envault.rotator import RotationError


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def mock_rotate():
    with patch("envault.cli_rotate.rotate_key") as m:
        yield m


class TestRunRotate:
    def test_outputs_rotated_keys(self, runner, mock_rotate):
        mock_rotate.return_value = ["DB_URL", "API_KEY"]
        result = runner.invoke(
            rotate_group,
            ["run", "my.vault", "--old-password", "old", "--new-password", "new"],
        )
        assert result.exit_code == 0
        assert "2 key(s)" in result.output
        assert "DB_URL" in result.output

    def test_empty_vault_message(self, runner, mock_rotate):
        mock_rotate.return_value = []
        result = runner.invoke(
            rotate_group,
            ["run", "my.vault", "--old-password", "old", "--new-password", "new"],
        )
        assert result.exit_code == 0
        assert "empty" in result.output.lower()

    def test_same_password_raises_usage_error(self, runner, mock_rotate):
        result = runner.invoke(
            rotate_group,
            ["run", "my.vault", "--old-password", "same", "--new-password", "same"],
        )
        assert result.exit_code != 0
        assert "differ" in result.output.lower()

    def test_rotation_error_shown_as_click_exception(self, runner, mock_rotate):
        mock_rotate.side_effect = RotationError("bad decrypt")
        result = runner.invoke(
            rotate_group,
            ["run", "my.vault", "--old-password", "old", "--new-password", "new"],
        )
        assert result.exit_code != 0
        assert "bad decrypt" in result.output
