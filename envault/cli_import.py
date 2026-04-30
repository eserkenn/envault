"""CLI commands for importing secrets into the vault."""

from __future__ import annotations

from pathlib import Path

import click

from envault.importer import ImportError as EnvImportError
from envault.importer import import_secrets
from envault.vault import Vault, VaultError


@click.group(name="import")
def import_group() -> None:
    """Import environment variables from external files."""


@import_group.command(name="run")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--vault-file",
    default=".envault",
    show_default=True,
    help="Path to the vault file.",
    type=click.Path(path_type=Path),
)
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    help="Vault master password.",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["dotenv", "json"], case_sensitive=False),
    default="dotenv",
    show_default=True,
    help="Format of the source file.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing keys in the vault.",
)
def run_import(source: Path, vault_file: Path, password: str, fmt: str, overwrite: bool) -> None:
    """Import secrets from SOURCE into the vault."""
    try:
        vault = Vault(vault_file, password)
        imported = import_secrets(vault, source, fmt, overwrite=overwrite)
    except VaultError as exc:
        raise click.ClickException(f"Vault error: {exc}") from exc
    except EnvImportError as exc:
        raise click.ClickException(f"Import error: {exc}") from exc
    except OSError as exc:
        raise click.ClickException(f"Could not read source file '{source}': {exc}") from exc

    if imported:
        click.echo(f"Imported {len(imported)} key(s): {', '.join(imported)}.")
    else:
        click.echo("No new keys imported (use --overwrite to replace existing keys).")
