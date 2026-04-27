"""CLI commands for exporting vault secrets."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from envault.vault import Vault
from envault.exporter import export_secrets, ExportError, SUPPORTED_FORMATS


@click.group(name="export")
def export_group() -> None:
    """Export secrets from the vault."""


@export_group.command(name="run")
@click.option(
    "--vault-file",
    default=".envault",
    show_default=True,
    help="Path to the vault file.",
    type=click.Path(),
)
@click.option(
    "--target",
    default=None,
    help="Filter secrets by deployment target name.",
)
@click.option(
    "--format",
    "fmt",
    default="dotenv",
    show_default=True,
    type=click.Choice(SUPPORTED_FORMATS),
    help="Output format.",
)
@click.option(
    "--output",
    default=None,
    help="Write output to this file instead of stdout.",
    type=click.Path(),
)
@click.password_option(
    "--password",
    prompt="Vault password",
    confirmation_prompt=False,
    help="Master password to decrypt the vault.",
)
def run_export(
    vault_file: str,
    target: Optional[str],
    fmt: str,
    output: Optional[str],
    password: str,
) -> None:
    """Decrypt and export secrets to stdout or a file."""
    vault = Vault(Path(vault_file))
    output_path = Path(output) if output else None

    try:
        content = export_secrets(vault, password, target=target, fmt=fmt, output_path=output_path)
    except ExportError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if output_path is None:
        click.echo(content, nl=False)
    else:
        click.echo(f"Secrets exported to {output_path}")
