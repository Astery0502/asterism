"""Small target-agnostic value types used by the application core."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class PrototypeError(RuntimeError):
    """A user-facing application or adapter failure."""


DEFAULT_ANALYSIS_QUESTION = (
    "What mathematical or physical account follows from the supplied material, "
    "and where is it valid?"
)


DEFAULT_REALIZATION_BRANCH = {
    "resume_artifact": "RepresentationRequirementsPackage",
    "default_target": "scientific-html",
    "target_selection": (
        "Use Scientific HTML as the visualization route supplied by this "
        "framework snapshot."
    ),
    "inputs": [
        "TheoreticalAccount",
        "RepresentationIntent",
        "RepresentationRequirements",
        "RepresentationInterface",
        "TargetCapabilityCatalog",
        "RuntimeCapabilityObservation",
    ],
    "selection_basis": [
        "computation_timing",
        "interaction_semantics",
        "delivery_topology",
        "delivery_connectivity",
        "view_semantics",
        "numeric_contract",
    ],
    "output": "TargetNativeDecisionPlan",
    "meaning": (
        "The same accepted requirements package may resume through a newly "
        "selected TargetRealizer without repeating analysis or requirements formation."
    ),
}


@dataclass(frozen=True)
class RawRealizationRequest:
    """One user request whose internal stages retain explicit boundaries."""

    raw_input: Path
    direction: str
    target: str
    stop_after: str
    reference_case: str | None = None
    analysis_question: str | None = None
    presentation_question: str | None = None

    def __post_init__(self) -> None:
        if self.stop_after not in {"analysis", "requirements", "application"}:
            raise PrototypeError(f"Unknown realization stop stage: {self.stop_after}")
        analysis_question = (self.analysis_question or DEFAULT_ANALYSIS_QUESTION).strip()
        presentation_question = (self.presentation_question or self.direction).strip()
        if not analysis_question:
            raise PrototypeError("Analysis question is empty")
        if self.stop_after != "analysis" and not presentation_question:
            raise PrototypeError("Presentation question is empty")
        object.__setattr__(self, "analysis_question", analysis_question)
        object.__setattr__(self, "presentation_question", presentation_question)
        object.__setattr__(self, "direction", presentation_question)

    def analysis_input(self) -> "ScientificAnalysisRequest":
        return ScientificAnalysisRequest(
            raw_input=self.raw_input,
            analysis_question=str(self.analysis_question),
            reference_case=self.reference_case,
        )

    def representation_input(self) -> "RepresentationFormationRequest":
        return RepresentationFormationRequest(
            presentation_question=str(self.presentation_question),
            reference_case=self.reference_case,
        )


@dataclass(frozen=True)
class ScientificAnalysisRequest:
    """Input of the mathematical-physics analysis stage."""

    raw_input: Path
    analysis_question: str
    reference_case: str | None = None


@dataclass(frozen=True)
class RepresentationFormationRequest:
    """Input of the representation-requirements stage."""

    presentation_question: str
    reference_case: str | None = None


@dataclass(frozen=True)
class MethodSpec:
    """Immutable top-level description of the portable scientific method."""

    method_id: str
    purpose: str
    phases: tuple[dict[str, Any], ...]
    handoff: dict[str, str]
    entry_modes: tuple[dict[str, Any], ...]
    inquiry_cycle: tuple[dict[str, str], ...]
    translation_chain: tuple[str, ...]
    authority: dict[str, str]
    outcome_dimensions: dict[str, str]
    realization_branch: dict[str, Any]
    intent_scope: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "MethodSpec":
        try:
            schema_version = raw["schema_version"]
            if schema_version not in {1, 2}:
                raise ValueError("unsupported method schema")
            inquiry_cycle = tuple(deepcopy(raw["inquiry_cycle"]))
            phases = tuple(deepcopy(raw["phases"]))
            if not all(
                isinstance(phase, dict)
                and phase.get("id")
                and phase.get("question")
                and phase.get("input")
                and phase.get("output")
                and phase.get("completion")
                for phase in phases
            ):
                raise ValueError("invalid phase boundary")
            handoff = deepcopy(raw["handoff"])
            if not isinstance(handoff, dict) or any(
                not handoff.get(field)
                for field in ("artifact", "producer", "consumer", "meaning")
            ):
                raise ValueError("invalid phase handoff")
            entry_modes = tuple(deepcopy(raw["entry_modes"]))
            if not all(
                isinstance(mode, dict)
                and mode.get("id")
                and mode.get("input")
                and mode.get("behavior")
                for mode in entry_modes
            ):
                raise ValueError("invalid entry modes")
            if not all(
                isinstance(stage, dict) and stage.get("id") and stage.get("question")
                for stage in inquiry_cycle
            ):
                raise ValueError("invalid inquiry cycle")
            if schema_version == 2 and "realization_branch" not in raw:
                raise ValueError("method schema 2 requires a realization branch")
            realization_branch = deepcopy(
                raw.get("realization_branch", DEFAULT_REALIZATION_BRANCH)
            )
            if (
                not isinstance(realization_branch, dict)
                or not isinstance(realization_branch.get("inputs"), list)
                or not isinstance(realization_branch.get("selection_basis"), list)
            ):
                raise ValueError("invalid realization branch")
            return cls(
                method_id=str(raw["method_id"]),
                purpose=str(raw["purpose"]),
                phases=phases,
                handoff=handoff,
                entry_modes=entry_modes,
                inquiry_cycle=inquiry_cycle,
                translation_chain=tuple(str(item) for item in raw["translation_chain"]),
                authority=deepcopy(raw["authority"]),
                outcome_dimensions=deepcopy(raw["outcome_dimensions"]),
                realization_branch=realization_branch,
                intent_scope=str(raw["intent_scope"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise PrototypeError(f"Invalid philosophical method record: {exc}") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.method_id,
            "purpose": self.purpose,
            "phases": deepcopy(list(self.phases)),
            "handoff": deepcopy(self.handoff),
            "entry_modes": deepcopy(list(self.entry_modes)),
            "inquiry_cycle": deepcopy(list(self.inquiry_cycle)),
            "translation_chain": list(self.translation_chain),
            "authority": deepcopy(self.authority),
            "outcome_dimensions": deepcopy(self.outcome_dimensions),
            "realization_branch": deepcopy(self.realization_branch),
            "intent_scope": self.intent_scope,
        }


@dataclass(frozen=True)
class RepresentationIntent:
    """Case-level semantic index from theory to representation requirements."""

    intent_id: str
    method_id: str
    case_id: str
    requirements_id: str
    presentation_question: str
    pivotal_hypotheses: tuple[dict[str, Any], ...]
    inquiry_path: dict[str, str]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RepresentationIntent":
        try:
            if raw["schema_version"] != 1:
                raise ValueError("unsupported intent schema")
            hypotheses = tuple(deepcopy(raw["pivotal_hypotheses"]))
            if not hypotheses:
                raise ValueError("no pivotal hypotheses")
            return cls(
                intent_id=str(raw["intent_id"]),
                method_id=str(raw["method_id"]),
                case_id=str(raw["case_id"]),
                requirements_id=str(raw["requirements_id"]),
                presentation_question=str(raw["presentation_question"]),
                pivotal_hypotheses=hypotheses,
                inquiry_path=deepcopy(raw["inquiry_path"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise PrototypeError(f"Invalid representation intent record: {exc}") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.intent_id,
            "intent_id": self.intent_id,
            "method_id": self.method_id,
            "case_id": self.case_id,
            "requirements_id": self.requirements_id,
            "presentation_question": self.presentation_question,
            "pivotal_hypotheses": deepcopy(list(self.pivotal_hypotheses)),
            "inquiry_path": deepcopy(self.inquiry_path),
        }


@dataclass(frozen=True)
class ValidationFinding:
    severity: str
    code: str
    message: str
    case_id: str | None = None
    target: str | None = None

    @property
    def is_error(self) -> bool:
        return self.severity == "error"

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}
