"""Public Python boundary of the Scientific Representation framework."""

from .domain import FrameworkError, ValidationFinding
from .runtime import FrameworkArchitecture, ScientificRepresentationApp

__all__ = [
    "FrameworkArchitecture",
    "FrameworkError",
    "ScientificRepresentationApp",
    "ValidationFinding",
]
