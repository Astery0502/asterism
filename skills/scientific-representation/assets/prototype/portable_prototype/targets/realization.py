"""Typed seam between accepted requirements and a target implementation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ..providers.base import ApplicationDraft, TargetPlanDraft


@dataclass(frozen=True)
class TargetPlanningRequest:
    """Detached target input containing no raw text or private analysis state."""

    target: str
    theoretical_account: str
    representation_intent_id: str
    requirements_id: str
    representation_intent: dict[str, Any]
    requirements_markdown: str
    interface_spec: dict[str, Any]
    capability_catalog: dict[str, Any]
    runtime_observation: dict[str, Any]
    plan_contract: dict[str, Any]
    artifact_contract: dict[str, Any]


@dataclass(frozen=True)
class TargetImplementationRequest:
    """A validated native plan paired with the requirements that produced it."""

    planning: TargetPlanningRequest
    plan: TargetPlanDraft


class TargetRealizer(Protocol):
    """Replaceable target translator and implementation mechanism."""

    realizer_id: str
    target_id: str

    def translate(self, request: TargetPlanningRequest) -> TargetPlanDraft: ...

    def implement(
        self,
        request: TargetImplementationRequest,
        output_root: Path,
    ) -> ApplicationDraft: ...
