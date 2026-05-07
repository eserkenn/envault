"""Profile-based secret grouping for envault."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class ProfileError(Exception):
    """Raised when a profile operation fails."""


@dataclass
class Profile:
    name: str
    keys: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ProfileResult:
    profile: str
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)


def _profile_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".profiles.json")


def _load_profiles(vault_path: Path) -> Dict[str, Profile]:
    path = _profile_path(vault_path)
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return {
        name: Profile(name=name, keys=entry["keys"], description=entry.get("description", ""))
        for name, entry in data.items()
    }


def _save_profiles(vault_path: Path, profiles: Dict[str, Profile]) -> None:
    path = _profile_path(vault_path)
    data = {
        name: {"keys": p.keys, "description": p.description}
        for name, p in profiles.items()
    }
    path.write_text(json.dumps(data, indent=2))


def create_profile(vault_path: Path, name: str, description: str = "") -> Profile:
    profiles = _load_profiles(vault_path)
    if name in profiles:
        raise ProfileError(f"Profile '{name}' already exists.")
    profile = Profile(name=name, description=description)
    profiles[name] = profile
    _save_profiles(vault_path, profiles)
    return profile


def assign_keys(vault_path: Path, profile_name: str, keys: List[str], vault_keys: List[str]) -> ProfileResult:
    profiles = _load_profiles(vault_path)
    if profile_name not in profiles:
        raise ProfileError(f"Profile '{profile_name}' does not exist.")
    profile = profiles[profile_name]
    missing = [k for k in keys if k not in vault_keys]
    valid = [k for k in keys if k in vault_keys]
    added = [k for k in valid if k not in profile.keys]
    profile.keys = list(dict.fromkeys(profile.keys + added))
    _save_profiles(vault_path, profiles)
    return ProfileResult(profile=profile_name, added=added, missing=missing)


def remove_profile(vault_path: Path, name: str) -> None:
    profiles = _load_profiles(vault_path)
    if name not in profiles:
        raise ProfileError(f"Profile '{name}' does not exist.")
    del profiles[name]
    _save_profiles(vault_path, profiles)


def list_profiles(vault_path: Path) -> List[Profile]:
    return list(_load_profiles(vault_path).values())


def get_profile(vault_path: Path, name: str) -> Optional[Profile]:
    return _load_profiles(vault_path).get(name)
