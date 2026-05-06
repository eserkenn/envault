"""CLI commands for managing secret rotation schedules."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import click

from envault.scheduler import (
    SchedulerError,
    due_keys,
    load_schedule,
    remove_schedule,
    set_schedule,
)


@click.group(name="schedule")
def schedule_group() -> None:
    """Manage secret rotation schedules."""


@schedule_group.command("set")
@click.argument("vault_path", type=click.Path())
@click.argument("key")
@click.option("--every", "rotate_every_days", default=90, show_default=True,
              help="Rotation interval in days.")
@click.option("--last-rotated", default=None,
              help="ISO 8601 date of last rotation (default: now).")
def set_cmd(vault_path: str, key: str, rotate_every_days: int,
            last_rotated: str | None) -> None:
    """Set a rotation schedule for KEY in VAULT_PATH."""
    try:
        entry = set_schedule(Path(vault_path), key, rotate_every_days, last_rotated)
        click.echo(
            f"Scheduled '{key}' to rotate every {entry.rotate_every_days} day(s). "
            f"Next rotation: {entry.next_rotation().date()}"
        )
    except SchedulerError as exc:
        raise click.ClickException(str(exc)) from exc


@schedule_group.command("remove")
@click.argument("vault_path", type=click.Path())
@click.argument("key")
def remove_cmd(vault_path: str, key: str) -> None:
    """Remove the rotation schedule for KEY."""
    removed = remove_schedule(Path(vault_path), key)
    if removed:
        click.echo(f"Schedule removed for '{key}'.")
    else:
        click.echo(f"No schedule found for '{key}'.")


@schedule_group.command("list")
@click.argument("vault_path", type=click.Path())
def list_cmd(vault_path: str) -> None:
    """List all scheduled keys and their next rotation dates."""
    entries = load_schedule(Path(vault_path))
    if not entries:
        click.echo("No schedules configured.")
        return
    for entry in entries:
        days = entry.days_until_due()
        status = click.style("DUE", fg="red") if entry.is_due() else f"in {days}d"
        click.echo(f"  {entry.key:<30} every {entry.rotate_every_days}d  [{status}]")


@schedule_group.command("due")
@click.argument("vault_path", type=click.Path())
def due_cmd(vault_path: str) -> None:
    """List keys whose rotation is currently due."""
    overdue = due_keys(Path(vault_path))
    if not overdue:
        click.echo("No keys are due for rotation.")
        return
    click.echo(f"{len(overdue)} key(s) due for rotation:")
    for entry in overdue:
        click.echo(f"  {click.style(entry.key, fg='red')}  (last rotated {entry.last_rotated[:10]})")
