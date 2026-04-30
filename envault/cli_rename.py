"""CLI commands for renaming vault keys."""

from __future__ import annotations

import click

from envault.renamer import RenameError, bulk_rename, rename_key
from envault.vault import Vault, VaultError


@click.group(name="rename")
def rename_group() -> None:
    """Rename keys stored in a vault."""


@rename_group.command(name="key")
@click.argument("vault_path")
@click.argument("old_key")
@click.argument("new_key")
@click.option("--password", prompt=True, hide_input=True, help="Vault master password.")
@click.option(
    "--overwrite", is_flag=True, default=False, help="Replace new_key if it exists."
)
def run_rename(vault_path: str, old_key: str, new_key: str, password: str, overwrite: bool) -> None:
    """Rename OLD_KEY to NEW_KEY inside VAULT_PATH."""
    try:
        vault = Vault(vault_path)
        result = rename_key(vault, password, old_key, new_key, overwrite=overwrite)
    except (RenameError, VaultError) as exc:
        raise click.ClickException(str(exc)) from exc

    if result.success:
        click.echo(f"Renamed '{result.old_key}' → '{result.new_key}'")


@rename_group.command(name="bulk")
@click.argument("vault_path")
@click.option(
    "--map",
    "pairs",
    multiple=True,
    type=(str, str),
    metavar="OLD NEW",
    required=True,
    help="OLD_KEY NEW_KEY pair (repeatable).",
)
@click.option("--password", prompt=True, hide_input=True, help="Vault master password.")
@click.option(
    "--overwrite", is_flag=True, default=False, help="Replace new keys if they exist."
)
def run_bulk_rename(
    vault_path: str, pairs: list[tuple[str, str]], password: str, overwrite: bool
) -> None:
    """Rename multiple keys at once inside VAULT_PATH."""
    try:
        vault = Vault(vault_path)
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc

    results = bulk_rename(vault, password, list(pairs), overwrite=overwrite)

    ok = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    for r in ok:
        click.echo(f"  ✔  '{r.old_key}' → '{r.new_key}'")
    for r in failed:
        click.echo(f"  ✘  '{r.old_key}' → '{r.new_key}': {r.message}", err=True)

    if failed:
        raise click.ClickException(f"{len(failed)} rename(s) failed.")
