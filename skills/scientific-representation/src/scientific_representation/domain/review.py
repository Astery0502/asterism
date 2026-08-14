"""Stable values crossing the independent scientific-review boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScientificReviewRequest:
    """Read-only public evidence bundle supplied to a scientific reviewer."""

    target: str
    theoretical_account_id: str
    theoretical_account: str
    representation_intent: dict[str, Any]
    requirements_markdown: str
    interface_spec: dict[str, Any]
    target_plan: dict[str, Any]
    application_manifest: dict[str, Any]
    mechanical_evidence: dict[str, Any]
    application_root: Path


@dataclass(frozen=True)
class ScientificReviewDraft:
    """Reviewer-owned judgment and its inspectable public record."""

    judgment: str
    record_markdown: str
    observations: dict[str, Any]
