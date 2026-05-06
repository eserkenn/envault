"""Template rendering for environment variable injection into config files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from envault.vault import Vault


class TemplateError(Exception):
    """Raised when template rendering fails."""


@dataclass
class RenderResult:
    output: str
    resolved: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    @property
    def has_missing(self) -> bool:
        return bool(self.missing)


_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Z0-9_]+)\s*\}\}")


def render_template(template: str, vault: "Vault", password: str) -> RenderResult:
    """Replace {{VAR}} placeholders in *template* with secrets from *vault*."""
    resolved: list[str] = []
    missing: list[str] = []

    def _replace(match: re.Match) -> str:
        key = match.group(1)
        try:
            value = vault.get(key, password)
            resolved.append(key)
            return value
        except Exception:  # noqa: BLE001
            missing.append(key)
            return match.group(0)

    output = _PLACEHOLDER_RE.sub(_replace, template)
    return RenderResult(output=output, resolved=resolved, missing=missing)


def render_file(
    template_path: Path,
    output_path: Path,
    vault: "Vault",
    password: str,
    *,
    overwrite: bool = False,
) -> RenderResult:
    """Read *template_path*, render placeholders, and write to *output_path*."""
    if not template_path.exists():
        raise TemplateError(f"Template file not found: {template_path}")
    if output_path.exists() and not overwrite:
        raise TemplateError(
            f"Output file already exists: {output_path}. Use overwrite=True to replace."
        )

    template = template_path.read_text(encoding="utf-8")
    result = render_template(template, vault, password)
    output_path.write_text(result.output, encoding="utf-8")
    return result
