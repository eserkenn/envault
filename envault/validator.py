"""Validation rules for environment variable keys and values."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ValidationIssue:
    key: str
    message: str
    severity: ValidationSeverity


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    def has_errors(self) -> bool:
        return any(i.severity == ValidationSeverity.ERROR for i in self.issues)

    def has_warnings(self) -> bool:
        return any(i.severity == ValidationSeverity.WARNING for i in self.issues)


class ValidatorError(Exception):
    pass


_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
_MAX_VALUE_LENGTH = 4096
_SENSITIVE_PREFIXES = ("SECRET", "PASSWORD", "TOKEN", "API_KEY", "PRIVATE")


def validate_secrets(vault, keys: Iterable[str] | None = None) -> ValidationResult:
    """Run all validation rules against the given vault keys."""
    result = ValidationResult()
    all_keys = list(vault.list_keys())
    targets = list(keys) if keys is not None else all_keys

    for key in targets:
        if key not in all_keys:
            raise ValidatorError(f"Key not found in vault: {key!r}")

        _check_key_format(key, result)
        value = vault.get(key)
        _check_value_length(key, value, result)
        _check_empty_value(key, value, result)
        _check_placeholder(key, value, result)

    return result


def _check_key_format(key: str, result: ValidationResult) -> None:
    if not _KEY_PATTERN.match(key):
        result.issues.append(ValidationIssue(
            key=key,
            message=f"Key {key!r} does not follow UPPER_SNAKE_CASE convention.",
            severity=ValidationSeverity.WARNING,
        ))


def _check_value_length(key: str, value: str, result: ValidationResult) -> None:
    if len(value) > _MAX_VALUE_LENGTH:
        result.issues.append(ValidationIssue(
            key=key,
            message=f"Value for {key!r} exceeds {_MAX_VALUE_LENGTH} characters.",
            severity=ValidationSeverity.ERROR,
        ))


def _check_empty_value(key: str, value: str, result: ValidationResult) -> None:
    if not value.strip():
        result.issues.append(ValidationIssue(
            key=key,
            message=f"Value for {key!r} is empty or blank.",
            severity=ValidationSeverity.WARNING,
        ))


def _check_placeholder(key: str, value: str, result: ValidationResult) -> None:
    placeholders = {"changeme", "todo", "fixme", "placeholder", "xxx", "tbd"}
    if value.strip().lower() in placeholders:
        result.issues.append(ValidationIssue(
            key=key,
            message=f"Value for {key!r} appears to be a placeholder ({value!r}).",
            severity=ValidationSeverity.ERROR,
        ))
