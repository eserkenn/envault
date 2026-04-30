"""Entry-point for the envault CLI."""

from __future__ import annotations

import click

from envault.cli_diff import diff_group
from envault.cli_export import export_group
from envault.cli_import import import_group
from envault.cli_lint import lint_group
from envault.cli_rename import rename_group
from envault.cli_rotate import rotate_group
from envault.cli_search import search_group
from envault.cli_snapshot import snapshot_group
from envault.cli_targets import target_group
from envault.vault import Vault, VaultError


@click.group()
@click.version_option()
def cli() -> None:
    """envault — encrypted environment variable manager."""


@cli.command()
@click.argument("vault_path")
@click.argument("key")
@click.argument("value")
@click.option("--password", prompt=True, hide_input=True)
def set(vault_path: str, key: str, value: str, password: str) -> None:  # noqa: A001
    """Set KEY to VALUE in VAULT_PATH."""
    try:
        vault = Vault(vault_path)
        vault.set(key, value, password)
        click.echo(f"Set '{key}' in {vault_path}")
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command(name="list")
@click.argument("vault_path")
def list_keys(vault_path: str) -> None:
    """List all keys stored in VAULT_PATH."""
    try:
        vault = Vault(vault_path)
        keys = vault.list_keys()
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc

    if not keys:
        click.echo("No keys found.")
        return
    for key in sorted(keys):
        click.echo(key)


cli.add_command(target_group)
cli.add_command(export_group)
cli.add_command(import_group)
cli.add_command(rotate_group)
cli.add_command(diff_group)
cli.add_command(lint_group)
cli.add_command(snapshot_group)
cli.add_command(search_group)
cli.add_command(rename_group)
