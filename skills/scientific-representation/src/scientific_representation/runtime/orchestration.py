"""Raw-input coordinator for the canonical five-stage workflow."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..domain import (
    FrameworkError,
    RawRealizationRequest,
    TheoreticalAccountRecord,
    WorkflowStatus,
)
from ..ports import (
    ApplicationRealizer,
    RepresentationAgent,
    ScientificAnalyst,
    ScientificReviewer,
    TargetTranslator,
)
from .handoff_support import normalize_requirements, planning_request
from .persistence import (
    create_staging_workspace,
    discard_staging_workspace,
    publish_workspace,
    write_json,
    write_text,
)
from .review import ScientificReviewCoordinator
from .target_flow import run_target_stages


STAGES = (
    "analysis",
    "representation",
    "target_translation",
    "application",
    "scientific_review",
)


class RealizationCoordinator:
    """Sequence a raw input through the canonical scientific workflow."""

    def __init__(
        self,
        analyst: ScientificAnalyst,
        target_translator: TargetTranslator | None = None,
        target_context: dict[str, Any] | None = None,
        reviewer: ScientificReviewer | None = None,
        method_id: str = "",
        *,
        representation_agent: RepresentationAgent | None = None,
        application_realizer: ApplicationRealizer | None = None,
    ) -> None:
        self.analyst = analyst
        self.representation_agent = representation_agent or (
            analyst
            if callable(getattr(analyst, "formulate_requirements", None))
            else None
        )
        self.target_translator = target_translator
        self.application_realizer = application_realizer or (
            target_translator
            if callable(getattr(target_translator, "implement", None))
            else None
        )
        self.target_context = deepcopy(target_context or {})
        self.reviewer = reviewer
        self.method_id = method_id

    def realize(
        self, request: RawRealizationRequest, destination: Path
    ) -> dict[str, Any]:
        destination = destination.resolve()
        if destination.exists():
            raise FrameworkError(f"Realization destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            raw_text = request.raw_input.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise FrameworkError(f"Could not read raw scientific input: {exc}") from exc
        if not raw_text.strip():
            raise FrameworkError("Raw scientific input is empty")

        temporary = create_staging_workspace(destination)
        try:
            result = self._run(request, raw_text, temporary)
            publish_workspace(temporary, destination)
        except Exception:
            discard_staging_workspace(temporary)
            raise
        result["workspace"] = str(destination)
        return result

    def _run(
        self, request: RawRealizationRequest, raw_text: str, workspace: Path
    ) -> dict[str, Any]:
        self._write_request_inputs(request, raw_text, workspace)

        completed: list[str] = []
        analysis = self.analyst.analyze(request.analysis_input(raw_text))
        if not analysis.theoretical_account.strip():
            raise FrameworkError("Analysis provider returned an empty TheoreticalAccount")
        write_text(
            workspace / "analysis" / "theoretical-account.md",
            analysis.theoretical_account,
        )
        account_record = TheoreticalAccountRecord.create(
            source_text=raw_text,
            analysis_question=str(request.analysis_question),
            account_content=analysis.theoretical_account,
        )
        write_json(
            workspace / "analysis" / "theoretical-account.json",
            account_record.to_dict(),
        )
        write_json(workspace / "analysis" / "observations.json", analysis.observations)
        completed.append("analysis")
        if request.stop_after == "analysis":
            return self._result(request, completed)

        if self.representation_agent is None:
            raise FrameworkError(
                "Representation stage requires a representation inquiry Agent"
            )
        requirements_draft = self.representation_agent.formulate_requirements(
            request.representation_input(), analysis.theoretical_account
        )
        requirements = normalize_requirements(
            requirements_draft,
            theoretical_account_id=account_record.account_id,
            method_id=self.method_id,
        )
        write_json(
            workspace / "representation" / "representation-intent.json",
            requirements.representation_intent,
        )
        write_text(
            workspace / "representation" / "representation-requirements.md",
            requirements.requirements_markdown,
        )
        write_json(
            workspace / "representation" / "observations.json",
            requirements_draft.observations,
        )
        write_json(
            workspace / "representation" / "representation-interface.json",
            requirements.interface_spec,
        )
        completed.append("representation")
        if request.stop_after == "representation":
            return self._result(request, completed)

        if self.target_translator is None:
            raise FrameworkError(
                "The scientific provider ends at requirements; supply a target realizer"
            )
        planning = planning_request(
            request.target,
            analysis.theoretical_account,
            requirements,
            self.target_context,
        )
        target_stop = (
            "target_translation"
            if request.stop_after == "target_translation"
            else "application"
        )
        outcome = run_target_stages(
            self.target_translator,
            self.application_realizer,
            planning,
            workspace,
            stop_after=target_stop,
        )
        completed.extend(outcome.completed_stages)

        review_status = "not_performed"
        if request.stop_after == "scientific_review":
            if outcome.application_execution == "failed":
                return self._result(
                    request,
                    completed,
                    application_execution="failed",
                    mechanical_passed=outcome.mechanical_passed,
                    requirement_status=outcome.target_requirement_coverage,
                    scientific_review="not_performed",
                    contract_validation=outcome.contract_validation,
                    halted_before="scientific_review",
                    halt_reason="application_execution_failed",
                )
            if self.reviewer is None:
                raise FrameworkError(
                    "Scientific review was requested but no reviewer was supplied"
                )
            review = ScientificReviewCoordinator(self.reviewer).review_staged(
                workspace, target=request.target
            )
            completed.append("scientific_review")
            review_status = review.judgment

        return self._result(
            request,
            completed,
            application_execution=outcome.application_execution,
            mechanical_passed=outcome.mechanical_passed,
            requirement_status=outcome.target_requirement_coverage,
            scientific_review=review_status,
            contract_validation=outcome.contract_validation,
        )

    def _write_request_inputs(
        self, request: RawRealizationRequest, raw_text: str, workspace: Path
    ) -> None:
        write_json(
            workspace / "request.json",
            {
                **asdict(request),
                "raw_input": str(request.raw_input),
                "provider_id": self.analyst.provider_id,
            },
        )
        write_text(workspace / "input" / "scientific-input.md", raw_text)
        write_text(
            workspace / "input" / "analysis-question.md",
            str(request.analysis_question),
        )
        if request.direction:
            write_text(
                workspace / "input" / "presentation-direction.md",
                request.direction,
            )
        if request.presentation_question:
            write_text(
                workspace / "input" / "presentation-question.md",
                request.presentation_question,
            )

    def _result(
        self,
        request: RawRealizationRequest,
        completed: list[str],
        application_execution: str = "not_performed",
        mechanical_passed: bool | None = None,
        requirement_status: str = "not_evaluated",
        scientific_review: str = "not_performed",
        contract_validation: dict[str, Any] | None = None,
        halted_before: str | None = None,
        halt_reason: str | None = None,
    ) -> dict[str, Any]:
        conformance = (
            "not_evaluated"
            if mechanical_passed is None
            else ("passed" if mechanical_passed else "failed")
        )
        result = {
            "operation": "realize",
            "provider": self.analyst.provider_id,
            "realizer": (
                self.target_translator.realizer_id
                if self.target_translator is not None
                else "not_invoked"
            ),
            "target": request.target,
            "stop_after": request.stop_after,
            "completed_stages": completed,
            "status": WorkflowStatus(
                application_execution=application_execution,
                mechanical_conformance=conformance,
                target_requirement_coverage=requirement_status,
                scientific_review=scientific_review,
            ).to_dict(),
        }
        if contract_validation is not None:
            result["contract_validation"] = deepcopy(contract_validation)
        if halted_before is not None:
            result["halted_before"] = halted_before
        if halt_reason is not None:
            result["halt_reason"] = halt_reason
        return result
