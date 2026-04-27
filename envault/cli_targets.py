"""CLI commands for managing deployment targets in envault."""

from __future__ import annotations

import click
from envault.targets import TargetManager, TargetError


@click.group("target")
def target_group() -> None:
    """Manage deployment targets."""


@target_group.command("add")
@click.argument("name")
@click.argument("vault_path")
@click.option("-d", "--description", default="", help="Human-readable description.")
def add_target(name: str, vault_path: str, description: str) -> None:
    """Register a new deployment target NAME with VAULT_PATH."""
    try:
        manager = TargetManager()
        manager.add(name, vault_path, description=description)
        click.echo(f"Target '{name}' added (vault: {vault_path}).")
    except TargetError as exc:
        raise click.ClickException(str(exc)) from exc


@target_group.command("remove")
@click.argument("name")
def remove_target(name: str) -> None:
    """Remove a registered deployment target by NAME."""
    try:
        manager = TargetManager()
        manager.remove(name)
        click.echo(f"Target '{name}' removed.")
    except TargetError as exc:
        raise click.ClickException(str(exc)) from exc


@target_group.command("list")
def list_targets() -> None:
    """List all registered deployment targets."""
    manager = TargetManager()
    names = manager.list_targets()
    if not names:
        click.echo("No targets registered.")
        return
    for name in names:
        info = manager.get(name)
        desc = f"  — {info['description']}" if info.get("description") else ""
        click.echo(f"  {name}: {info['vault_path']}{desc}")


@target_group.command("info")
@click.argument("name")
def target_info(name: str) -> None:
    """Show details for a specific deployment target."""
    try:
        manager = TargetManager()
        info = manager.get(name)
        click.echo(f"Name:        {name}")
        click.echo(f"Vault path:  {info['vault_path']}")
        click.echo(f"Description: {info.get('description') or '(none)'}")
    except TargetError as exc:
        raise click.ClickException(str(exc)) from exc
