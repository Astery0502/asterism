"""Target-independent representation semantics."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .errors import FrameworkError


@dataclass(frozen=True)
class RepresentationIntent:
    """Case-level semantic index from theory to representation requirements."""

    intent_id: str
    requirements_id: str
    theoretical_account_id: str
    presentation_question: str
    pivotal_hypotheses: tuple[dict[str, Any], ...]
    method_id: str = ""
    case_id: str = ""

    def __post_init__(self) -> None:
        if not self.pivotal_hypotheses:
            raise FrameworkError("Representation intent has no pivotal hypotheses")
        for hypothesis in self.pivotal_hypotheses:
            if not isinstance(hypothesis, dict):
                raise FrameworkError("Pivotal hypothesis must be an object")
            hypothesis_id = hypothesis.get("id")
            requirement_refs = hypothesis.get("requirement_refs")
            if not isinstance(hypothesis_id, str) or not hypothesis_id.strip():
                raise FrameworkError("Pivotal hypothesis has no ID")
            if not isinstance(requirement_refs, list) or not requirement_refs:
                raise FrameworkError("Pivotal hypothesis has no requirement references")
            if not all(
                isinstance(value, str) and value.strip()
                for value in requirement_refs
            ):
                raise FrameworkError(
                    "Pivotal hypothesis has invalid requirement references"
                )

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RepresentationIntent":
        try:
            if raw["schema_version"] != 2:
                raise ValueError("unsupported intent schema")
            hypotheses = tuple(deepcopy(raw["pivotal_hypotheses"]))
            return cls(
                intent_id=str(raw["intent_id"]),
                requirements_id=str(raw["requirements_id"]),
                theoretical_account_id=str(raw["theoretical_account_id"]),
                presentation_question=str(raw["presentation_question"]),
                pivotal_hypotheses=hypotheses,
                method_id=str(raw.get("method_id", "")),
                case_id=str(raw.get("case_id", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise FrameworkError(f"Invalid representation intent record: {exc}") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 2,
            "id": self.intent_id,
            "intent_id": self.intent_id,
            "requirements_id": self.requirements_id,
            "theoretical_account_id": self.theoretical_account_id,
            "presentation_question": self.presentation_question,
            "pivotal_hypotheses": deepcopy(list(self.pivotal_hypotheses)),
            **({"method_id": self.method_id} if self.method_id else {}),
            **({"case_id": self.case_id} if self.case_id else {}),
        }
