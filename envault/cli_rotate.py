"""CLI commands for key rotation."""

from __future__ import annotations

import click

from envault.rotator import RotationError, rotate_key


@click.group("rotate")
def rotate_group() -> None:
    """Rotate the master password for a vault."""


@rotate_group.command("run")
@click.argument("vault_path")
@click.option(
    "--old-password",
    prompt=True,
    hide_input=True,
    help="Current vault password.",
)
@click.option(
    "--new-password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="New vault password.",
)
def run_rotate(vault_path: str, old_password: str, new_password: str) -> None:
    """Re-encrypt all secrets in VAULT_PATH with a new password."""
    if old_password == new_password:
        raise click.UsageError("New password must differ from the old password.")

    try:
        rotated = rotate_key(vault_path, old_password, new_password)
    except RotationError as exc:
        raise click.ClickException(str(exc)) from exc

    if rotated:
        click.echo(f"Rotated {len(rotated)} key(s): {', '.join(rotated)}")
    else:
        click.echo("Vault is empty — nothing to rotate.")
