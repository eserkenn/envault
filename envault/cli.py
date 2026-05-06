"""Main CLI entry point for envault."""
from __future__ import annotations

import click

from envault.cli_export import export_group
from envault.cli_import import import_group
from envault.cli_rotate import rotate_group
from envault.cli_targets import target_group
from envault.cli_diff import diff_group
from envault.cli_lint import lint_group
from envault.cli_snapshot import snapshot_group
from envault.cli_search import search_group
from envault.cli_rename import rename_group
from envault.cli_tagger import tag_group
from envault.vault import Vault, VaultError


@click.group()
@click.version_option()
def cli() -> None:
    """envault — encrypted environment variable manager."""


@cli.command()
@click.argument("vault_path")
@click.argument("password")
@click.argument("key")
@click.argument("value")
def set(vault_path: str, password: str, key: str, value: str) -> None:
    """Set a secret KEY=VALUE in the vault."""
    try:
        vault = Vault(vault_path, password)
        vault.set(key, value)
        click.echo(f"Set '{key}' in vault.")
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command(name="list")
@click.argument("vault_path")
@click.argument("password")
def list_keys(vault_path: str, password: str) -> None:
    """List all keys stored in the vault."""
    try:
        vault = Vault(vault_path, password)
        keys = [k for k in vault.list_keys() if not k.startswith("__tags__")]
        if keys:
            for key in keys:
                click.echo(key)
        else:
            click.echo("Vault is empty.")
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc


cli.add_command(export_group)
cli.add_command(import_group)
cli.add_command(rotate_group)
cli.add_command(target_group)
cli.add_command(diff_group)
cli.add_command(lint_group)
cli.add_command(snapshot_group)
cli.add_command(search_group)
cli.add_command(rename_group)
cli.add_command(tag_group)
