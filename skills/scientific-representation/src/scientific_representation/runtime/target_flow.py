"""Resumable target translation and application-conformance mechanics."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..domain import (
    FrameworkError,
    RepresentationRequirementsPackage,
    TheoreticalAccountRecord,
    WorkflowStatus,
)
from ..ports import (
    ApplicationConformanceRequest,
    ApplicationRealizer,
    RequirementsDraft,
    TargetPlanDraft,
    TargetPlanningRequest,
    TargetTranslator,
)
from ..targets.artifact_validation import validate_target_application
from ..targets.plan_validation import (
    validate_target_plan,
    validate_target_plan_implementation_ready,
)
from ..targets.traceability import target_requirement_coverage
from .handoff_support import normalize_requirements, planning_request, validate_realizer
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
class TargetStageOutcome:
    completed_stages: tuple[str, ...]
    application_execution: str
    mechanical_passed: bool | None
    target_requirement_coverage: str
    contract_validation: dict[str, Any]


@dataclass(frozen=True)
class ApplicationStageOutcome:
    execution_status: str
    contract_validation: dict[str, Any]


class RequirementsRealizationCoordinator:
    """Resume target translation from persisted representation requirements."""

    def __init__(
        self,
        target_translator: TargetTranslator,
        target_context: dict[str, Any] | None = None,
        *,
        method_id: str = "",
        application_realizer: ApplicationRealizer | None = None,
    ) -> None:
        self.target_translator = target_translator
        self.application_realizer = application_realizer or (
            target_translator
            if callable(getattr(target_translator, "implement", None))
            else None
        )
        self.target_context = deepcopy(target_context or {})
        self.method_id = method_id

    def realize(
        self,
        source_workspace: Path,
        destination: Path,
        *,
        target: str,
        stop_after: str = "application",
    ) -> dict[str, Any]:
        if stop_after not in {"target_translation", "application"}:
            raise FrameworkError(
                "Requirements realization may stop at target_translation or application"
            )
        validate_realizer(target, self.target_translator)
        source = source_workspace.resolve()
        destination = destination.resolve()
        if destination.exists():
            raise FrameworkError(f"Realization destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)

        account, account_record, requirements = _load_representation_handoff(
            source, method_id=self.method_id, source_kind="persisted-requirements-workspace"
        )
        planning = planning_request(
            target,
            account,
            requirements,
            self.target_context,
        )
        temporary = create_staging_workspace(destination)
        try:
            write_json(
                temporary / "request.json",
                {
                    "operation": "realize-target",
                    "target": target,
                    "stop_after": stop_after,
                    "realizer_id": self.target_translator.realizer_id,
                    "source_kind": "persisted-requirements-workspace",
                },
            )
            _write_representation_handoff(
                temporary, account, account_record, requirements
            )
            outcome = run_target_stages(
                self.target_translator,
                self.application_realizer,
                planning,
                temporary,
                stop_after=stop_after,
            )
            publish_workspace(temporary, destination)
        except Exception:
            discard_staging_workspace(temporary)
            raise
        return {
            "operation": "realize-target",
            "realizer": self.target_translator.realizer_id,
            "target": target,
            "stop_after": stop_after,
            "completed_stages": list(outcome.completed_stages),
            "contract_validation": outcome.contract_validation,
            "workspace": str(destination),
            "status": WorkflowStatus(
                application_execution=outcome.application_execution,
                mechanical_conformance=(
                    "not_evaluated"
                    if outcome.mechanical_passed is None
                    else ("passed" if outcome.mechanical_passed else "failed")
                ),
                target_requirement_coverage=outcome.target_requirement_coverage,
            ).to_dict(),
        }


class PlanApplicationCoordinator:
    """Resume application conformance from an accepted native plan."""

    def __init__(
        self,
        application_realizer: ApplicationRealizer,
        target_context: dict[str, Any] | None = None,
        *,
        method_id: str = "",
    ) -> None:
        self.application_realizer = application_realizer
        self.target_context = deepcopy(target_context or {})
        self.method_id = method_id

    def realize(
        self, source_workspace: Path, destination: Path, *, target: str
    ) -> dict[str, Any]:
        validate_realizer(target, self.application_realizer)
        source = source_workspace.resolve()
        destination = destination.resolve()
        if destination.exists():
            raise FrameworkError(f"Realization destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        account, account_record, requirements = _load_representation_handoff(
            source, method_id=self.method_id, source_kind="persisted-target-plan-workspace"
        )
        planning = planning_request(
            target,
            account,
            requirements,
            self.target_context,
        )
        plan_record = read_json(
            source / "targets" / target / "native-plan.json", "target-native plan"
        )
        validate_target_plan(planning, plan_record)
        plan = TargetPlanDraft(
            target=target,
            plan=plan_record,
            observations={"source_kind": "persisted-target-plan-workspace"},
        )
        temporary = create_staging_workspace(destination)
        try:
            copy_workspace(source, temporary)
            outcome = run_application_stage(
                self.application_realizer, planning, plan, temporary
            )
            publish_workspace(temporary, destination)
        except Exception:
            discard_staging_workspace(temporary)
            raise
        return {
            "operation": "realize-plan",
            "realizer": self.application_realizer.realizer_id,
            "target": target,
            "completed_stages": ["application"],
            "contract_validation": outcome.contract_validation,
            "workspace": str(destination),
            "status": WorkflowStatus(
                application_execution=outcome.execution_status,
                mechanical_conformance=(
                    "passed"
                    if outcome.contract_validation.get("pass") is True
                    else "failed"
                ),
                target_requirement_coverage=target_requirement_coverage(plan_record),
            ).to_dict(),
        }


def run_target_stages(
    translator: TargetTranslator,
    application_realizer: ApplicationRealizer | None,
    planning: TargetPlanningRequest,
    workspace: Path,
    *,
    stop_after: str,
) -> TargetStageOutcome:
    """Translate and optionally implement through the common validator path."""

    if stop_after not in {"target_translation", "application"}:
        raise FrameworkError(
            "Target stages may stop at target_translation or application"
        )
    validate_realizer(planning.target, translator)
    plan = translator.translate(planning)
    if plan.target != planning.target:
        raise FrameworkError("Target realizer returned a plan for the wrong target")
    if not isinstance(plan.plan, dict) or not plan.plan:
        raise FrameworkError("Target realizer returned an empty plan")
    validate_target_plan(planning, plan.plan)
    write_json(
        workspace / "targets" / planning.target / "native-plan.json", plan.plan
    )
    write_json(
        workspace / "targets" / planning.target / "observations.json",
        plan.observations,
    )
    coverage = target_requirement_coverage(plan.plan)
    plan_validation = {
        "status": "plan-contract-validated",
        "plan_contract_id": planning.plan_contract.get("contract_id"),
        "pass": True,
    }
    write_json(
        workspace / "targets" / planning.target / "contract-validation.json",
        plan_validation,
    )
    if stop_after == "target_translation":
        return TargetStageOutcome(
            ("target_translation",),
            "not_performed",
            None,
            coverage,
            plan_validation,
        )
    if application_realizer is None:
        raise FrameworkError("Application stage requires an application realizer")
    application_outcome = run_application_stage(
        application_realizer, planning, plan, workspace
    )
    return TargetStageOutcome(
        ("target_translation", "application"),
        application_outcome.execution_status,
        application_outcome.contract_validation["pass"],
        coverage,
        application_outcome.contract_validation,
    )


def run_application_stage(
    realizer: ApplicationRealizer,
    planning: TargetPlanningRequest,
    plan: TargetPlanDraft,
    workspace: Path,
) -> ApplicationStageOutcome:
    """Implement one validated native plan through the common validator path."""

    validate_target_plan_implementation_ready(planning, plan.plan)
    application = realizer.implement(
        ApplicationConformanceRequest(
            target=planning.target,
            theoretical_account=planning.theoretical_account,
            requirements=planning.requirements,
            artifact_contract=deepcopy(planning.artifact_contract),
            plan=plan,
        ),
        workspace / "application",
    )
    if not isinstance(application.observations, dict):
        raise FrameworkError("Target realizer returned an invalid application result")
    execution = {
        "execution_status": application.execution_status,
        "manifest_record": application.manifest_record,
    }
    write_json(workspace / "application" / "result.json", execution)
    write_json(
        workspace / "application" / "observations.json", application.observations
    )
    validation = validate_target_application(
        planning,
        plan.plan,
        application.execution_status,
        application.manifest_record,
        workspace / "application",
    )
    write_json(
        workspace / "application" / "contract-validation.json", validation
    )
    return ApplicationStageOutcome(application.execution_status, validation)


def _load_representation_handoff(
    source: Path, *, method_id: str, source_kind: str
) -> tuple[str, TheoreticalAccountRecord, RepresentationRequirementsPackage]:
    account = read_text(
        source / "analysis" / "theoretical-account.md", "TheoreticalAccount"
    )
    account_record = TheoreticalAccountRecord.from_dict(
        read_json(
            source / "analysis" / "theoretical-account.json",
            "theoretical account lineage",
        )
    )
    account_record.verify_content(account)
    intent = read_json(
        source / "representation" / "representation-intent.json",
        "representation intent",
    )
    requirements_markdown = read_text(
        source / "representation" / "representation-requirements.md",
        "representation requirements",
    )
    interface_path = source / "representation" / "representation-interface.json"
    interface = (
        read_json(interface_path, "representation interface")
        if interface_path.is_file()
        else {}
    )
    requirements = normalize_requirements(
        RequirementsDraft(
            representation_intent=intent,
            requirements_markdown=requirements_markdown,
            observations={"source_kind": source_kind},
            interface_spec=interface,
        ),
        theoretical_account_id=account_record.account_id,
        method_id=method_id,
    )
    return account, account_record, requirements


def _write_representation_handoff(
    workspace: Path,
    account: str,
    account_record: TheoreticalAccountRecord,
    requirements: RepresentationRequirementsPackage,
) -> None:
    write_text(workspace / "analysis" / "theoretical-account.md", account)
    write_json(
        workspace / "analysis" / "theoretical-account.json",
        account_record.to_dict(),
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
        workspace / "representation" / "representation-interface.json",
        requirements.interface_spec,
    )
