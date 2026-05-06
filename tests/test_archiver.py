"""Tests for envault.archiver."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.archiver import ArchiveError, ArchiveManifest, create_archive, restore_archive


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    """Create a minimal vault file on disk."""
    vf = tmp_path / "secrets.vault"
    vf.write_bytes(b"{\"data\": {}}")
    return vf


@pytest.fixture()
def archive_dir(tmp_path: Path) -> Path:
    return tmp_path / "archives"


@pytest.fixture()
def mock_vault():
    """Patch Vault so tests don't need real encryption."""
    with patch("envault.archiver.Vault") as MockVault:
        instance = MagicMock()
        instance.list_keys.return_value = ["DB_URL", "SECRET_KEY"]
        MockVault.return_value = instance
        yield MockVault


class TestCreateArchive:
    def test_raises_when_vault_missing(self, tmp_path: Path, archive_dir: Path):
        missing = tmp_path / "nope.vault"
        with pytest.raises(ArchiveError, match="Vault not found"):
            create_archive(missing, "pw", archive_dir)

    def test_returns_path_to_archive(self, vault_file: Path, archive_dir: Path, mock_vault):
        result = create_archive(vault_file, "pw", archive_dir)
        assert result.suffix == ".gz"
        assert result.exists()

    def test_archive_filename_contains_vault_stem(self, vault_file: Path, archive_dir: Path, mock_vault):
        result = create_archive(vault_file, "pw", archive_dir)
        assert "secrets" in result.name

    def test_archive_contains_vault_file(self, vault_file: Path, archive_dir: Path, mock_vault):
        import tarfile

        result = create_archive(vault_file, "pw", archive_dir)
        with tarfile.open(result, "r:gz") as tar:
            names = tar.getnames()
        assert vault_file.name in names

    def test_archive_contains_manifest(self, vault_file: Path, archive_dir: Path, mock_vault):
        import tarfile

        result = create_archive(vault_file, "pw", archive_dir)
        with tarfile.open(result, "r:gz") as tar:
            names = tar.getnames()
        assert "manifest.json" in names

    def test_manifest_lists_keys(self, vault_file: Path, archive_dir: Path, mock_vault):
        import tarfile

        result = create_archive(vault_file, "pw", archive_dir)
        with tarfile.open(result, "r:gz") as tar:
            member = tar.extractfile("manifest.json")
            data = json.loads(member.read())
        assert data["keys"] == ["DB_URL", "SECRET_KEY"]


class TestRestoreArchive:
    def test_raises_when_archive_missing(self, tmp_path: Path):
        with pytest.raises(ArchiveError, match="Archive not found"):
            restore_archive(tmp_path / "ghost.tar.gz", tmp_path / "out")

    def test_returns_manifest(self, vault_file: Path, archive_dir: Path, tmp_path: Path, mock_vault):
        archive = create_archive(vault_file, "pw", archive_dir)
        restore_dir = tmp_path / "restored"
        manifest = restore_archive(archive, restore_dir)
        assert isinstance(manifest, ArchiveManifest)
        assert manifest.keys == ["DB_URL", "SECRET_KEY"]

    def test_vault_file_restored(self, vault_file: Path, archive_dir: Path, tmp_path: Path, mock_vault):
        archive = create_archive(vault_file, "pw", archive_dir)
        restore_dir = tmp_path / "restored"
        restore_archive(archive, restore_dir)
        assert (restore_dir / vault_file.name).exists()

    def test_raises_on_corrupt_archive(self, tmp_path: Path):
        bad = tmp_path / "bad.tar.gz"
        bad.write_bytes(b"not a tarball")
        with pytest.raises(ArchiveError, match="Failed to read archive"):
            restore_archive(bad, tmp_path / "out")
