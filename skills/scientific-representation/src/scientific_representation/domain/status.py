"""Public status vocabulary for independently judged workflow dimensions."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import FrameworkError


@dataclass(frozen=True)
class WorkflowStatus:
    """Orthogonal lifecycle statuses; no field stands in for another."""

    application_execution: str = "not_performed"
    structural_validation: str = "not_evaluated"
    mechanical_conformance: str = "not_evaluated"
    target_requirement_coverage: str = "not_evaluated"
    scientific_review: str = "not_performed"

    def __post_init__(self) -> None:
        allowed = {
            "application_execution": {"not_performed", "completed", "failed"},
            "structural_validation": {"not_evaluated", "passed", "failed"},
            "mechanical_conformance": {"not_evaluated", "passed", "failed"},
            "target_requirement_coverage": {
                "not_evaluated",
                "covered",
                "conditional",
                "unmet",
            },
            "scientific_review": {
                "not_performed",
                "accepted",
                "revision_requested",
                "inconclusive",
            },
        }
        for field, values in allowed.items():
            value = getattr(self, field)
            if value not in values:
                raise FrameworkError(f"Unknown {field}: {value}")

    def to_dict(self) -> dict[str, str]:
        return {
            "application_execution": self.application_execution,
            "structural_validation": self.structural_validation,
            "mechanical_conformance": self.mechanical_conformance,
            "target_requirement_coverage": self.target_requirement_coverage,
            "scientific_review": self.scientific_review,
        }
