"""Coordinator that stitches raw analysis into the representation pipeline."""

from __future__ import annotations

import json
import shutil
import tempfile
from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .models import (
    PrototypeError,
    RawRealizationRequest,
    RepresentationFormationRequest,
)
from .providers.base import ScientificProvider, RequirementsDraft, TargetPlanDraft
from .targets.realization import (
    TargetImplementationRequest,
    TargetPlanningRequest,
    TargetRealizer,
)
from .targets.contracts import (
    validate_target_application,
    validate_target_plan,
    validate_target_plan_implementation_ready,
)


STAGES = ("analysis", "requirements", "plan", "application")


@dataclass(frozen=True)
class TargetStageOutcome:
    completed_stages: tuple[str, ...]
    mechanical_passed: bool
    contract_validation: dict[str, Any]


class RealizationCoordinator:
    """Own sequencing and persistence while providers own scientific work."""

    def __init__(
        self,
        provider: ScientificProvider,
        target_realizer: TargetRealizer | None = None,
        target_context: dict[str, Any] | None = None,
    ) -> None:
        self.provider = provider
        self.target_realizer = target_realizer
        self.target_context = deepcopy(target_context or {})

    def realize(
        self, request: RawRealizationRequest, destination: Path
    ) -> dict[str, Any]:
        destination = destination.resolve()
        if destination.exists():
            raise PrototypeError(f"Realization destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            raw_text = request.raw_input.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise PrototypeError(f"Could not read raw scientific input: {exc}") from exc
        if not raw_text.strip():
            raise PrototypeError("Raw scientific input is empty")

        temporary = Path(
            tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent)
        )
        try:
            result = self._run(request, raw_text, temporary)
            self._rebase_json_artifacts(temporary, temporary, destination)
            temporary.replace(destination)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        result["workspace"] = str(destination)
        return result

    def _run(
        self, request: RawRealizationRequest, raw_text: str, workspace: Path
    ) -> dict[str, Any]:
        self._write_json(
            workspace / "request.json",
            {
                **asdict(request),
                "raw_input": str(request.raw_input),
                "provider_id": self.provider.provider_id,
            },
        )
        self._write_text(workspace / "input" / "raw-scientific-text.md", raw_text)
        self._write_text(
            workspace / "input" / "analysis-question.md",
            str(request.analysis_question),
        )
        if request.presentation_question:
            self._write_text(
                workspace / "input" / "presentation-question.md",
                str(request.presentation_question),
            )
            self._write_text(workspace / "input" / "direction.md", request.direction)

        completed: list[str] = []
        analysis = self.provider.analyze(request.analysis_input(), raw_text)
        if not analysis.theoretical_account.strip():
            raise PrototypeError("Analysis provider returned an empty TheoreticalAccount")
        self._write_text(
            workspace / "analysis" / "theoretical-account.md",
            analysis.theoretical_account,
        )
        self._write_json(workspace / "analysis" / "observations.json", analysis.observations)
        completed.append("analysis")
        if request.stop_after == "analysis":
            return self._result(request, completed)

        requirements = self._normalize_requirements(
            self.provider.formulate_requirements(
                request.representation_input(), analysis.theoretical_account
            )
        )
        self._write_json(
            workspace / "representation" / "representation-intent.json",
            requirements.representation_intent,
        )
        self._write_text(
            workspace / "representation" / "representation-requirements.md",
            requirements.requirements_markdown,
        )
        self._write_json(
            workspace / "representation" / "observations.json",
            requirements.observations,
        )
        self._write_json(
            workspace / "representation" / "representation-interface.json",
            requirements.interface_spec,
        )
        completed.append("requirements")
        if request.stop_after == "requirements":
            return self._result(request, completed)

        if self.target_realizer is not None:
            planning = self._planning_request(
                request.target,
                analysis.theoretical_account,
                requirements,
                self.target_context,
            )
            outcome = _run_target_stages(
                self.target_realizer,
                planning,
                workspace,
                stop_after=request.stop_after,
            )
            completed.extend(outcome.completed_stages)
            return self._result(
                request,
                completed,
                outcome.mechanical_passed,
                contract_validation=outcome.contract_validation,
            )

        translate = getattr(self.provider, "translate", None)
        if not callable(translate):
            raise PrototypeError(
                "The scientific provider ends at requirements; supply a target realizer"
            )
        plan = translate(request, analysis.theoretical_account, requirements)
        self._validate_plan(request, plan)
        self._write_json(workspace / "targets" / request.target / "plan.json", plan.plan)
        self._write_json(
            workspace / "targets" / request.target / "observations.json",
            plan.observations,
        )
        completed.append("plan")
        if request.stop_after == "plan":
            return self._result(request, completed)

        implement = getattr(self.provider, "implement", None)
        if not callable(implement):
            raise PrototypeError(
                "The scientific provider cannot implement the target; supply a target realizer"
            )
        application = implement(request, plan, workspace / "application")
        self._write_json(workspace / "application" / "result.json", application.result)
        self._write_json(
            workspace / "application" / "observations.json",
            application.observations,
        )
        completed.append("application")
        return self._result(request, completed, application.result.get("pass") is True)

    def _result(
        self,
        request: RawRealizationRequest,
        completed: list[str],
        mechanical_passed: bool = True,
        contract_validation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        conformance = (
            ("passed" if mechanical_passed else "failed")
            if "application" in completed
            else "not_evaluated"
        )
        result = {
            "operation": "realize",
            "provider": self.provider.provider_id,
            "realizer": (
                self.target_realizer.realizer_id
                if self.target_realizer is not None
                else "provider-owned-compatibility"
            ),
            "target": request.target,
            "stop_after": request.stop_after,
            "completed_stages": completed,
            "pass": mechanical_passed,
            "outcome_status": {
                "mechanical_conformance": conformance,
                "scientific_review": "not_performed",
                "interpretive_authority": "analysis_and_review",
            },
        }
        if contract_validation is not None:
            result["contract_validation"] = deepcopy(contract_validation)
        return result

    @staticmethod
    def _validate_requirements(requirements: RequirementsDraft) -> None:
        if not requirements.requirements_markdown.strip():
            raise PrototypeError("Requirements provider returned empty requirements")
        intent = requirements.representation_intent
        if not isinstance(intent, dict) or not intent.get("presentation_question"):
            raise PrototypeError("Requirements provider returned no presentation question")
        if not intent.get("pivotal_hypotheses"):
            raise PrototypeError("Requirements provider returned no pivotal hypotheses")

    @classmethod
    def _normalize_requirements(
        cls,
        requirements: RequirementsDraft,
    ) -> RequirementsDraft:
        """Normalize identity aliases once at the scientific/target boundary."""

        cls._validate_requirements(requirements)
        intent = deepcopy(requirements.representation_intent)
        declared_intent_ids = {
            value
            for value in (intent.get("intent_id"), intent.get("id"))
            if isinstance(value, str) and value.strip()
        }
        if len(declared_intent_ids) > 1:
            raise PrototypeError("Representation intent identity fields disagree")
        if not declared_intent_ids:
            raise PrototypeError("Requirements provider returned no representation intent ID")
        intent_id = next(iter(declared_intent_ids), None)
        requirements_id = intent.get("requirements_id")
        if (
            not isinstance(requirements_id, str) or not requirements_id.strip()
        ):
            raise PrototypeError("Requirements provider returned no requirements ID")
        if intent_id is not None:
            intent["intent_id"] = intent_id
            intent["id"] = intent_id
        if isinstance(requirements_id, str) and requirements_id.strip():
            intent["requirements_id"] = requirements_id
        interface_spec = cls._normalize_interface(requirements.interface_spec)
        return RequirementsDraft(
            representation_intent=intent,
            requirements_markdown=requirements.requirements_markdown,
            observations=deepcopy(requirements.observations),
            interface_spec=interface_spec,
        )

    @staticmethod
    def _normalize_interface(interface_spec: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(interface_spec, dict):
            raise PrototypeError("Representation interface must be an object")
        normalized = deepcopy(interface_spec)
        for field in ("controls", "anchors", "views", "exports"):
            value = normalized.setdefault(field, [])
            if not isinstance(value, list):
                raise PrototypeError(f"Representation interface {field} must be a list")
        return normalized

    @staticmethod
    def _validate_plan(request: RawRealizationRequest, plan: TargetPlanDraft) -> None:
        if plan.target != request.target:
            raise PrototypeError("Target provider returned a plan for the wrong target")
        if not plan.plan:
            raise PrototypeError("Target provider returned an empty plan")

    @staticmethod
    def _validate_realizer(target: str, realizer: TargetRealizer) -> None:
        if realizer.target_id != target:
            raise PrototypeError(
                f"Target realizer '{realizer.realizer_id}' serves "
                f"'{realizer.target_id}', not '{target}'"
            )

    @staticmethod
    def _planning_request(
        target: str,
        theoretical_account: str,
        requirements: RequirementsDraft,
        target_context: dict[str, Any] | None = None,
    ) -> TargetPlanningRequest:
        context = target_context or {}
        intent_id = str(requirements.representation_intent["intent_id"])
        requirements_id = str(requirements.representation_intent["requirements_id"])
        return TargetPlanningRequest(
            target=target,
            theoretical_account=theoretical_account,
            representation_intent_id=intent_id,
            requirements_id=requirements_id,
            representation_intent=deepcopy(requirements.representation_intent),
            requirements_markdown=requirements.requirements_markdown,
            interface_spec=deepcopy(requirements.interface_spec),
            capability_catalog=deepcopy(context.get("capabilities", {})),
            runtime_observation=deepcopy(context.get("runtime_observation", {})),
            plan_contract=deepcopy(context.get("plan_contract", {})),
            artifact_contract=deepcopy(context.get("artifact_contract", {})),
        )

    @staticmethod
    def _write_text(path: Path, value: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value.rstrip() + "\n", encoding="utf-8")

    @staticmethod
    def _write_json(path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    @classmethod
    def _rebase_json_artifacts(
        cls, workspace: Path, old_root: Path, new_root: Path
    ) -> None:
        """Replace staging paths before atomic publication."""

        old = str(old_root)
        new = str(new_root)

        def rebase(value: Any) -> Any:
            if isinstance(value, str):
                return value.replace(old, new)
            if isinstance(value, list):
                return [rebase(item) for item in value]
            if isinstance(value, dict):
                return {key: rebase(item) for key, item in value.items()}
            return value

        for path in workspace.rglob("*.json"):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise PrototypeError(f"Could not rebase realization record {path}: {exc}") from exc
            path.write_text(
                json.dumps(rebase(raw), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )


class RequirementsRealizationCoordinator:
    """Resume at a persisted requirements handoff without rerunning analysis."""

    def __init__(
        self,
        target_realizer: TargetRealizer,
        target_context: dict[str, Any] | None = None,
    ) -> None:
        self.target_realizer = target_realizer
        self.target_context = deepcopy(target_context or {})

    def realize(
        self,
        source_workspace: Path,
        destination: Path,
        *,
        target: str,
        stop_after: str = "application",
    ) -> dict[str, Any]:
        if stop_after not in {"plan", "application"}:
            raise PrototypeError("Requirements realization may stop at plan or application")
        RealizationCoordinator._validate_realizer(target, self.target_realizer)
        source_workspace = source_workspace.resolve()
        destination = destination.resolve()
        if destination.exists():
            raise PrototypeError(f"Realization destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)

        account = self._read_text(
            source_workspace / "analysis" / "theoretical-account.md",
            "TheoreticalAccount",
        )
        intent = self._read_json(
            source_workspace / "representation" / "representation-intent.json",
            "representation intent",
        )
        requirements_markdown = self._read_text(
            source_workspace / "representation" / "representation-requirements.md",
            "representation requirements",
        )
        interface_path = (
            source_workspace / "representation" / "representation-interface.json"
        )
        interface_spec = (
            self._read_json(interface_path, "representation interface")
            if interface_path.is_file()
            else {}
        )
        requirements = RealizationCoordinator._normalize_requirements(
            RequirementsDraft(
                representation_intent=intent,
                requirements_markdown=requirements_markdown,
                observations={"source_kind": "persisted-requirements-workspace"},
                interface_spec=interface_spec,
            )
        )
        intent = requirements.representation_intent
        planning = RealizationCoordinator._planning_request(
            target, account, requirements, self.target_context
        )

        temporary = Path(
            tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent)
        )
        try:
            RealizationCoordinator._write_json(
                temporary / "request.json",
                {
                    "operation": "realize-target",
                    "target": target,
                    "stop_after": stop_after,
                    "realizer_id": self.target_realizer.realizer_id,
                    "source_kind": "persisted-requirements-workspace",
                },
            )
            RealizationCoordinator._write_text(
                temporary / "analysis" / "theoretical-account.md", account
            )
            RealizationCoordinator._write_json(
                temporary / "representation" / "representation-intent.json", intent
            )
            RealizationCoordinator._write_text(
                temporary / "representation" / "representation-requirements.md",
                requirements_markdown,
            )
            RealizationCoordinator._write_json(
                temporary / "representation" / "representation-interface.json",
                interface_spec,
            )

            outcome = _run_target_stages(
                self.target_realizer,
                planning,
                temporary,
                stop_after=stop_after,
            )

            RealizationCoordinator._rebase_json_artifacts(
                temporary, temporary, destination
            )
            temporary.replace(destination)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise

        return {
            "operation": "realize-target",
            "realizer": self.target_realizer.realizer_id,
            "target": target,
            "stop_after": stop_after,
            "completed_stages": list(outcome.completed_stages),
            "contract_validation": outcome.contract_validation,
            "workspace": str(destination),
            "pass": outcome.mechanical_passed,
            "outcome_status": {
                "mechanical_conformance": (
                    "passed" if outcome.mechanical_passed else "failed"
                ),
                "scientific_review": "not_performed",
                "interpretive_authority": "analysis_and_review",
            },
        }

    @staticmethod
    def _read_text(path: Path, label: str) -> str:
        try:
            value = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise PrototypeError(f"Could not read {label}: {exc}") from exc
        if not value.strip():
            raise PrototypeError(f"Persisted {label} is empty")
        return value

    @staticmethod
    def _read_json(path: Path, label: str) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise PrototypeError(f"Could not read {label}: {exc}") from exc
        if not isinstance(value, dict):
            raise PrototypeError(f"Persisted {label} must be an object")
        return value


class AccountRequirementsCoordinator:
    """Form requirements from an existing TheoreticalAccount."""

    def __init__(self, provider: ScientificProvider) -> None:
        self.provider = provider

    def realize(
        self,
        source_workspace: Path,
        destination: Path,
        *,
        presentation_question: str,
        reference_case: str | None = None,
    ) -> dict[str, Any]:
        question = presentation_question.strip()
        if not question:
            raise PrototypeError("Presentation question is empty")
        source_workspace = source_workspace.resolve()
        destination = destination.resolve()
        if destination.exists():
            raise PrototypeError(f"Realization destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        account = RequirementsRealizationCoordinator._read_text(
            source_workspace / "analysis" / "theoretical-account.md",
            "TheoreticalAccount",
        )
        requirements = RealizationCoordinator._normalize_requirements(
            self.provider.formulate_requirements(
                RepresentationFormationRequest(
                    presentation_question=question,
                    reference_case=reference_case,
                ),
                account,
            )
        )

        temporary = Path(
            tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent)
        )
        try:
            RealizationCoordinator._write_json(
                temporary / "request.json",
                {
                    "operation": "realize-account",
                    "provider_id": self.provider.provider_id,
                    "presentation_question": question,
                    "reference_case": reference_case,
                },
            )
            RealizationCoordinator._write_text(
                temporary / "analysis" / "theoretical-account.md", account
            )
            RealizationCoordinator._write_text(
                temporary / "input" / "presentation-question.md", question
            )
            RealizationCoordinator._write_json(
                temporary / "representation" / "representation-intent.json",
                requirements.representation_intent,
            )
            RealizationCoordinator._write_text(
                temporary / "representation" / "representation-requirements.md",
                requirements.requirements_markdown,
            )
            RealizationCoordinator._write_json(
                temporary / "representation" / "representation-interface.json",
                requirements.interface_spec,
            )
            RealizationCoordinator._write_json(
                temporary / "representation" / "observations.json",
                requirements.observations,
            )
            RealizationCoordinator._rebase_json_artifacts(
                temporary, temporary, destination
            )
            temporary.replace(destination)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise

        return {
            "operation": "realize-account",
            "provider": self.provider.provider_id,
            "completed_stages": ["requirements"],
            "workspace": str(destination),
            "pass": True,
            "outcome_status": {
                "mechanical_conformance": "not_evaluated",
                "scientific_review": "not_performed",
                "interpretive_authority": "analysis_and_review",
            },
        }

def _run_target_stages(
    realizer: TargetRealizer,
    planning: TargetPlanningRequest,
    workspace: Path,
    *,
    stop_after: str,
) -> TargetStageOutcome:
    """Run detached target stages under coordinator-owned artifact paths."""

    if stop_after not in {"plan", "application"}:
        raise PrototypeError("Target stages may stop at plan or application")
    RealizationCoordinator._validate_realizer(planning.target, realizer)
    plan = realizer.translate(planning)
    if plan.target != planning.target:
        raise PrototypeError("Target realizer returned a plan for the wrong target")
    if not isinstance(plan.plan, dict) or not plan.plan:
        raise PrototypeError("Target realizer returned an empty plan")
    validate_target_plan(planning, plan.plan)
    RealizationCoordinator._write_json(
        workspace / "targets" / planning.target / "plan.json", plan.plan
    )
    RealizationCoordinator._write_json(
        workspace / "targets" / planning.target / "observations.json",
        plan.observations,
    )
    if stop_after == "plan":
        validation = {
            "status": "plan-contract-validated",
            "plan_contract_id": planning.plan_contract.get("contract_id"),
            "pass": True,
        }
        RealizationCoordinator._write_json(
            workspace / "targets" / planning.target / "contract-validation.json",
            validation,
        )
        return TargetStageOutcome(("plan",), True, validation)

    validate_target_plan_implementation_ready(planning, plan.plan)
    application = realizer.implement(
        TargetImplementationRequest(planning=planning, plan=plan),
        workspace / "application",
    )
    if not isinstance(application.result, dict) or not isinstance(
        application.observations, dict
    ):
        raise PrototypeError("Target realizer returned an invalid application result")
    RealizationCoordinator._write_json(
        workspace / "application" / "result.json", application.result
    )
    RealizationCoordinator._write_json(
        workspace / "application" / "observations.json", application.observations
    )
    validation = validate_target_application(
        planning, plan.plan, application.result, workspace / "application"
    )
    RealizationCoordinator._write_json(
        workspace / "application" / "contract-validation.json", validation
    )
    return TargetStageOutcome(("plan", "application"), validation["pass"], validation)
