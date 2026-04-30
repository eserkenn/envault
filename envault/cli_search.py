"""CLI commands for searching secrets in a vault."""

from __future__ import annotations

import click

from envault.search import SearchError, search_vault
from envault.vault import Vault, VaultError


@click.group(name="search")
def search_group() -> None:
    """Search secrets in a vault."""


@search_group.command(name="run")
@click.argument("vault_file")
@click.argument("pattern")
@click.password_option("--password", "-p", prompt="Vault password", confirmation_prompt=False)
@click.option("--values", "-v", is_flag=True, default=False, help="Also search secret values.")
@click.option("--regex", "-r", is_flag=True, default=False, help="Treat pattern as regex.")
def run_search(
    vault_file: str,
    pattern: str,
    password: str,
    values: bool,
    regex: bool,
) -> None:
    """Search VAULT_FILE for keys (and optionally values) matching PATTERN."""
    try:
        vault = Vault(vault_file)
    except VaultError as exc:
        raise click.ClickException(str(exc))

    try:
        results = search_vault(
            vault=vault,
            password=password,
            pattern=pattern,
            search_values=values,
            use_regex=regex,
        )
    except SearchError as exc:
        raise click.ClickException(str(exc))

    if not results:
        click.echo("No matches found.")
        return

    click.echo(f"Found {len(results)} match(es):")
    for result in results:
        click.echo(f"  [{result.matched_by}] {result.key}")
