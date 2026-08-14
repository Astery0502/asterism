"""Integrated application service over a target-agnostic catalog."""

from __future__ import annotations

import importlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .framework_registry import FrameworkCatalog
from ..domain import (
    FrameworkError,
    RawRealizationRequest,
    ValidationFinding,
    WorkflowStatus,
)
from .orchestration import RealizationCoordinator
from .representation_flow import AccountRequirementsCoordinator
from .review import ScientificReviewCoordinator
from .target_flow import PlanApplicationCoordinator, RequirementsRealizationCoordinator
from ..targets import TargetDefinition


class ScientificRepresentationApp:
    """Application service over framework methods and target definitions."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = (
            Path(root).resolve()
            if root is not None
            else Path(__file__).resolve().parents[3]
        )
        self.catalog = FrameworkCatalog.load(self.root)
        self._target_definitions: dict[str, TargetDefinition] = {}

    def list_cases(self) -> list[dict[str, Any]]:
        return [
            {
                "id": case.case_id,
                "title": case.title,
                "method_id": self.catalog.method.method_id,
                "intent_id": self.catalog.get_intent(case).intent_id,
                "requirements_id": case.requirements.get("id"),
                "targets": sorted(case.target_bindings),
                "planning_targets": sorted(
                    set(self.catalog.targets) - set(case.target_bindings)
                ),
            }
            for case in self.catalog.cases
        ]

    def describe_case(self, case_id: str, target: str | None = None) -> dict[str, Any]:
        """Return the combined compatibility view of both independent phases."""

        case = self.catalog.get_case(case_id)
        target_id = target or self.catalog.default_target
        description = case.to_dict()
        description["method"] = self.catalog.method.to_dict()
        description["representation_intent"] = self.catalog.get_intent(case).to_dict()
        if target is not None or target_id in case.target_bindings:
            target_description = self.describe_target(target_id)
            if target_id in case.target_bindings:
                target_description["case_binding"] = case.target_bindings[target_id]
            description["target"] = target_description
        return description

    def describe_analysis(self, case_id: str) -> dict[str, Any]:
        """Return only the description-to-analysis phase and its handoff."""

        case = self.catalog.get_case(case_id)
        return {
            "phase": self._phase("analysis"),
            "case_id": case.case_id,
            "title": case.title,
            "artifacts": deepcopy(case.analysis),
            "module_id": self._phase("analysis")["module"],
            "output_handoff": deepcopy(self.catalog.method.handoff),
        }

    def describe_representation(
        self, case_id: str, target: str | None = None
    ) -> dict[str, Any]:
        """Return the requirements-to-realization phase without rerunning analysis."""

        case = self.catalog.get_case(case_id)
        result = {
            "phase": self._phase("representation"),
            "case_id": case.case_id,
            "title": case.title,
            "input_handoff": {
                "artifact": self.catalog.method.handoff["artifact"],
                "path": case.analysis["theoretical_account"],
            },
            "artifacts": deepcopy(case.representation),
            "representation_intent": self.catalog.get_intent(case).to_dict(),
            "requirements": deepcopy(case.requirements),
            "interface": deepcopy(case.interface),
        }
        if target is not None:
            target_description = self.describe_target(target)
            if target in case.target_bindings:
                target_description["case_binding"] = case.target_bindings[target]
            result["target"] = target_description
        return result

    def describe_method(self) -> dict[str, Any]:
        """Return the target-agnostic module and handoff topology."""

        return self.catalog.method.to_dict()

    def list_targets(self) -> list[dict[str, Any]]:
        return [self.describe_target(target) for target in sorted(self.catalog.targets)]

    def describe_target(self, target: str) -> dict[str, Any]:
        record = self.catalog.target_record(target)
        definition = self._target_definition(target)
        result = definition.describe()
        result["definition"] = record["definition"]
        result["definition_record"] = record["definition_record"]
        result["realized_cases"] = [
            case.case_id for case in self.catalog.cases if target in case.target_bindings
        ]
        return result

    def doctor(self, target: str | None = None) -> dict[str, Any]:
        target_id = target or self.catalog.default_target
        return {
            "application_id": self.catalog.application_id,
            "application_version": self.catalog.application_version,
            "framework_root": str(self.root),
            "target": self._target_definition(target_id).observe_runtime(),
        }

    def validate(
        self,
        selector: str = "all",
        *,
        target: str | None = None,
        structural_only: bool = False,
    ) -> dict[str, Any]:
        cases = self.catalog.select_cases(selector)
        selected_ids = {case.case_id for case in cases}
        target_id = target or self.catalog.default_target
        findings = [
            finding
            for finding in self.catalog.validate()
            if finding.case_id is None or finding.case_id in selected_ids
        ]
        target_results: list[dict[str, Any]] = []
        if not structural_only and cases:
            raise FrameworkError(
                "Recorded-case target validation requires a consumer-owned "
                "workspace validator; target definitions do not execute cases"
            )

        return self._validation_result(
            selector=selector,
            target=target_id,
            structural_only=structural_only,
            findings=findings,
            target_results=target_results,
        )

    def test(self, selector: str = "all", *, target: str | None = None) -> dict[str, Any]:
        cases = self.catalog.select_cases(selector)
        target_id = target or self.catalog.default_target
        if cases:
            raise FrameworkError(
                "Recorded-case testing requires a consumer-injected realizer; "
                "target definitions do not execute cases"
            )
        results: list[dict[str, Any]] = []
        for case, result in zip(cases, results, strict=True):
            result["method_id"] = self.catalog.method.method_id
            result["intent_id"] = self.catalog.get_intent(case).intent_id
            result["status"] = WorkflowStatus(
                mechanical_conformance=(
                    "passed" if result.get("pass") is True else "failed"
                )
            ).to_dict()
        passed = all(result.get("pass") is True for result in results)
        return {
            "operation": "test",
            "selector": selector,
            "target": target_id,
            "case_count": len(results),
            "pass": passed,
            "status": WorkflowStatus(
                mechanical_conformance="passed" if passed else "failed"
            ).to_dict(),
            "results": results,
        }

    def build(
        self,
        selector: str = "all",
        *,
        target: str | None = None,
        output_root: str | Path | None = None,
        recompute_data: bool = False,
    ) -> dict[str, Any]:
        cases = self.catalog.select_cases(selector)
        target_id = target or self.catalog.default_target
        if cases:
            raise FrameworkError(
                "Recorded-case builds require a consumer-injected realizer; "
                "target definitions do not build applications"
            )
        destination = (
            Path(output_root).resolve()
            if output_root is not None
            else (self.root / "work").resolve()
        )
        destination.mkdir(parents=True, exist_ok=True)
        results: list[dict[str, Any]] = []
        passed = all(result.get("pass") is True for result in results)
        for case, result in zip(cases, results, strict=True):
            result["method_id"] = self.catalog.method.method_id
            result["intent_id"] = self.catalog.get_intent(case).intent_id
            result["status"] = WorkflowStatus(
                mechanical_conformance=(
                    "passed" if result.get("pass") is True else "failed"
                )
            ).to_dict()
        return {
            "operation": "build",
            "selector": selector,
            "target": target_id,
            "output_root": str(destination),
            "case_count": len(results),
            "pass": passed,
            "status": WorkflowStatus(
                mechanical_conformance="passed" if passed else "failed"
            ).to_dict(),
            "results": results,
        }

    def realize(
        self,
        raw_input: str | Path,
        direction: str | None,
        destination: str | Path,
        *,
        provider: str,
        realizer: str | None = None,
        reviewer: str | None = None,
        target: str | None = None,
        stop_after: str = "application",
        analysis_question: str | None = None,
        presentation_question: str | None = None,
    ) -> dict[str, Any]:
        """Run raw input through the requested canonical workflow boundary."""

        provider_instance = self._load_extension(provider, "scientific provider")
        target_id = target or str(
            self.catalog.method.realization_branch.get(
                "default_target", self.catalog.default_target
            )
        )
        needs_target_stages = stop_after in {
            "target_translation",
            "application",
            "scientific_review",
        }
        realizer_instance = (
            self._load_extension(realizer, "target realizer")
            if realizer is not None and needs_target_stages
            else None
        )
        if needs_target_stages and realizer_instance is None:
            raise FrameworkError(
                "Target realization requires an injected target realizer"
            )
        reviewer_instance = (
            self._load_extension(reviewer, "scientific reviewer")
            if reviewer is not None and stop_after == "scientific_review"
            else None
        )
        if stop_after == "scientific_review" and reviewer_instance is None:
            raise FrameworkError(
                "Scientific review requires an injected scientific reviewer"
            )
        request = RawRealizationRequest(
            raw_input=Path(raw_input).resolve(),
            direction=(direction or ""),
            target=target_id,
            stop_after=stop_after,
            analysis_question=analysis_question,
            presentation_question=presentation_question,
        )
        target_context = (
            self._target_planning_context(target_id)
            if realizer_instance is not None
            else None
        )
        result = RealizationCoordinator(
            provider_instance,
            realizer_instance,
            target_context,
            reviewer=reviewer_instance,
            method_id=self.catalog.method.method_id,
        ).realize(
            request, Path(destination)
        )
        if realizer is not None and not needs_target_stages:
            result["realizer"] = "not_invoked"
            result["requested_realizer"] = realizer
        return result

    def realize_account(
        self,
        source_workspace: str | Path,
        destination: str | Path,
        *,
        presentation_direction: str = "",
        presentation_question: str | None = None,
        provider: str,
    ) -> dict[str, Any]:
        """Form requirements from an existing TheoreticalAccount."""

        provider_instance = self._load_extension(provider, "scientific provider")
        return AccountRequirementsCoordinator(
            provider_instance, method_id=self.catalog.method.method_id
        ).realize(
            Path(source_workspace),
            Path(destination),
            presentation_direction=presentation_direction,
            presentation_question=presentation_question,
        )

    def realize_requirements(
        self,
        source_workspace: str | Path,
        destination: str | Path,
        *,
        target: str,
        realizer: str,
        stop_after: str = "application",
    ) -> dict[str, Any]:
        """Resume from persisted requirements through a selected target realizer."""

        self.catalog.target_record(target)
        realizer_instance = self._load_extension(realizer, "target realizer")
        return RequirementsRealizationCoordinator(
            realizer_instance,
            self._target_planning_context(target),
            method_id=self.catalog.method.method_id,
        ).realize(
            Path(source_workspace),
            Path(destination),
            target=target,
            stop_after=stop_after,
        )

    def review_application(
        self,
        source_workspace: str | Path,
        destination: str | Path,
        *,
        target: str,
        reviewer: str,
    ) -> dict[str, Any]:
        """Resume at scientific review without rerunning implementation."""

        self.catalog.target_record(target)
        reviewer_instance = self._load_extension(reviewer, "scientific reviewer")
        return ScientificReviewCoordinator(reviewer_instance).review(
            Path(source_workspace), Path(destination), target=target
        )

    def realize_plan(
        self,
        source_workspace: str | Path,
        destination: str | Path,
        *,
        target: str,
        realizer: str,
    ) -> dict[str, Any]:
        """Resume application conformance from a persisted native plan."""

        self.catalog.target_record(target)
        realizer_instance = self._load_extension(realizer, "target realizer")
        return PlanApplicationCoordinator(
            realizer_instance,
            self._target_planning_context(target),
            method_id=self.catalog.method.method_id,
        ).realize(
            Path(source_workspace), Path(destination), target=target
        )

    def _target_definition(self, target_id: str) -> TargetDefinition:
        if target_id not in self._target_definitions:
            definition_reference, definition_record = self.catalog.target_definition(
                target_id
            )
            try:
                module_name, class_name = definition_reference.split(":", 1)
                definition_class = getattr(
                    importlib.import_module(module_name), class_name
                )
            except (ValueError, ImportError, AttributeError) as exc:
                raise FrameworkError(
                    "Could not load target definition "
                    f"'{definition_reference}' for target '{target_id}'"
                ) from exc
            definition = definition_class(self.root, definition_record)
            if definition.target_id != target_id:
                raise FrameworkError(
                    f"Target definition '{definition_reference}' serves "
                    f"'{definition.target_id}', not '{target_id}'"
                )
            if not callable(getattr(definition, "describe", None)) or not callable(
                getattr(definition, "observe_runtime", None)
            ):
                raise FrameworkError(
                    f"Target definition '{definition_reference}' is incomplete"
                )
            self._target_definitions[target_id] = definition
        return self._target_definitions[target_id]

    def _load_extension(self, reference: str, label: str) -> Any:
        try:
            module_name, class_name = reference.split(":", 1)
            extension_class = getattr(importlib.import_module(module_name), class_name)
            return extension_class(self)
        except (ValueError, ImportError, AttributeError, TypeError) as exc:
            raise FrameworkError(f"Could not load {label} '{reference}'") from exc

    def _target_planning_context(self, target: str) -> dict[str, Any]:
        definition = self._target_definition(target)
        description = definition.describe()
        runtime = description.get("runtime")
        if runtime is None:
            runtime = definition.observe_runtime()
        return {
            "capabilities": description.get("capabilities", {}),
            "runtime_observation": runtime,
            "plan_contract": description.get("plan_contract", {}),
            "artifact_contract": description.get("artifact_contract", {}),
        }

    def _phase(self, phase_id: str) -> dict[str, Any]:
        stage = self.catalog.architecture.stage(phase_id)
        return {
            "id": stage.stage_id,
            "module": stage.module_id,
            "inputs": list(stage.inputs),
            "outputs": list(stage.outputs),
            "authority": stage.authority,
        }

    @staticmethod
    def _validation_result(
        *,
        selector: str,
        target: str,
        structural_only: bool,
        findings: list[ValidationFinding],
        target_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        errors = [finding for finding in findings if finding.is_error]
        passed = not errors
        return {
            "operation": "validate",
            "selector": selector,
            "target": target,
            "structural_only": structural_only,
            "pass": passed,
            "status": WorkflowStatus(
                structural_validation="passed" if passed else "failed"
            ).to_dict(),
            "error_count": len(errors),
            "warning_count": sum(finding.severity == "warning" for finding in findings),
            "findings": [finding.to_dict() for finding in findings],
            "target_results": target_results,
        }
