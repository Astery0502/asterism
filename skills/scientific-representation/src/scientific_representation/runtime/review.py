"""Mechanical loading and persistence for independent scientific review."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from ..domain import (
    FrameworkError,
    ScientificReviewRequest,
    TheoreticalAccountRecord,
    WorkflowStatus,
    content_digest,
)
from ..ports import ScientificReviewer
from ..targets.traceability import target_requirement_coverage
from ..targets.validation_support import contained_path
from .persistence import (
    copy_workspace,
    create_staging_workspace,
    discard_staging_workspace,
    publish_workspace,
    read_json,
    read_text,
    write_json,
    write_text,
)


@dataclass(frozen=True)
class ReviewOutcome:
    reviewer_id: str
    judgment: str
    target_requirement_coverage: str
    mechanical_conformance: str


class ScientificReviewCoordinator:
    """Expose one review boundary while hiding workspace mechanics."""

    def __init__(self, reviewer: ScientificReviewer) -> None:
        self.reviewer = reviewer

    def review(
        self,
        source_workspace: Path,
        destination: Path,
        *,
        target: str,
    ) -> dict[str, Any]:
        source = source_workspace.resolve()
        destination = destination.resolve()
        if destination.exists():
            raise FrameworkError(f"Review destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = create_staging_workspace(destination)
        try:
            copy_workspace(source, temporary)
            outcome = self.review_staged(temporary, target=target)
            publish_workspace(temporary, destination)
        except Exception:
            discard_staging_workspace(temporary)
            raise
        return {
            "operation": "review-application",
            "reviewer": outcome.reviewer_id,
            "target": target,
            "completed_stages": ["scientific_review"],
            "workspace": str(destination),
            "status": WorkflowStatus(
                application_execution="completed",
                mechanical_conformance=outcome.mechanical_conformance,
                target_requirement_coverage=outcome.target_requirement_coverage,
                scientific_review=outcome.judgment,
            ).to_dict(),
        }

    def review_staged(self, workspace: Path, *, target: str) -> ReviewOutcome:
        request, plan, contract_validation = self._load_request(workspace, target)
        draft = self.reviewer.review(request)
        judgment = str(draft.judgment)
        WorkflowStatus(scientific_review=judgment)
        if not isinstance(draft.record_markdown, str) or not draft.record_markdown.strip():
            raise FrameworkError("Scientific reviewer returned an empty review record")
        if not isinstance(draft.observations, dict):
            raise FrameworkError("Scientific reviewer returned invalid observations")
        write_text(workspace / "review" / "scientific-review.md", draft.record_markdown)
        reviewed = {
            "theoretical_account_id": request.theoretical_account_id,
            "representation_intent_id": request.representation_intent.get(
                "intent_id"
            ),
            "requirements_id": request.representation_intent.get(
                "requirements_id"
            ),
            "plan_id": request.target_plan.get("plan_id"),
            "application_manifest_digest": content_digest(
                json.dumps(
                    request.application_manifest,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            ),
        }
        review_identity = {
            "reviewer_id": self.reviewer.reviewer_id,
            "judgment": judgment,
            "record_digest": content_digest(draft.record_markdown),
            "reviewed": reviewed,
        }
        write_json(
            workspace / "review" / "review-result.json",
            {
                "schema_version": 1,
                "review_id": "scientific-review:"
                + content_digest(
                    json.dumps(review_identity, sort_keys=True, separators=(",", ":"))
                ),
                **review_identity,
            },
        )
        write_json(
            workspace / "review" / "observations.json",
            deepcopy(draft.observations),
        )
        mechanical = "passed" if contract_validation.get("pass") is True else "failed"
        return ReviewOutcome(
            reviewer_id=self.reviewer.reviewer_id,
            judgment=judgment,
            target_requirement_coverage=target_requirement_coverage(plan),
            mechanical_conformance=mechanical,
        )

    @staticmethod
    def _load_request(
        workspace: Path, target: str
    ) -> tuple[ScientificReviewRequest, dict[str, Any], dict[str, Any]]:
        account = read_text(
            workspace / "analysis" / "theoretical-account.md", "TheoreticalAccount"
        )
        account_record = TheoreticalAccountRecord.from_dict(
            read_json(
                workspace / "analysis" / "theoretical-account.json",
                "theoretical account lineage",
            )
        )
        account_record.verify_content(account)
        intent = read_json(
            workspace / "representation" / "representation-intent.json",
            "representation intent",
        )
        if intent.get("theoretical_account_id") != account_record.account_id:
            raise FrameworkError(
                "Representation intent refers to a different theoretical account"
            )
        requirements = read_text(
            workspace / "representation" / "representation-requirements.md",
            "representation requirements",
        )
        interface = read_json(
            workspace / "representation" / "representation-interface.json",
            "representation interface",
        )
        plan = read_json(
            workspace / "targets" / target / "native-plan.json",
            "target-native plan",
        )
        application_root = workspace / "application"
        execution = read_json(
            application_root / "result.json", "application execution record"
        )
        if execution.get("execution_status") != "completed":
            raise FrameworkError(
                "Scientific review requires a completed application execution"
            )
        manifest_record = execution.get("manifest_record")
        if not isinstance(manifest_record, str) or not manifest_record.strip():
            raise FrameworkError(
                "Completed application execution declares no manifest record"
            )
        manifest_path = contained_path(
            application_root, manifest_record, "application manifest"
        )
        manifest = read_json(
            manifest_path, "application manifest"
        )
        expected_links = {
            "plan representation intent": (
                plan.get("representation_intent_id"),
                intent.get("intent_id"),
            ),
            "plan requirements": (
                plan.get("requirements_id"),
                intent.get("requirements_id"),
            ),
            "manifest plan": (manifest.get("plan_id"), plan.get("plan_id")),
            "manifest target": (manifest.get("target_id"), target),
            "manifest representation intent": (
                manifest.get("representation_intent_id"),
                intent.get("intent_id"),
            ),
            "manifest requirements": (
                manifest.get("requirements_id"),
                intent.get("requirements_id"),
            ),
        }
        mismatched = [
            name for name, (actual, expected) in expected_links.items() if actual != expected
        ]
        if mismatched:
            raise FrameworkError(
                f"Scientific review lineage links differ: {mismatched}"
            )
        contract_validation = read_json(
            application_root / "contract-validation.json",
            "application contract validation",
        )
        evidence: dict[str, Any] = {
            "application_execution": execution,
            "contract_validation": contract_validation,
            "records": {},
        }
        for relative in manifest.get("validation_evidence", []):
            path = contained_path(application_root, relative, "review evidence")
            evidence["records"][relative] = read_json(path, f"review evidence {relative}")
        return (
            ScientificReviewRequest(
                target=target,
                theoretical_account_id=account_record.account_id,
                theoretical_account=account,
                representation_intent=intent,
                requirements_markdown=requirements,
                interface_spec=interface,
                target_plan=plan,
                application_manifest=manifest,
                mechanical_evidence=evidence,
                application_root=application_root,
            ),
            plan,
            contract_validation,
        )
