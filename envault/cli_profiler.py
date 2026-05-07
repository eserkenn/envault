"""CLI commands for profile management in envault."""

import click
from pathlib import Path

from envault.profiler import (
    ProfileError,
    create_profile,
    assign_keys,
    remove_profile,
    list_profiles,
    get_profile,
)
from envault.vault import Vault


@click.group(name="profile")
def profile_group() -> None:
    """Manage secret profiles (logical groupings of keys)."""


@profile_group.command("create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Optional profile description.")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def create_cmd(name: str, description: str, vault_path: str) -> None:
    """Create a new profile."""
    try:
        profile = create_profile(Path(vault_path), name, description)
        click.echo(f"Profile '{profile.name}' created.")
    except ProfileError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@profile_group.command("assign")
@click.argument("profile_name")
@click.argument("keys", nargs=-1, required=True)
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
@click.option("--password", prompt=True, hide_input=True)
def assign_cmd(profile_name: str, keys: tuple, vault_path: str, password: str) -> None:
    """Assign keys to a profile."""
    try:
        vault = Vault(Path(vault_path), password)
        vault_keys = vault.list_keys()
        result = assign_keys(Path(vault_path), profile_name, list(keys), vault_keys)
        if result.added:
            click.echo(f"Assigned: {', '.join(result.added)}.")
        if result.missing:
            click.echo(f"Not found in vault: {', '.join(result.missing)}.")
        if not result.added:
            click.echo("No new keys assigned.")
    except ProfileError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@profile_group.command("remove")
@click.argument("name")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def remove_cmd(name: str, vault_path: str) -> None:
    """Remove a profile."""
    try:
        remove_profile(Path(vault_path), name)
        click.echo(f"Profile '{name}' removed.")
    except ProfileError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@profile_group.command("list")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def list_cmd(vault_path: str) -> None:
    """List all profiles."""
    profiles = list_profiles(Path(vault_path))
    if not profiles:
        click.echo("No profiles defined.")
        return
    for p in profiles:
        desc = f" — {p.description}" if p.description else ""
        click.echo(f"  {p.name}{desc} ({len(p.keys)} keys)")


@profile_group.command("show")
@click.argument("name")
@click.option("--vault", "vault_path", default="vault.enc", show_default=True)
def show_cmd(name: str, vault_path: str) -> None:
    """Show keys in a profile."""
    profile = get_profile(Path(vault_path), name)
    if profile is None:
        click.echo(f"Error: Profile '{name}' not found.", err=True)
        raise SystemExit(1)
    if not profile.keys:
        click.echo(f"Profile '{name}' has no keys assigned.")
    else:
        for key in profile.keys:
            click.echo(f"  {key}")
