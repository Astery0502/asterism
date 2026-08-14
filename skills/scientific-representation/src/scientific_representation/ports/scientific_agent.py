"""Ports for Agent-provided scientific reasoning and realization drafts."""

from __future__ import annotations

from typing import Protocol

from ..domain import (
    AnalysisDraft,
    ApplicationDraft,
    RepresentationFormationRequest,
    RequirementsDraft,
    ScientificAnalysisRequest,
    TargetPlanDraft,
)


class ScientificAnalyst(Protocol):
    """Agent authority that produces a bounded scientific account."""

    provider_id: str

    def analyze(self, request: ScientificAnalysisRequest) -> AnalysisDraft: ...


class RepresentationAgent(Protocol):
    """Agent authority that produces target-independent representation requirements."""

    provider_id: str

    def formulate_requirements(
        self, request: RepresentationFormationRequest, theoretical_account: str
    ) -> RequirementsDraft: ...


class ScientificProvider(ScientificAnalyst, RepresentationAgent, Protocol):
    """Compatibility composite for implementations that provide both inquiry ports."""
