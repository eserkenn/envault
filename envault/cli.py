"""Root CLI entry point for envault."""

from __future__ import annotations

import click

from envault.cli_targets import target_group
from envault.cli_export import export_group
from envault.cli_import import import_group
from envault.cli_rotate import rotate_group
from envault.cli_diff import diff_group
from envault.cli_lint import lint_group
from envault.cli_snapshot import snapshot_group
from envault.cli_search import search_group
from envault.cli_rename import rename_group
from envault.cli_tagger import tag_group
from envault.cli_scheduler import schedule_group
from envault.cli_validator import validate_group
from envault.cli_comparator import compare_group
from envault.vault import Vault, VaultError


@click.group()
@click.version_option()
def cli() -> None:
    """envault — encrypted environment variable manager."""


@cli.command()
@click.argument("key")
@click.argument("value")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.option("--password", prompt=True, hide_input=True, envvar="ENVAULT_PASSWORD")
def set(key: str, value: str, vault_path: str, password: str) -> None:
    """Set a secret KEY to VALUE in the vault."""
    try:
        v = Vault(vault_path, password)
        v.set(key, value)
        click.echo(f"Set {key}")
    except VaultError as exc:
        raise click.ClickException(str(exc))


@cli.command("list")
@click.option("--vault", "vault_path", default=".envault", show_default=True)
@click.option("--password", prompt=True, hide_input=True, envvar="ENVAULT_PASSWORD")
def list_keys(vault_path: str, password: str) -> None:
    """List all keys stored in the vault."""
    try:
        v = Vault(vault_path, password)
        keys = v.list_keys()
        if not keys:
            click.echo("No secrets stored.")
        for key in keys:
            click.echo(key)
    except VaultError as exc:
        raise click.ClickException(str(exc))


cli.add_command(target_group)
cli.add_command(export_group)
cli.add_command(import_group)
cli.add_command(rotate_group)
cli.add_command(diff_group)
cli.add_command(lint_group)
cli.add_command(snapshot_group)
cli.add_command(search_group)
cli.add_command(rename_group)
cli.add_command(tag_group)
cli.add_command(schedule_group)
cli.add_command(validate_group)
cli.add_command(compare_group)
