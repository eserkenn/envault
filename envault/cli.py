"""Entry-point for the envault CLI."""

from __future__ import annotations

import click

from envault.cli_export import export_group
from envault.cli_import import import_group
from envault.cli_rotate import rotate_group
from envault.cli_targets import target_group
from envault.vault import Vault, VaultError


@click.group()
def cli() -> None:
    """envault — manage and encrypt environment variables."""


# ---------------------------------------------------------------------------
# Inline vault commands
# ---------------------------------------------------------------------------


@cli.command("set")
@click.argument("vault_path")
@click.argument("key")
@click.argument("value")
@click.option("--password", prompt=True, hide_input=True)
def set(vault_path: str, key: str, value: str, password: str) -> None:
    """Set KEY=VALUE in VAULT_PATH."""
    try:
        vault = Vault(vault_path, password)
        vault.set(key, value)
        click.echo(f"Set '{key}' in {vault_path}.")
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command("list")
@click.argument("vault_path")
@click.option("--password", prompt=True, hide_input=True)
def list_keys(vault_path: str, password: str) -> None:
    """List all keys stored in VAULT_PATH."""
    try:
        vault = Vault(vault_path, password)
        keys = vault.list_keys()
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc

    if keys:
        click.echo("\n".join(sorted(keys)))
    else:
        click.echo("Vault is empty.")


# ---------------------------------------------------------------------------
# Sub-command groups
# ---------------------------------------------------------------------------

cli.add_command(export_group)
cli.add_command(import_group)
cli.add_command(rotate_group)
cli.add_command(target_group)

if __name__ == "__main__":
    cli()
