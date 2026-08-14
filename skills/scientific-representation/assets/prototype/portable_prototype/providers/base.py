"""Typed stage results and protocol for one-step scientific realization."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from ..models import (
    RawRealizationRequest,
    RepresentationFormationRequest,
    ScientificAnalysisRequest,
)


@dataclass(frozen=True)
class AnalysisDraft:
    theoretical_account: str
    observations: dict[str, Any]


@dataclass(frozen=True)
class RequirementsDraft:
    representation_intent: dict[str, Any]
    requirements_markdown: str
    observations: dict[str, Any]
    interface_spec: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TargetPlanDraft:
    target: str
    plan: dict[str, Any]
    observations: dict[str, Any]


@dataclass(frozen=True)
class ApplicationDraft:
    result: dict[str, Any]
    observations: dict[str, Any]


class ScientificProvider(Protocol):
    """Scientific intelligence that ends at target-independent requirements."""

    provider_id: str

    def analyze(self, request: ScientificAnalysisRequest, raw_text: str) -> AnalysisDraft: ...

    def formulate_requirements(
        self, request: RepresentationFormationRequest, theoretical_account: str
    ) -> RequirementsDraft: ...


class RealizationProvider(ScientificProvider, Protocol):
    """Compatibility contract for providers that still own every stage."""

    def translate(
        self,
        request: RawRealizationRequest,
        theoretical_account: str,
        requirements: RequirementsDraft,
    ) -> TargetPlanDraft: ...

    def implement(
        self,
        request: RawRealizationRequest,
        plan: TargetPlanDraft,
        output_root: Path,
    ) -> ApplicationDraft: ...
