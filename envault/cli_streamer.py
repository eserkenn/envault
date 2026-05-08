"""CLI commands for streaming vault secrets."""

from __future__ import annotations

import click

from envault.streamer import StreamError, _render_record, stream_vault
from envault.vault import Vault, VaultError


@click.group("stream")
def stream_group() -> None:
    """Stream decrypted secrets to stdout."""


@stream_group.command("run")
@click.argument("vault_path", type=click.Path(exists=True))
@click.option("--password", "-p", prompt=True, hide_input=True, help="Vault password.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["plain", "dotenv", "json"]),
    default="plain",
    show_default=True,
    help="Output format for each record.",
)
@click.option("--prefix", default=None, help="Only stream keys with this prefix.")
@click.option(
    "--key",
    "keys",
    multiple=True,
    help="Explicit key(s) to stream (repeatable).",
)
@click.option(
    "--progress",
    is_flag=True,
    default=False,
    help="Print progress indicator to stderr.",
)
def run_stream(
    vault_path: str,
    password: str,
    fmt: str,
    prefix: str | None,
    keys: tuple[str, ...],
    progress: bool,
) -> None:
    """Stream secrets from VAULT_PATH to stdout."""
    try:
        vault = Vault(vault_path)
    except VaultError as exc:
        raise click.ClickException(str(exc)) from exc

    explicit_keys = list(keys) if keys else None

    try:
        for record in stream_vault(
            vault, password, prefix=prefix, keys=explicit_keys
        ):
            if progress:
                click.echo(
                    f"[{record.index}/{record.total}] {record.key}", err=True
                )
            click.echo(_render_record(record, fmt))
    except StreamError as exc:
        raise click.ClickException(str(exc)) from exc

    if progress:
        click.echo("Stream complete.", err=True)
