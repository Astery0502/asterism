"""Read-only view of the target-neutral pipeline architecture."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..domain import FrameworkError


EXPECTED_STAGE_ORDER = (
    "analysis",
    "representation",
    "target_translation",
    "application",
    "scientific_review",
)


@dataclass(frozen=True)
class StageBoundary:
    """One explicit change of authority in the representation pipeline."""

    stage_id: str
    module_id: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    authority: str


@dataclass(frozen=True)
class FrameworkArchitecture:
    """Validated architectural contract shared by runtimes and consumers."""

    root: Path
    contract_id: str
    stages: tuple[StageBoundary, ...]
    dependency_rules: tuple[str, ...]
    case_workspace: dict[str, tuple[str, ...]]

    @classmethod
    def load(cls, root: str | Path) -> "FrameworkArchitecture":
        project_root = Path(root).resolve()
        path = project_root / "framework" / "pipeline.json"
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise FrameworkError(f"Pipeline contract not found: {path}") from exc
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise FrameworkError(f"Invalid pipeline contract: {exc}") from exc
        if not isinstance(raw, dict) or raw.get("schema_version") != 3:
            raise FrameworkError("Pipeline contract must use schema version 2")

        try:
            stages = tuple(
                StageBoundary(
                    stage_id=str(item["id"]),
                    module_id=str(item["module"]),
                    inputs=tuple(str(value) for value in item["inputs"]),
                    outputs=tuple(str(value) for value in item["outputs"]),
                    authority=str(item["authority"]),
                )
                for item in raw["stages"]
            )
            workspace = {
                str(stage): tuple(str(path) for path in paths)
                for stage, paths in raw["case_workspace"].items()
            }
            architecture = cls(
                root=project_root,
                contract_id=str(raw["contract_id"]),
                stages=stages,
                dependency_rules=tuple(str(rule) for rule in raw["dependency_rules"]),
                case_workspace=workspace,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise FrameworkError(f"Incomplete pipeline contract: {exc}") from exc
        architecture.validate()
        return architecture

    def validate(self) -> None:
        stage_ids = tuple(stage.stage_id for stage in self.stages)
        if stage_ids != EXPECTED_STAGE_ORDER:
            raise FrameworkError(
                "Pipeline stages must be ordered as " + ", ".join(EXPECTED_STAGE_ORDER)
            )
        if set(self.case_workspace) != set(EXPECTED_STAGE_ORDER) | {"input"}:
            raise FrameworkError("Case workspace does not cover every pipeline boundary")
        if not self.dependency_rules:
            raise FrameworkError("Pipeline contract declares no dependency rules")
        for stage in self.stages:
            if (
                not stage.module_id.strip()
                or not stage.inputs
                or not stage.outputs
                or not stage.authority.strip()
            ):
                raise FrameworkError(f"Stage boundary is incomplete: {stage.stage_id}")
        for paths in self.case_workspace.values():
            for value in paths:
                path = Path(value.replace("<target>", "target"))
                if path.is_absolute() or ".." in path.parts:
                    raise FrameworkError(f"Unsafe case-workspace path: {value}")

    def stage(self, stage_id: str) -> StageBoundary:
        for stage in self.stages:
            if stage.stage_id == stage_id:
                return stage
        raise FrameworkError(f"Unknown pipeline stage: {stage_id}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "stages": [
                {
                    "id": stage.stage_id,
                    "module": stage.module_id,
                    "inputs": list(stage.inputs),
                    "outputs": list(stage.outputs),
                    "authority": stage.authority,
                }
                for stage in self.stages
            ],
            "dependency_rules": list(self.dependency_rules),
            "case_workspace": deepcopy(
                {stage: list(paths) for stage, paths in self.case_workspace.items()}
            ),
        }
