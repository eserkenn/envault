"""Main CLI entry point for envault."""

from __future__ import annotations

import click

from envault.cli_export import export_group
from envault.cli_import import import_group
from envault.cli_targets import target_group


@click.group()
@click.version_option(package_name="envault")
def cli() -> None:
    """envault — manage and encrypt environment variables across deployment targets."""


cli.add_command(target_group)
cli.add_command(export_group)
cli.add_command(import_group)


@cli.command()
@click.argument("key")
@click.argument("value")
@click.option(
    "--vault-file",
    default=".envault",
    show_default=True,
    type=click.Path(),
    help="Path to the vault file.",
)
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    help="Vault master password.",
)
def set(key: str, value: str, vault_file: str, password: str) -> None:  # noqa: A001
    """Store KEY=VALUE in the vault."""
    from pathlib import Path

    from envault.vault import Vault, VaultError

    try:
        vault = Vault(Path(vault_file), password)
        vault.set(key, value)
        click.echo(f"Stored {key!r} in vault.")
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command(name="list")
@click.option(
    "--vault-file",
    default=".envault",
    show_default=True,
    type=click.Path(),
    help="Path to the vault file.",
)
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    help="Vault master password.",
)
def list_keys(vault_file: str, password: str) -> None:
    """List all keys stored in the vault."""
    from pathlib import Path

    from envault.vault import Vault, VaultError

    try:
        vault = Vault(Path(vault_file), password)
        keys = vault.keys()
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc

    if keys:
        for k in sorted(keys):
            click.echo(k)
    else:
        click.echo("Vault is empty.")


if __name__ == "__main__":
    cli()
