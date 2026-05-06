"""Archive and restore vault backups as compressed tarballs."""

from __future__ import annotations

import json
import tarfile
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


class ArchiveError(Exception):
    """Raised when an archive operation fails."""


@dataclass
class ArchiveManifest:
    created_at: str
    vault_path: str
    keys: list[str] = field(default_factory=list)


def create_archive(vault_path: Path, password: str, output_dir: Path) -> Path:
    """Encrypt and compress a vault into a .tar.gz archive.

    Args:
        vault_path: Path to the source vault file.
        password: Password used to decrypt the vault for manifest generation.
        output_dir: Directory where the archive will be written.

    Returns:
        Path to the created archive file.

    Raises:
        ArchiveError: If the vault file does not exist or archiving fails.
    """
    if not vault_path.exists():
        raise ArchiveError(f"Vault not found: {vault_path}")

    from envault.vault import Vault

    vault = Vault(vault_path, password)
    keys = vault.list_keys()

    manifest = ArchiveManifest(
        created_at=datetime.now(timezone.utc).isoformat(),
        vault_path=str(vault_path),
        keys=keys,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_name = f"{vault_path.stem}_{timestamp}.tar.gz"
    archive_path = output_dir / archive_name

    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps(manifest.__dict__, indent=2))

        try:
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(vault_path, arcname=vault_path.name)
                tar.add(manifest_file, arcname="manifest.json")
        except Exception as exc:
            raise ArchiveError(f"Failed to create archive: {exc}") from exc

    return archive_path


def restore_archive(archive_path: Path, output_dir: Path) -> ArchiveManifest:
    """Extract a vault archive into output_dir.

    Args:
        archive_path: Path to the .tar.gz archive.
        output_dir: Directory where the vault file will be restored.

    Returns:
        The ArchiveManifest embedded in the archive.

    Raises:
        ArchiveError: If the archive is missing or malformed.
    """
    if not archive_path.exists():
        raise ArchiveError(f"Archive not found: {archive_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            members = tar.getnames()
            if "manifest.json" not in members:
                raise ArchiveError("Archive is missing manifest.json")
            tar.extractall(output_dir)  # noqa: S202
    except tarfile.TarError as exc:
        raise ArchiveError(f"Failed to read archive: {exc}") from exc

    manifest_path = output_dir / "manifest.json"
    data = json.loads(manifest_path.read_text())
    return ArchiveManifest(**data)
