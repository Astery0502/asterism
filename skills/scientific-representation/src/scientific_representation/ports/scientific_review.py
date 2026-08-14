"""Replaceable port for independent scientific judgment."""

from __future__ import annotations

from typing import Protocol

from ..domain.review import ScientificReviewDraft, ScientificReviewRequest


class ScientificReviewer(Protocol):
    """Judge scientific meaning without owning implementation or validation."""

    reviewer_id: str

    def review(self, request: ScientificReviewRequest) -> ScientificReviewDraft: ...
