"""Deployment target management for envault."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

TARGETS_FILE = Path(".envault-targets.json")


class TargetError(Exception):
    """Raised when a target operation fails."""


class TargetManager:
    """Manages named deployment targets (e.g. staging, production)."""

    def __init__(self, targets_path: Path = TARGETS_FILE) -> None:
        self._path = targets_path
        self._targets: Dict[str, dict] = self._load()

    def _load(self) -> Dict[str, dict]:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text())
        except json.JSONDecodeError as exc:
            raise TargetError(f"Corrupted targets file: {exc}") from exc

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._targets, indent=2))

    def add(self, name: str, vault_path: str, description: str = "") -> None:
        """Register a new deployment target."""
        if name in self._targets:
            raise TargetError(f"Target '{name}' already exists.")
        self._targets[name] = {"vault_path": vault_path, "description": description}
        self._save()

    def remove(self, name: str) -> None:
        """Remove an existing deployment target."""
        if name not in self._targets:
            raise TargetError(f"Target '{name}' not found.")
        del self._targets[name]
        self._save()

    def get(self, name: str) -> dict:
        """Retrieve metadata for a named target."""
        if name not in self._targets:
            raise TargetError(f"Target '{name}' not found.")
        return self._targets[name]

    def list_targets(self) -> List[str]:
        """Return all registered target names."""
        return list(self._targets.keys())

    def vault_path(self, name: str) -> Path:
        """Return the vault file path associated with a target."""
        return Path(self.get(name)["vault_path"])
