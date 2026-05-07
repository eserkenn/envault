"""CLI commands for vault summary reporting."""
from __future__ import annotations

import click

from envault.summarizer import SummaryError, summarize_vault
from envault.vault import Vault, VaultError


@click.group("summary")
def summary_group() -> None:
    """Display vault statistics and summaries."""


@summary_group.command("show")
@click.argument("vault_file", type=click.Path(exists=True))
@click.password_option("--password", "-p", prompt=True, confirmation_prompt=False)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def run_summary(vault_file: str, password: str, as_json: bool) -> None:
    """Show a statistical summary of a vault."""
    try:
        vault = Vault(vault_file)
        result = summarize_vault(vault, password)
    except (VaultError, SummaryError) as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        import json

        click.echo(
            json.dumps(
                {
                    "total_keys": result.total_keys,
                    "tagged_keys": result.tagged_keys,
                    "untagged_keys": result.untagged_keys,
                    "unique_tags": result.unique_tags,
                    "longest_key": result.longest_key,
                    "shortest_key": result.shortest_key,
                    "avg_value_length": result.avg_value_length,
                },
                indent=2,
            )
        )
        return

    if result.total_keys == 0:
        click.echo("Vault is empty — no secrets found.")
        return

    click.echo(f"Total keys       : {result.total_keys}")
    click.echo(f"Tagged keys      : {result.tagged_keys}")
    click.echo(f"Untagged keys    : {result.untagged_keys}")
    click.echo(f"Unique tags      : {len(result.unique_tags)}")
    if result.unique_tags:
        click.echo(f"  Tags           : {', '.join(result.unique_tags)}")
    click.echo(f"Longest key      : {result.longest_key}")
    click.echo(f"Shortest key     : {result.shortest_key}")
    click.echo(f"Avg value length : {result.avg_value_length} chars")
