"""Main CLI entry point for envault."""
from __future__ import annotations

import click

from envault.cli_export import export_group
from envault.cli_import import import_group
from envault.cli_targets import target_group
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
from envault.cli_templater import template_group
from envault.vault import Vault, VaultError


@click.group()
def cli() -> None:
    """envault — encrypted environment variable manager."""


@cli.command()
@click.argument("key")
@click.argument("value")
@click.option("--vault", "vault_path", required=True, type=click.Path(), help="Path to vault file.")
@click.option("--password", prompt=True, hide_input=True)
def set(key: str, value: str, vault_path: str, password: str) -> None:  # noqa: A001
    """Set a secret KEY=VALUE in the vault."""
    try:
        vault = Vault(vault_path)  # type: ignore[arg-type]
        vault.set(key, value, password)
        click.echo(f"Set {key}")
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command(name="list")
@click.option("--vault", "vault_path", required=True, type=click.Path(), help="Path to vault file.")
@click.option("--password", prompt=True, hide_input=True)
def list_keys(vault_path: str, password: str) -> None:
    """List all keys stored in the vault."""
    try:
        vault = Vault(vault_path)  # type: ignore[arg-type]
        keys = vault.list_keys(password)
        if not keys:
            click.echo("No secrets stored.")
        else:
            for key in keys:
                click.echo(key)
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc


cli.add_command(export_group)
cli.add_command(import_group)
cli.add_command(target_group)
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
cli.add_command(template_group)
