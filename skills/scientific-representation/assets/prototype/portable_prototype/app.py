"""Integrated application service over a target-agnostic catalog."""

from __future__ import annotations

import importlib
import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

from .catalog import CaseSpec, PrototypeCatalog
from .models import PrototypeError, RawRealizationRequest, ValidationFinding
from .workflow import (
    AccountRequirementsCoordinator,
    RealizationCoordinator,
    RequirementsRealizationCoordinator,
)


class PrototypeApp:
    """One facade for discovery, validation, testing, building, and migration."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = (
            Path(root).resolve()
            if root is not None
            else Path(__file__).resolve().parents[1]
        )
        self.catalog = PrototypeCatalog.load(self.root)
        self._adapters: dict[str, Any] = {}

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
            description["target"] = self._adapter(target_id).describe_case(case)
        return description

    def describe_analysis(self, case_id: str) -> dict[str, Any]:
        """Return only the description-to-analysis phase and its handoff."""

        case = self.catalog.get_case(case_id)
        return {
            "phase": self._phase("analysis"),
            "case_id": case.case_id,
            "title": case.title,
            "artifacts": deepcopy(case.analysis),
            "inquiry_cycle": deepcopy(list(self.catalog.method.inquiry_cycle)),
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
            result["target"] = self._adapter(target).describe_case(case)
        return result

    def describe_method(self) -> dict[str, Any]:
        """Return the target-agnostic philosophical method used by every case."""

        return self.catalog.method.to_dict()

    def list_targets(self) -> list[dict[str, Any]]:
        return [self.describe_target(target) for target in sorted(self.catalog.targets)]

    def describe_target(self, target: str) -> dict[str, Any]:
        record = self.catalog.target_record(target)
        adapter = self._adapter(target)
        describe = getattr(adapter, "describe_target", None)
        if callable(describe):
            result = describe()
        else:
            runtime = adapter.doctor()
            result = {
                "id": target,
                "display_name": runtime.get("display_name"),
                "runtime": runtime,
            }
        result["adapter"] = record["adapter"]
        result["descriptor"] = record["descriptor"]
        result["realized_cases"] = [
            case.case_id for case in self.catalog.cases if target in case.target_bindings
        ]
        return result

    def doctor(self, target: str | None = None) -> dict[str, Any]:
        target_id = target or self.catalog.default_target
        return {
            "application_id": self.catalog.application_id,
            "application_version": self.catalog.application_version,
            "prototype_root": str(self.root),
            "target": self._adapter(target_id).doctor(),
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
        if not structural_only:
            adapter = self._adapter(target_id)
            for case in cases:
                result = adapter.validate_case(case, runtime=True)
                findings.extend(result.pop("findings"))
                target_results.append(result)

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
        adapter = self._adapter(target_id)
        results = [adapter.test_case(case) for case in cases]
        for case, result in zip(cases, results, strict=True):
            result["method_id"] = self.catalog.method.method_id
            result["intent_id"] = self.catalog.get_intent(case).intent_id
            result["outcome_status"] = self._outcome_status(result.get("pass") is True)
        passed = all(result.get("pass") is True for result in results)
        return {
            "operation": "test",
            "selector": selector,
            "target": target_id,
            "case_count": len(results),
            "pass": passed,
            "outcome_status": self._outcome_status(passed),
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
        adapter = self._adapter(target_id)
        destination = (
            Path(output_root).resolve()
            if output_root is not None
            else (self.root / "work").resolve()
        )
        destination.mkdir(parents=True, exist_ok=True)
        results = [
            adapter.build_case(case, destination, recompute_data=recompute_data)
            for case in cases
        ]
        passed = all(result.get("pass") is True for result in results)
        for case, result in zip(cases, results, strict=True):
            result["method_id"] = self.catalog.method.method_id
            result["intent_id"] = self.catalog.get_intent(case).intent_id
            result["outcome_status"] = self._outcome_status(result.get("pass") is True)
        return {
            "operation": "build",
            "selector": selector,
            "target": target_id,
            "output_root": str(destination),
            "case_count": len(results),
            "pass": passed,
            "outcome_status": self._outcome_status(passed),
            "results": results,
        }

    def bundle(self, destination: str | Path, *, profile: str = "runtime") -> dict[str, Any]:
        if profile not in {"source", "runtime", "archive"}:
            raise PrototypeError(f"Unknown bundle profile: {profile}")
        destination_path = Path(destination).resolve()
        if destination_path.exists():
            raise PrototypeError(f"Bundle destination already exists: {destination_path}")
        try:
            destination_path.relative_to(self.root)
        except ValueError:
            pass
        else:
            raise PrototypeError("Bundle destination must be outside the prototype being copied")

        excluded: set[Path] = set()
        if profile in {"source", "runtime"}:
            excluded.add((self.root / "work").resolve())
        if profile == "source":
            for target_id in self.catalog.targets:
                excluded.update(
                    self._adapter(target_id).bundle_excludes(profile, self.catalog.cases)
                )

        def ignore(directory: str, names: list[str]) -> set[str]:
            base = Path(directory).resolve()
            skipped: set[str] = set()
            for name in names:
                path = (base / name).resolve()
                if name == "__pycache__" or name.endswith((".pyc", ".pyo")):
                    skipped.add(name)
                elif any(path == item or item in path.parents for item in excluded):
                    skipped.add(name)
            return skipped

        shutil.copytree(self.root, destination_path, ignore=ignore)
        bundle_record = {
            "schema_version": 1,
            "application_id": self.catalog.application_id,
            "application_version": self.catalog.application_version,
            "profile": profile,
        }
        (destination_path / "BUNDLE.json").write_text(
            json.dumps(bundle_record, indent=2) + "\n", encoding="utf-8"
        )
        files = [path for path in destination_path.rglob("*") if path.is_file()]
        return {
            "operation": "bundle",
            "pass": True,
            "profile": profile,
            "destination": str(destination_path),
            "file_count": len(files),
            "bytes": sum(path.stat().st_size for path in files),
        }

    def realize(
        self,
        raw_input: str | Path,
        direction: str | None,
        destination: str | Path,
        *,
        provider: str,
        realizer: str | None = None,
        reference_case: str | None = None,
        target: str | None = None,
        stop_after: str = "application",
        analysis_question: str | None = None,
        presentation_question: str | None = None,
    ) -> dict[str, Any]:
        """Run both phases through a replaceable provider and persisted handoff."""

        provider_instance = self._load_extension(provider, "realization provider")
        target_id = target or str(
            self.catalog.method.realization_branch.get(
                "default_target", self.catalog.default_target
            )
        )
        needs_target_stages = stop_after == "application"
        realizer_instance = (
            self._load_extension(realizer, "target realizer")
            if realizer is not None and needs_target_stages
            else None
        )
        request = RawRealizationRequest(
            raw_input=Path(raw_input).resolve(),
            direction=(presentation_question or direction or ""),
            target=target_id,
            stop_after=stop_after,
            reference_case=reference_case,
            analysis_question=analysis_question,
            presentation_question=presentation_question,
        )
        target_context = (
            self._target_planning_context(target_id)
            if realizer_instance is not None
            else None
        )
        result = RealizationCoordinator(
            provider_instance, realizer_instance, target_context
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
        presentation_question: str,
        provider: str,
        reference_case: str | None = None,
    ) -> dict[str, Any]:
        """Form requirements from an existing TheoreticalAccount."""

        provider_instance = self._load_extension(provider, "scientific provider")
        return AccountRequirementsCoordinator(provider_instance).realize(
            Path(source_workspace),
            Path(destination),
            presentation_question=presentation_question,
            reference_case=reference_case,
        )

    def realize_requirements(
        self,
        source_workspace: str | Path,
        destination: str | Path,
        *,
        target: str,
        realizer: str,
    ) -> dict[str, Any]:
        """Resume from persisted requirements through a selected target realizer."""

        self.catalog.target_record(target)
        realizer_instance = self._load_extension(realizer, "target realizer")
        return RequirementsRealizationCoordinator(
            realizer_instance, self._target_planning_context(target)
        ).realize(
            Path(source_workspace),
            Path(destination),
            target=target,
            stop_after="application",
        )

    def _adapter(self, target_id: str) -> Any:
        if target_id not in self._adapters:
            adapter_reference, descriptor = self.catalog.target_descriptor(target_id)
            try:
                module_name, class_name = adapter_reference.split(":", 1)
                adapter_class = getattr(importlib.import_module(module_name), class_name)
            except (ValueError, ImportError, AttributeError) as exc:
                raise PrototypeError(
                    f"Could not load adapter '{adapter_reference}' for target '{target_id}'"
                ) from exc
            self._adapters[target_id] = adapter_class(self.root, descriptor)
        return self._adapters[target_id]

    def _load_extension(self, reference: str, label: str) -> Any:
        try:
            module_name, class_name = reference.split(":", 1)
            extension_class = getattr(importlib.import_module(module_name), class_name)
            return extension_class(self)
        except (ValueError, ImportError, AttributeError, TypeError) as exc:
            raise PrototypeError(f"Could not load {label} '{reference}'") from exc

    def _target_planning_context(self, target: str) -> dict[str, Any]:
        adapter = self._adapter(target)
        describe = getattr(adapter, "describe_target", None)
        description = describe() if callable(describe) else {}
        runtime = description.get("runtime")
        if runtime is None:
            runtime = adapter.doctor()
        return {
            "capabilities": description.get("capabilities", {}),
            "runtime_observation": runtime,
            "plan_contract": description.get("plan_contract", {}),
            "artifact_contract": description.get("artifact_contract", {}),
        }

    def _phase(self, phase_id: str) -> dict[str, Any]:
        for phase in self.catalog.method.phases:
            if phase["id"] == phase_id:
                return deepcopy(phase)
        raise PrototypeError(f"Unknown method phase: {phase_id}")

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
            "outcome_status": PrototypeApp._outcome_status(passed),
            "error_count": len(errors),
            "warning_count": sum(finding.severity == "warning" for finding in findings),
            "findings": [finding.to_dict() for finding in findings],
            "target_results": target_results,
        }

    @staticmethod
    def _outcome_status(mechanical_passed: bool) -> dict[str, str]:
        """Keep execution conformance distinct from interpretive judgment."""

        return {
            "mechanical_conformance": "passed" if mechanical_passed else "failed",
            "scientific_review": "not_performed",
            "interpretive_authority": "analysis_and_review",
        }
