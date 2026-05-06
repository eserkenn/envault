"""CLI commands for validating vault secrets."""

from __future__ import annotations

import sys

import click

from envault.validator import ValidationSeverity, ValidatorError, validate_secrets
from envault.vault import Vault, VaultError


@click.group("validate")
def validate_group() -> None:
    """Validate environment variable keys and values."""


@validate_group.command("run")
@click.argument("vault_path", type=click.Path(exists=True))
@click.password_option("--password", prompt="Vault password", confirmation_prompt=False)
@click.option("--keys", "-k", multiple=True, help="Specific keys to validate (default: all).")
@click.option("--strict", is_flag=True, default=False, help="Exit non-zero on warnings too.")
def run_validate(vault_path: str, password: str, keys: tuple[str, ...], strict: bool) -> None:
    """Validate secrets in the vault."""
    try:
        vault = Vault(vault_path, password)
        result = validate_secrets(vault, keys or None)
    except (VaultError, ValidatorError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if not result.issues:
        click.echo("✔ All secrets passed validation.")
        return

    for issue in result.issues:
        icon = "✖" if issue.severity == ValidationSeverity.ERROR else "⚠"
        click.echo(f"{icon} [{issue.severity.value.upper()}] {issue.key}: {issue.message}")

    errors = result.has_errors()
    warnings = result.has_warnings()

    if errors or (strict and warnings):
        sys.exit(1)
