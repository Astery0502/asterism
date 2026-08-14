"""Target-neutral interface for registered target definitions."""

from __future__ import annotations

from typing import Any, Protocol


class TargetDefinition(Protocol):
    """Describe one target without translating or realizing an application."""

    target_id: str

    def describe(self) -> dict[str, Any]: ...

    def observe_runtime(self) -> dict[str, Any]: ...
