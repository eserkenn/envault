"""CLI commands for diffing secrets between two vault files."""

from __future__ import annotations

import click

from envault.differ import DiffError, diff_vaults
from envault.vault import Vault


@click.group(name="diff")
def diff_group() -> None:
    """Compare secrets between two vault files."""


@diff_group.command(name="run")
@click.argument("left_vault_path", type=click.Path(exists=True))
@click.argument("right_vault_path", type=click.Path(exists=True))
@click.option("--left-password", prompt=True, hide_input=True, help="Password for the left vault.")
@click.option("--right-password", prompt=True, hide_input=True, help="Password for the right vault.")
@click.option("--show-unchanged", is_flag=True, default=False, help="Also display unchanged keys.")
def run_diff(
    left_vault_path: str,
    right_vault_path: str,
    left_password: str,
    right_password: str,
    show_unchanged: bool,
) -> None:
    """Diff secrets stored in LEFT_VAULT_PATH against RIGHT_VAULT_PATH."""
    left_vault = Vault(left_vault_path)
    right_vault = Vault(right_vault_path)

    try:
        entries = diff_vaults(left_vault, left_password, right_vault, right_password)
    except DiffError as exc:
        raise click.ClickException(str(exc)) from exc

    if not entries:
        click.echo("Both vaults are empty.")
        return

    status_symbols = {
        "added": click.style("+", fg="green"),
        "removed": click.style("-", fg="red"),
        "changed": click.style("~", fg="yellow"),
        "unchanged": click.style(" ", fg="white"),
    }

    displayed = 0
    for entry in entries:
        if entry.status == "unchanged" and not show_unchanged:
            continue
        symbol = status_symbols[entry.status]
        click.echo(f"  {symbol} {entry.key}")
        displayed += 1

    if displayed == 0:
        click.echo("No differences found.")
    else:
        summary = {"added": 0, "removed": 0, "changed": 0}
        for e in entries:
            if e.status in summary:
                summary[e.status] += 1
        click.echo(
            f"\nSummary: "
            f"{click.style(str(summary['added']) + ' added', fg='green')}, "
            f"{click.style(str(summary['removed']) + ' removed', fg='red')}, "
            f"{click.style(str(summary['changed']) + ' changed', fg='yellow')}"
        )
