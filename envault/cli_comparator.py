"""CLI commands for comparing two vault files."""

from __future__ import annotations

from pathlib import Path

import click

from envault.comparator import CompareError, compare_vaults


@click.group("compare")
def compare_group() -> None:
    """Compare two vault files."""


@compare_group.command("run")
@click.argument("left", type=click.Path(exists=True, path_type=Path))
@click.argument("right", type=click.Path(exists=True, path_type=Path))
@click.option("--left-password", prompt=True, hide_input=True, envvar="ENVAULT_LEFT_PASSWORD")
@click.option("--right-password", prompt=True, hide_input=True, envvar="ENVAULT_RIGHT_PASSWORD")
@click.option("--show-same", is_flag=True, default=False, help="Also list identical keys.")
def run_compare(
    left: Path,
    right: Path,
    left_password: str,
    right_password: str,
    show_same: bool,
) -> None:
    """Compare LEFT vault against RIGHT vault."""
    try:
        result = compare_vaults(left, left_password, right, right_password)
    except CompareError as exc:
        raise click.ClickException(str(exc))

    if result.is_identical:
        click.echo("Vaults are identical.")
        return

    click.echo(f"Similarity: {result.similarity_pct}%")

    for key in result.only_in_left:
        click.echo(f"  < {key}  (only in left)")
    for key in result.only_in_right:
        click.echo(f"  > {key}  (only in right)")
    for key in result.in_both_different:
        click.echo(f"  ~ {key}  (value differs)")
    if show_same:
        for key in result.in_both_same:
            click.echo(f"  = {key}  (identical)")
