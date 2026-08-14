"""Minimal values that cross lifecycle module boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

from .errors import FrameworkError
from .representation import RepresentationIntent


def content_digest(value: str) -> str:
    """Return one stable content identity without assigning scientific meaning."""

    persisted = value.rstrip() + "\n"
    return f"sha256:{sha256(persisted.encode('utf-8')).hexdigest()}"


@dataclass(frozen=True)
class TheoreticalAccountRecord:
    """Lineage sidecar for the human-readable TheoreticalAccount."""

    account_id: str
    source_digest: str
    analysis_question: str

    @classmethod
    def create(
        cls, *, source_text: str, analysis_question: str, account_content: str
    ) -> "TheoreticalAccountRecord":
        return cls(
            account_id=f"theoretical-account:{content_digest(account_content)}",
            source_digest=content_digest(source_text),
            analysis_question=analysis_question,
        )

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "TheoreticalAccountRecord":
        try:
            if raw["schema_version"] != 1:
                raise ValueError("unsupported account record schema")
            record = cls(
                account_id=str(raw["account_id"]),
                source_digest=str(raw["source_digest"]),
                analysis_question=str(raw["analysis_question"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise FrameworkError(f"Invalid theoretical account record: {exc}") from exc
        if not all(
            value.strip()
            for value in (
                record.account_id,
                record.source_digest,
                record.analysis_question,
            )
        ):
            raise FrameworkError("Theoretical account record contains empty fields")
        return record

    def verify_content(self, account_content: str) -> None:
        expected = f"theoretical-account:{content_digest(account_content)}"
        if self.account_id != expected:
            raise FrameworkError(
                "Theoretical account content differs from its lineage record"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "account_id": self.account_id,
            "source_digest": self.source_digest,
            "analysis_question": self.analysis_question,
        }


@dataclass(frozen=True)
class AnalysisDraft:
    theoretical_account: str
    observations: dict[str, Any]


@dataclass(frozen=True)
class RequirementsDraft:
    representation_intent: dict[str, Any]
    requirements_markdown: str
    observations: dict[str, Any]
    interface_spec: dict[str, Any]


@dataclass(frozen=True)
class RepresentationRequirementsPackage:
    """Accepted, target-neutral handoff from representation inquiry."""

    intent: RepresentationIntent
    requirements_markdown: str
    interface_spec: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.requirements_markdown.strip():
            raise FrameworkError("Representation requirements package is empty")
        if not isinstance(self.interface_spec, dict):
            raise FrameworkError("Representation requirements interface must be an object")

    @property
    def theoretical_account_id(self) -> str:
        return self.intent.theoretical_account_id

    @property
    def representation_intent_id(self) -> str:
        return self.intent.intent_id

    @property
    def requirements_id(self) -> str:
        return self.intent.requirements_id

    @property
    def representation_intent(self) -> dict[str, Any]:
        return self.intent.to_dict()


@dataclass(frozen=True)
class TargetPlanDraft:
    target: str
    plan: dict[str, Any]
    observations: dict[str, Any]


@dataclass(frozen=True)
class ApplicationDraft:
    """Implementation execution result; conformance is judged separately."""

    execution_status: str
    observations: dict[str, Any] = field(default_factory=dict)
    manifest_record: str | None = None

    def __post_init__(self) -> None:
        if self.execution_status not in {"completed", "failed"}:
            raise FrameworkError(
                f"Unknown implementation execution status: {self.execution_status}"
            )
        if self.execution_status == "completed" and not (
            isinstance(self.manifest_record, str) and self.manifest_record.strip()
        ):
            raise FrameworkError("Completed implementation declares no manifest record")
        if self.execution_status == "failed" and self.manifest_record is not None:
            raise FrameworkError("Failed implementation must not declare a manifest record")
