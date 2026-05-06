"""CLI commands for the template rendering feature."""
from __future__ import annotations

from pathlib import Path

import click

from envault.templater import TemplateError, render_file
from envault.vault import Vault


@click.group(name="template")
def template_group() -> None:
    """Render config templates using vault secrets."""


@template_group.command(name="render")
@click.argument("template", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
@click.option("--vault", "vault_path", required=True, type=click.Path(path_type=Path), help="Path to vault file.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite output if it exists.")
def run_render(
    template: Path,
    output: Path,
    vault_path: Path,
    password: str,
    overwrite: bool,
) -> None:
    """Render TEMPLATE into OUTPUT, substituting {{VAR}} placeholders from the vault."""
    try:
        vault = Vault(vault_path)
        result = render_file(template, output, vault, password, overwrite=overwrite)
    except TemplateError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.resolved:
        click.echo(f"Resolved {len(result.resolved)} secret(s): {', '.join(result.resolved)}")
    if result.missing:
        click.echo(
            click.style(
                f"Warning: {len(result.missing)} placeholder(s) not found in vault: {', '.join(result.missing)}",
                fg="yellow",
            )
        )
    click.echo(f"Rendered template written to {output}")
