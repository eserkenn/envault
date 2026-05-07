"""CLI commands for the vault clone feature."""

from __future__ import annotations

from pathlib import Path

import click

from envault.cloner import CloneError, clone_vault
from envault.vault import Vault


@click.group(name="clone")
def clone_group() -> None:
    """Clone secrets between vaults."""


@clone_group.command(name="run")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.argument("dest", type=click.Path(path_type=Path))
@click.option("--source-password", prompt=True, hide_input=True, help="Source vault password.")
@click.option("--dest-password", prompt=True, hide_input=True, help="Destination vault password.")
@click.option(
    "--key",
    "keys",
    multiple=True,
    default=None,
    help="Key(s) to clone. Repeat to clone multiple. Omit to clone all.",
)
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys in destination.")
def run_clone(
    source: Path,
    dest: Path,
    source_password: str,
    dest_password: str,
    keys: tuple[str, ...],
    overwrite: bool,
) -> None:
    """Clone secrets from SOURCE vault into DEST vault."""
    try:
        result = clone_vault(
            source_path=source,
            source_password=source_password,
            dest_path=dest,
            dest_password=dest_password,
            keys=list(keys) if keys else None,
            overwrite=overwrite,
        )
    except CloneError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.cloned:
        click.echo(f"Cloned {result.total_cloned} key(s): {', '.join(result.cloned)}")
    else:
        click.echo("No keys were cloned.")

    if result.skipped:
        click.echo(f"Skipped (already exist): {', '.join(result.skipped)}")

    if result.errors:
        click.echo(f"Errors: {', '.join(result.errors)}", err=True)
