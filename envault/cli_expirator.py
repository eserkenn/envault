"""CLI commands for secret expiration management."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import click

from envault.expirator import (
    ExpirationError,
    check_expirations,
    list_expirations,
    remove_expiration,
    set_expiration,
)


@click.group("expire")
def expire_group() -> None:
    """Manage secret expiration dates."""


@expire_group.command("set")
@click.argument("vault_path", type=click.Path(path_type=Path))
@click.argument("key")
@click.argument("expires_on")
def set_cmd(vault_path: Path, key: str, expires_on: str) -> None:
    """Set expiration date for KEY (format: YYYY-MM-DD)."""
    try:
        parsed = date.fromisoformat(expires_on)
        set_expiration(vault_path, key, parsed)
        click.echo(f"Expiration set: {key} expires on {parsed.isoformat()}")
    except ValueError:
        click.echo(f"Error: invalid date format '{expires_on}'. Use YYYY-MM-DD.", err=True)
        raise SystemExit(1)
    except ExpirationError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@expire_group.command("remove")
@click.argument("vault_path", type=click.Path(path_type=Path))
@click.argument("key")
def remove_cmd(vault_path: Path, key: str) -> None:
    """Remove expiration date for KEY."""
    removed = remove_expiration(vault_path, key)
    if removed:
        click.echo(f"Expiration removed for: {key}")
    else:
        click.echo(f"No expiration set for: {key}")


@expire_group.command("list")
@click.argument("vault_path", type=click.Path(path_type=Path))
def list_cmd(vault_path: Path) -> None:
    """List all expiration dates in the vault."""
    entries = list_expirations(Path(vault_path))
    if not entries:
        click.echo("No expiration dates configured.")
        return
    for entry in entries:
        status = "EXPIRED" if entry.is_expired else f"in {entry.days_remaining}d"
        click.echo(f"{entry.key:<30} {entry.expires_on.isoformat()}  ({status})")


@expire_group.command("check")
@click.argument("vault_path", type=click.Path(path_type=Path))
@click.option("--warn-days", default=7, show_default=True, help="Warn within N days.")
def check_cmd(vault_path: Path, warn_days: int) -> None:
    """Check for expired or soon-to-expire secrets."""
    entries = check_expirations(Path(vault_path), warn_within_days=warn_days)
    if not entries:
        click.echo("All secrets are within acceptable expiration windows.")
        return
    for entry in entries:
        label = "[EXPIRED]" if entry.is_expired else f"[expires in {entry.days_remaining}d]"
        click.echo(f"{label} {entry.key} — {entry.expires_on.isoformat()}")
    raise SystemExit(1)
