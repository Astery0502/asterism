"""Compatibility exports for the domain package.

New code should import from :mod:`scientific_representation.domain`.
"""

from .domain import (
    DEFAULT_ANALYSIS_QUESTION,
    FrameworkError,
    MethodSpec,
    RawRealizationRequest,
    RepresentationFormationRequest,
    RepresentationIntent,
    ScientificAnalysisRequest,
    ScientificReviewDraft,
    ScientificReviewRequest,
    TheoreticalAccountRecord,
    ValidationFinding,
    WorkflowStatus,
)

__all__ = [
    "DEFAULT_ANALYSIS_QUESTION",
    "FrameworkError",
    "MethodSpec",
    "RawRealizationRequest",
    "RepresentationFormationRequest",
    "RepresentationIntent",
    "ScientificAnalysisRequest",
    "ScientificReviewDraft",
    "ScientificReviewRequest",
    "TheoreticalAccountRecord",
    "ValidationFinding",
    "WorkflowStatus",
]
