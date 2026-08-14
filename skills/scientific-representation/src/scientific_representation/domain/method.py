"""Value type for the portable module-coordination record."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .errors import FrameworkError


@dataclass(frozen=True)
class MethodSpec:
    """Immutable coordination references between Agent-owned modules."""

    method_id: str
    purpose: str
    principles: str
    pipeline: str
    handoff: dict[str, str]
    entry_modes: tuple[dict[str, Any], ...]
    realization_branch: dict[str, Any]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "MethodSpec":
        try:
            if raw["schema_version"] != 3:
                raise ValueError("unsupported method schema")
            handoff = deepcopy(raw["handoff"])
            if not isinstance(handoff, dict) or any(
                not handoff.get(field)
                for field in ("artifact", "producer", "consumer")
            ):
                raise ValueError("invalid phase handoff")
            entry_modes = tuple(deepcopy(raw["entry_modes"]))
            if not all(
                isinstance(mode, dict)
                and mode.get("id")
                and mode.get("start_module")
                and mode.get("input")
                for mode in entry_modes
            ):
                raise ValueError("invalid entry modes")
            realization_branch = deepcopy(raw["realization_branch"])
            if (
                not isinstance(realization_branch, dict)
                or not realization_branch.get("module")
                or not realization_branch.get("resume_artifact")
                or not realization_branch.get("default_target")
                or not realization_branch.get("output")
            ):
                raise ValueError("invalid realization branch")
            return cls(
                method_id=str(raw["method_id"]),
                purpose=str(raw["purpose"]),
                principles=str(raw["principles"]),
                pipeline=str(raw["pipeline"]),
                handoff=handoff,
                entry_modes=entry_modes,
                realization_branch=realization_branch,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise FrameworkError(f"Invalid method coordination record: {exc}") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.method_id,
            "purpose": self.purpose,
            "principles": self.principles,
            "pipeline": self.pipeline,
            "handoff": deepcopy(self.handoff),
            "entry_modes": deepcopy(list(self.entry_modes)),
            "realization_branch": deepcopy(self.realization_branch),
        }
