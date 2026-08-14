"""Port between accepted requirements and a target implementation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ..domain import (
    ApplicationDraft,
    RepresentationRequirementsPackage,
    TargetPlanDraft,
)


@dataclass(frozen=True)
class TargetPlanningRequest:
    """Detached target input containing no raw text or private analysis state."""

    target: str
    theoretical_account: str
    requirements: RepresentationRequirementsPackage
    capability_catalog: dict[str, Any]
    runtime_observation: dict[str, Any]
    plan_contract: dict[str, Any]
    artifact_contract: dict[str, Any]

    @property
    def theoretical_account_id(self) -> str:
        return self.requirements.theoretical_account_id

    @property
    def representation_intent_id(self) -> str:
        return self.requirements.representation_intent_id

    @property
    def requirements_id(self) -> str:
        return self.requirements.requirements_id

    @property
    def representation_intent(self) -> dict[str, Any]:
        return self.requirements.representation_intent

    @property
    def requirements_markdown(self) -> str:
        return self.requirements.requirements_markdown

    @property
    def interface_spec(self) -> dict[str, Any]:
        return self.requirements.interface_spec


@dataclass(frozen=True)
class ApplicationConformanceRequest:
    """Narrow implementation input for one accepted target-native plan."""

    target: str
    theoretical_account: str
    requirements: RepresentationRequirementsPackage
    artifact_contract: dict[str, Any]
    plan: TargetPlanDraft

    @property
    def theoretical_account_id(self) -> str:
        return self.requirements.theoretical_account_id

    @property
    def representation_intent_id(self) -> str:
        return self.requirements.representation_intent_id

    @property
    def requirements_id(self) -> str:
        return self.requirements.requirements_id

    @property
    def representation_intent(self) -> dict[str, Any]:
        return self.requirements.representation_intent

    @property
    def requirements_markdown(self) -> str:
        return self.requirements.requirements_markdown

    @property
    def interface_spec(self) -> dict[str, Any]:
        return self.requirements.interface_spec


# Compatibility name retained while the lifecycle term becomes canonical.
TargetImplementationRequest = ApplicationConformanceRequest


class TargetTranslator(Protocol):
    """Agent authority that translates requirements into a target-native plan."""

    realizer_id: str
    target_id: str

    def translate(self, request: TargetPlanningRequest) -> TargetPlanDraft: ...


class ApplicationRealizer(Protocol):
    """Agent authority that materializes one accepted target-native plan."""

    realizer_id: str
    target_id: str

    def implement(
        self,
        request: ApplicationConformanceRequest,
        output_root: Path,
    ) -> ApplicationDraft: ...


class TargetRealizer(TargetTranslator, ApplicationRealizer, Protocol):
    """Compatibility composite for targets that provide both realization ports."""
