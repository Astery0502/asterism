"""Validation findings shared across the framework."""

from __future__ import annotations

from dataclasses import dataclass


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
