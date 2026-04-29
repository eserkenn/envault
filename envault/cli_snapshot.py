"""CLI commands for vault snapshot / restore."""

from __future__ import annotations

from pathlib import Path

import click

from envault.snapshot import SnapshotError, create_snapshot, list_snapshots, restore_snapshot


@click.group("snapshot")
def snapshot_group() -> None:
    """Create and restore vault snapshots."""


@snapshot_group.command("create")
@click.argument("vault_file", type=click.Path(exists=True, path_type=Path))
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option(
    "--snapshots-dir",
    default=".snapshots",
    show_default=True,
    type=click.Path(path_type=Path),
    help="Directory to store snapshots.",
)
def create_cmd(vault_file: Path, password: str, snapshots_dir: Path) -> None:
    """Create a snapshot of VAULT_FILE."""
    try:
        out = create_snapshot(vault_file, password, snapshots_dir)
        click.echo(f"Snapshot created: {out}")
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc


@snapshot_group.command("list")
@click.option(
    "--snapshots-dir",
    default=".snapshots",
    show_default=True,
    type=click.Path(path_type=Path),
    help="Directory containing snapshots.",
)
def list_cmd(snapshots_dir: Path) -> None:
    """List available snapshots."""
    snaps = list_snapshots(snapshots_dir)
    if not snaps:
        click.echo("No snapshots found.")
        return
    for snap in snaps:
        click.echo(snap.name)


@snapshot_group.command("restore")
@click.argument("snapshot_file", type=click.Path(exists=True, path_type=Path))
@click.argument("vault_file", type=click.Path(path_type=Path))
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def restore_cmd(snapshot_file: Path, vault_file: Path, password: str) -> None:
    """Restore secrets from SNAPSHOT_FILE into VAULT_FILE."""
    try:
        keys = restore_snapshot(snapshot_file, vault_file, password)
        click.echo(f"Restored {len(keys)} key(s): {', '.join(keys)}")
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc
