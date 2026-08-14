"""Requests entering the Agent-centered scientific workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .errors import FrameworkError


DEFAULT_ANALYSIS_QUESTION = (
    "What mathematical or physical account follows from the supplied material, "
    "and where is it valid?"
)


@dataclass(frozen=True)
class RawRealizationRequest:
    """One user request whose internal stages retain explicit boundaries."""

    raw_input: Path
    direction: str
    target: str
    stop_after: str
    analysis_question: str | None = None
    presentation_question: str | None = None

    def __post_init__(self) -> None:
        if self.stop_after not in {
            "analysis",
            "representation",
            "target_translation",
            "application",
            "scientific_review",
        }:
            raise FrameworkError(f"Unknown realization stop stage: {self.stop_after}")
        analysis_question = (self.analysis_question or DEFAULT_ANALYSIS_QUESTION).strip()
        direction = self.direction.strip()
        presentation_question = (
            self.presentation_question.strip()
            if self.presentation_question is not None
            else None
        )
        if not analysis_question:
            raise FrameworkError("Analysis question is empty")
        if (
            self.stop_after != "analysis"
            and not direction
            and not presentation_question
        ):
            raise FrameworkError(
                "Representation requires a presentation direction or direct question"
            )
        object.__setattr__(self, "analysis_question", analysis_question)
        object.__setattr__(self, "presentation_question", presentation_question)
        object.__setattr__(self, "direction", direction)

    def analysis_input(self, scientific_input: str) -> "ScientificAnalysisRequest":
        return ScientificAnalysisRequest(
            scientific_input=scientific_input,
            analysis_question=str(self.analysis_question),
        )

    def representation_input(self) -> "RepresentationFormationRequest":
        return RepresentationFormationRequest(
            presentation_direction=self.direction,
            presentation_question=self.presentation_question,
        )


@dataclass(frozen=True)
class ScientificAnalysisRequest:
    """Input of the mathematical-physics analysis stage."""

    scientific_input: str
    analysis_question: str


@dataclass(frozen=True)
class RepresentationFormationRequest:
    """Input of the representation-requirements stage."""

    presentation_direction: str
    presentation_question: str | None = None
