import click
from envault.vault import Vault, VaultError
from envault.linter import lint_vault, LintError


@click.group(name="lint")
def lint_group():
    """Lint vault secrets for common issues."""


@lint_group.command(name="run")
@click.argument("vault_path")
@click.password_option(
    "--password",
    prompt="Vault password",
    confirmation_prompt=False,
    help="Password to decrypt the vault.",
)
@click.option(
    "--warn-only",
    is_flag=True,
    default=False,
    help="Exit 0 even if errors are found.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def run_lint(vault_path, password, warn_only, output_format):
    """Run lint checks against a vault file."""
    import json as _json

    try:
        vault = Vault(vault_path, password)
    except VaultError as exc:
        raise click.ClickException(str(exc))

    try:
        result = lint_vault(vault)
    except LintError as exc:
        raise click.ClickException(str(exc))

    if output_format == "json":
        issues = [
            {"key": i.key, "severity": i.severity, "message": i.message}
            for i in result.issues
        ]
        click.echo(_json.dumps({"issues": issues, "error_count": result.error_count, "warning_count": result.warning_count}, indent=2))
    else:
        if not result.issues:
            click.echo("No issues found.")
        else:
            for issue in result.issues:
                severity_label = click.style(
                    issue.severity.upper(),
                    fg="red" if issue.severity == "error" else "yellow",
                    bold=True,
                )
                click.echo(f"[{severity_label}] {issue.key}: {issue.message}")
            click.echo(
                f"\n{result.error_count} error(s), {result.warning_count} warning(s)."
            )

    if result.has_errors() and not warn_only:
        raise SystemExit(1)
