"""CLI commands for vault inspection."""

from __future__ import annotations

from pathlib import Path

import click

from envault.inspector import InspectError, inspect_vault


@click.group("inspect")
def inspect_group() -> None:
    """Inspect vault metadata and health."""


@inspect_group.command("run")
@click.argument("vault_file", type=click.Path(exists=True, path_type=Path))
@click.password_option("--password", "-p", prompt=True, confirmation_prompt=False)
@click.option("--keys", "show_keys", is_flag=True, default=False, help="List all key names.")
def run_inspect(vault_file: Path, password: str, show_keys: bool) -> None:
    """Display metadata and health information for VAULT_FILE."""
    try:
        result = inspect_vault(vault_file, password)
    except InspectError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    click.echo(f"Vault       : {result.vault_path}")
    click.echo(f"Total keys  : {result.total_keys}")
    click.echo(f"File size   : {result.file_size_bytes} bytes")
    click.echo(f"Has targets : {'yes' if result.has_targets else 'no'}")
    click.echo(f"Has audit   : {'yes' if result.has_audit_log else 'no'}")

    if result.total_keys:
        click.echo(f"Longest key : {result.longest_key}")
        click.echo(f"Shortest key: {result.shortest_key}")
        click.echo(f"Avg key len : {result.avg_key_length:.1f}")

    if show_keys:
        click.echo("\nKeys:")
        for key in result.key_names:
            click.echo(f"  {key}")
