"""Workspace persistence and atomic publication primitives."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from ..domain import FrameworkError


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def read_text(path: Path, label: str) -> str:
    try:
        value = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise FrameworkError(f"Could not read {label}: {exc}") from exc
    if not value.strip():
        raise FrameworkError(f"Persisted {label} is empty")
    return value


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FrameworkError(f"Could not read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise FrameworkError(f"Persisted {label} must be an object")
    return value


def create_staging_workspace(destination: Path) -> Path:
    return Path(
        tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent)
    )


def discard_staging_workspace(workspace: Path) -> None:
    shutil.rmtree(workspace, ignore_errors=True)


def publish_workspace(workspace: Path, destination: Path) -> None:
    """Rebase staging paths and atomically publish a completed workspace."""

    rebase_json_artifacts(workspace, workspace, destination)
    workspace.replace(destination)


def copy_workspace(source: Path, staging: Path) -> None:
    """Copy a published workspace into an empty staging directory."""

    if not source.is_dir():
        raise FrameworkError(f"Source workspace does not exist: {source}")
    shutil.copytree(source, staging, dirs_exist_ok=True)


def rebase_json_artifacts(workspace: Path, old_root: Path, new_root: Path) -> None:
    """Replace staging paths before atomic publication."""

    old = str(old_root)
    new = str(new_root)

    def rebase(value: Any) -> Any:
        if isinstance(value, str):
            return value.replace(old, new)
        if isinstance(value, list):
            return [rebase(item) for item in value]
        if isinstance(value, dict):
            return {key: rebase(item) for key, item in value.items()}
        return value

    for path in workspace.rglob("*.json"):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise FrameworkError(
                f"Could not rebase realization record {path}: {exc}"
            ) from exc
        path.write_text(
            json.dumps(rebase(raw), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
