"""Case-registry records kept separate from framework semantics."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from ..domain import FrameworkError


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    title: str
    analysis: dict[str, str]
    representation: dict[str, str]
    requirements: dict[str, str]
    interface: dict[str, Any]
    target_bindings: dict[str, str]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "CaseSpec":
        try:
            return cls(
                case_id=str(raw["id"]),
                title=str(raw["title"]),
                analysis=dict(raw["analysis"]),
                representation=dict(raw["representation"]),
                requirements=dict(raw["requirements"]),
                interface=deepcopy(raw.get("interface", {})),
                target_bindings=dict(raw["target_bindings"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise FrameworkError(f"Invalid case record: {raw!r}") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.case_id,
            "title": self.title,
            "analysis": deepcopy(self.analysis),
            "representation": deepcopy(self.representation),
            "requirements": deepcopy(self.requirements),
            "interface": deepcopy(self.interface),
            "target_bindings": deepcopy(self.target_bindings),
        }
