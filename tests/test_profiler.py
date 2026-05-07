"""Tests for envault.profiler."""

import json
import pytest
from pathlib import Path

from envault.profiler import (
    ProfileError,
    create_profile,
    assign_keys,
    remove_profile,
    list_profiles,
    get_profile,
    _profile_path,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "vault.enc"
    path.write_text("{}")  # minimal placeholder
    return path


class TestCreateProfile:
    def test_creates_profile_file(self, vault_file: Path) -> None:
        create_profile(vault_file, "production")
        assert _profile_path(vault_file).exists()

    def test_profile_is_persisted(self, vault_file: Path) -> None:
        create_profile(vault_file, "staging", description="Staging env")
        profiles = list_profiles(vault_file)
        assert any(p.name == "staging" for p in profiles)

    def test_description_is_stored(self, vault_file: Path) -> None:
        create_profile(vault_file, "dev", description="Local dev")
        profile = get_profile(vault_file, "dev")
        assert profile is not None
        assert profile.description == "Local dev"

    def test_raises_on_duplicate_name(self, vault_file: Path) -> None:
        create_profile(vault_file, "prod")
        with pytest.raises(ProfileError, match="already exists"):
            create_profile(vault_file, "prod")


class TestAssignKeys:
    def test_adds_valid_keys(self, vault_file: Path) -> None:
        create_profile(vault_file, "prod")
        result = assign_keys(vault_file, "prod", ["DB_URL", "API_KEY"], ["DB_URL", "API_KEY", "SECRET"])
        assert "DB_URL" in result.added
        assert "API_KEY" in result.added

    def test_missing_keys_reported(self, vault_file: Path) -> None:
        create_profile(vault_file, "prod")
        result = assign_keys(vault_file, "prod", ["GHOST_KEY"], ["DB_URL"])
        assert "GHOST_KEY" in result.missing
        assert "GHOST_KEY" not in result.added

    def test_no_duplicates_in_profile(self, vault_file: Path) -> None:
        create_profile(vault_file, "prod")
        assign_keys(vault_file, "prod", ["DB_URL"], ["DB_URL"])
        assign_keys(vault_file, "prod", ["DB_URL"], ["DB_URL"])
        profile = get_profile(vault_file, "prod")
        assert profile is not None
        assert profile.keys.count("DB_URL") == 1

    def test_raises_for_unknown_profile(self, vault_file: Path) -> None:
        with pytest.raises(ProfileError, match="does not exist"):
            assign_keys(vault_file, "ghost", ["KEY"], ["KEY"])


class TestRemoveProfile:
    def test_removes_existing_profile(self, vault_file: Path) -> None:
        create_profile(vault_file, "temp")
        remove_profile(vault_file, "temp")
        assert get_profile(vault_file, "temp") is None

    def test_raises_for_unknown_profile(self, vault_file: Path) -> None:
        with pytest.raises(ProfileError, match="does not exist"):
            remove_profile(vault_file, "nonexistent")


class TestListProfiles:
    def test_empty_when_no_file(self, vault_file: Path) -> None:
        assert list_profiles(vault_file) == []

    def test_returns_all_profiles(self, vault_file: Path) -> None:
        create_profile(vault_file, "a")
        create_profile(vault_file, "b")
        names = [p.name for p in list_profiles(vault_file)]
        assert "a" in names
        assert "b" in names
