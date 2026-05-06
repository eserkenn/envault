"""CLI commands for secret tagging."""
from __future__ import annotations

import click

from envault.tagger import TaggerError, add_tags, get_tags, list_by_tag, remove_tags
from envault.vault import Vault, VaultError


@click.group(name="tag")
def tag_group() -> None:
    """Manage tags on vault secrets."""


@tag_group.command("add")
@click.argument("vault_path")
@click.argument("password")
@click.argument("key")
@click.argument("tags", nargs=-1, required=True)
def run_add(vault_path: str, password: str, key: str, tags: tuple) -> None:
    """Add TAGS to KEY in the vault."""
    try:
        vault = Vault(vault_path, password)
        result = add_tags(vault, key, list(tags))
        click.echo(f"Tags for '{result.key}': {', '.join(result.tags) or '(none)'}")
    except (TaggerError, VaultError) as exc:
        raise click.ClickException(str(exc)) from exc


@tag_group.command("remove")
@click.argument("vault_path")
@click.argument("password")
@click.argument("key")
@click.argument("tags", nargs=-1, required=True)
def run_remove(vault_path: str, password: str, key: str, tags: tuple) -> None:
    """Remove TAGS from KEY in the vault."""
    try:
        vault = Vault(vault_path, password)
        result = remove_tags(vault, key, list(tags))
        click.echo(f"Tags for '{result.key}': {', '.join(result.tags) or '(none)'}")
    except (TaggerError, VaultError) as exc:
        raise click.ClickException(str(exc)) from exc


@tag_group.command("list")
@click.argument("vault_path")
@click.argument("password")
@click.argument("key")
def run_list(vault_path: str, password: str, key: str) -> None:
    """List tags for KEY."""
    try:
        vault = Vault(vault_path, password)
        result = get_tags(vault, key)
        if result.tags:
            for tag in result.tags:
                click.echo(tag)
        else:
            click.echo(f"No tags for '{key}'.")
    except (TaggerError, VaultError) as exc:
        raise click.ClickException(str(exc)) from exc


@tag_group.command("find")
@click.argument("vault_path")
@click.argument("password")
@click.argument("tag")
def run_find(vault_path: str, password: str, tag: str) -> None:
    """Find all keys with TAG."""
    try:
        vault = Vault(vault_path, password)
        keys = list_by_tag(vault, tag)
        if keys:
            for key in keys:
                click.echo(key)
        else:
            click.echo(f"No keys found with tag '{tag}'.")
    except (TaggerError, VaultError) as exc:
        raise click.ClickException(str(exc)) from exc
