"""Small shared primitives for contract-driven target validation."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

from ..domain import FrameworkError


def contained_path(root: Path, relative: Any, label: str) -> Path:
    """Resolve a relative record path without allowing it to leave ``root``."""

    if not isinstance(relative, str) or not relative:
        raise FrameworkError(f"{label} path must be a non-empty relative string")
    candidate = Path(relative)
    if candidate.is_absolute():
        raise FrameworkError(f"{label} path must be relative: {relative}")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise FrameworkError(f"{label} path leaves its root: {relative}") from exc
    return resolved


def read_json_object(path: Path, label: str) -> dict[str, Any]:
    """Read a JSON object and report failures in contract vocabulary."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FrameworkError(f"Invalid {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise FrameworkError(f"{label} must contain an object")
    return value


def load_validation_extension(
    contract: dict[str, Any], function_name: str
) -> ModuleType:
    """Load the target-owned validator declared by a target contract."""

    module_name = contract.get("validation_extension")
    if not isinstance(module_name, str) or not module_name:
        raise FrameworkError("Target contract declares no validation extension")
    try:
        module = importlib.import_module(module_name)
    except (ImportError, ValueError) as exc:
        raise FrameworkError(
            f"Target validation extension cannot be loaded: {module_name}: {exc}"
        ) from exc
    if not callable(getattr(module, function_name, None)):
        raise FrameworkError(
            f"Target validation extension lacks {function_name}: {module_name}"
        )
    return module
