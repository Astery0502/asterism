"""Tool-agnostic catalog and requirements-layer validation."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

from ..domain import FrameworkError, MethodSpec, RepresentationIntent, ValidationFinding
from .architecture import FrameworkArchitecture
from .case_registry import CaseSpec


def resolve_relative(root: Path, value: str, *, label: str = "path") -> Path:
    """Resolve a manifest path while keeping it inside the framework root."""

    candidate = Path(value)
    if candidate.is_absolute():
        raise FrameworkError(f"{label} must be relative: {value}")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise FrameworkError(f"{label} leaves the framework root: {value}") from exc
    return resolved


class FrameworkCatalog:
    """Immutable view of the portable, target-agnostic case catalog."""

    def __init__(self, root: Path, raw: dict[str, Any]) -> None:
        self.root = root.resolve()
        self.schema_version = raw.get("schema_version")
        self.application_id = str(raw.get("application_id", ""))
        self.application_version = str(raw.get("application_version", ""))
        self.compatibility_contract = str(raw.get("compatibility_contract", ""))
        self.pipeline_reference = deepcopy(raw.get("pipeline", {}))
        self.architecture = FrameworkArchitecture.load(self.root)
        method_record = raw.get("method", {})
        if not isinstance(method_record, dict):
            raise FrameworkError("framework.json field 'method' must be an object")
        self.method_reference = deepcopy(method_record)
        self.method = self._load_method()
        self.default_target = str(raw.get("default_target", ""))
        self.targets = deepcopy(raw.get("targets", {}))
        self.modules = deepcopy(raw.get("modules", {}))
        self.case_catalog_reference = raw.get("case_catalog")
        raw_cases = self._load_cases(raw)
        if not isinstance(raw_cases, list):
            raise FrameworkError("Case catalog field 'cases' must be a list")
        self.cases = tuple(CaseSpec.from_dict(item) for item in raw_cases)
        self._cases_by_id = {case.case_id: case for case in self.cases}
        self._intent_cache: dict[str, RepresentationIntent] = {}

    @classmethod
    def load(cls, root: Path) -> "FrameworkCatalog":
        manifest_path = root.resolve() / "framework.json"
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise FrameworkError(f"Framework manifest not found: {manifest_path}") from exc
        except json.JSONDecodeError as exc:
            raise FrameworkError(f"Invalid framework manifest: {exc}") from exc
        if not isinstance(raw, dict):
            raise FrameworkError("framework.json must contain a JSON object")
        return cls(root, raw)

    def get_case(self, case_id: str) -> CaseSpec:
        try:
            return self._cases_by_id[case_id]
        except KeyError as exc:
            choices = ", ".join(sorted(self._cases_by_id))
            raise FrameworkError(f"Unknown case '{case_id}'. Available cases: {choices}") from exc

    def get_intent(self, case: CaseSpec | str) -> RepresentationIntent:
        spec = self.get_case(case) if isinstance(case, str) else case
        if spec.case_id not in self._intent_cache:
            relative = spec.requirements.get("intent")
            if not relative:
                raise FrameworkError(f"Case '{spec.case_id}' has no representation intent")
            path = resolve_relative(self.root, relative, label=f"{spec.case_id} intent")
            self._intent_cache[spec.case_id] = RepresentationIntent.from_dict(
                self._load_json(path, label=f"{spec.case_id} representation intent")
            )
        return self._intent_cache[spec.case_id]

    def select_cases(self, selector: str) -> tuple[CaseSpec, ...]:
        return self.cases if selector == "all" else (self.get_case(selector),)

    def target_definition(self, target: str) -> tuple[str, Path]:
        record = self.target_record(target)
        try:
            definition = str(record["definition"])
            definition_record = resolve_relative(
                self.root,
                str(record["definition_record"]),
                label=f"{target} definition record",
            )
        except (KeyError, TypeError) as exc:
            raise FrameworkError(f"Target '{target}' is not configured") from exc
        return definition, definition_record

    def target_record(self, target: str) -> dict[str, Any]:
        try:
            record = self.targets[target]
        except KeyError as exc:
            choices = ", ".join(sorted(self.targets))
            raise FrameworkError(
                f"Target '{target}' is not configured. Available targets: {choices}"
            ) from exc
        if not isinstance(record, dict):
            raise FrameworkError(f"Target '{target}' configuration must be an object")
        return deepcopy(record)

    def validate(self) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        if self.schema_version != 2:
            findings.append(
                ValidationFinding("error", "catalog.schema", f"Unsupported schema: {self.schema_version}")
            )
        if not self.application_id:
            findings.append(
                ValidationFinding("error", "catalog.application-id", "Application ID is missing")
            )
        ids = [case.case_id for case in self.cases]
        if len(ids) != len(set(ids)):
            findings.append(
                ValidationFinding("error", "catalog.case-id", "Case IDs are not unique")
            )
        if self.default_target not in self.targets:
            findings.append(
                ValidationFinding(
                    "error", "catalog.default-target", "Default target is not configured"
                )
            )
        try:
            declared_pipeline = self.pipeline_reference.get("path")
            if declared_pipeline != self.method.pipeline:
                raise FrameworkError(
                    "Framework and method records reference different pipelines"
                )
            module_ids = tuple(
                stage.module_id for stage in self.architecture.stages
            )
            referenced_modules = {
                self.method.handoff.get("producer"),
                self.method.handoff.get("consumer"),
                self.method.realization_branch.get("module"),
                *(mode.get("start_module") for mode in self.method.entry_modes),
            }
            unknown_modules = sorted(
                module_id
                for module_id in referenced_modules
                if module_id not in module_ids
            )
            if unknown_modules:
                raise FrameworkError(
                    f"Method references unknown pipeline modules: {unknown_modules}"
                )
        except (FrameworkError, AttributeError, TypeError) as exc:
            findings.append(
                ValidationFinding("error", "pipeline.topology", str(exc))
            )
        module_ids = tuple(stage.module_id for stage in self.architecture.stages)
        if not isinstance(self.modules, dict):
            findings.append(
                ValidationFinding(
                    "error",
                    "catalog.modules",
                    "Framework module registry must be an object",
                )
            )
        else:
            for module_id in module_ids:
                record = self.modules.get(module_id)
                if not isinstance(record, dict):
                    findings.append(
                        ValidationFinding(
                            "error",
                            "catalog.module",
                            f"Method module is absent from the registry: {module_id}",
                        )
                    )
                    continue
                for field in ("guide", "contract"):
                    try:
                        path = resolve_relative(
                            self.root,
                            str(record[field]),
                            label=f"{module_id} {field}",
                        )
                        if not path.is_file():
                            raise FrameworkError(f"Module resource is missing: {record[field]}")
                    except (FrameworkError, KeyError, TypeError) as exc:
                        findings.append(
                            ValidationFinding("error", "catalog.module-resource", str(exc))
                        )
        entry_mode_ids = [mode["id"] for mode in self.method.entry_modes]
        if len(entry_mode_ids) != len(set(entry_mode_ids)):
            findings.append(
                ValidationFinding(
                    "error",
                    "method.entry-modes",
                    "Method entry-mode IDs are not unique",
                )
            )
        if self.method.realization_branch.get("default_target") not in self.targets:
            findings.append(
                ValidationFinding(
                    "error",
                    "method.realization-branch",
                    "The realization branch default target is not configured",
                )
            )

        for target, record in self.targets.items():
            try:
                definition_reference = record["definition"]
                if (
                    not isinstance(definition_reference, str)
                    or ":" not in definition_reference
                ):
                    raise FrameworkError(
                        f"Target definition reference is invalid: {definition_reference!r}"
                    )
                definition_record = resolve_relative(
                    self.root,
                    str(record["definition_record"]),
                    label=f"{target} definition record",
                )
                if not definition_record.is_file():
                    findings.append(
                        ValidationFinding(
                            "error",
                            "catalog.target-definition",
                            "Target definition record is missing: "
                            f"{record['definition_record']}",
                            target=target,
                        )
                    )
            except (FrameworkError, KeyError, TypeError) as exc:
                findings.append(
                    ValidationFinding(
                        "error", "catalog.target-definition", str(exc), target=target
                    )
                )

        for case in self.cases:
            findings.extend(self._validate_case(case))
        return findings

    def _validate_case(self, case: CaseSpec) -> Iterable[ValidationFinding]:
        findings: list[ValidationFinding] = []
        paths = {f"analysis.{name}": value for name, value in case.analysis.items()}
        paths.update(
            {f"representation.{name}": value for name, value in case.representation.items()}
        )
        requirements_path = case.requirements.get("path")
        intent_path = case.requirements.get("intent")
        if requirements_path:
            paths["requirements.path"] = requirements_path
        else:
            findings.append(
                ValidationFinding(
                    "error", "case.requirements-path", "Requirements path is missing", case.case_id
                )
            )
        if intent_path:
            paths["requirements.intent"] = intent_path
        else:
            findings.append(
                ValidationFinding(
                    "error", "case.intent-path", "Representation intent path is missing", case.case_id
                )
            )
        for target, value in case.target_bindings.items():
            paths[f"target_bindings.{target}"] = value

        for label, value in paths.items():
            try:
                path = resolve_relative(self.root, value, label=f"{case.case_id} {label}")
                if not path.is_file():
                    findings.append(
                        ValidationFinding(
                            "error",
                            "case.file-missing",
                            f"Missing {label}: {value}",
                            case.case_id,
                        )
                    )
            except FrameworkError as exc:
                findings.append(
                    ValidationFinding(
                        "error", "case.path", str(exc), case.case_id
                    )
                )

        requirements_id = case.requirements.get("id")
        if not requirements_id:
            findings.append(
                ValidationFinding(
                    "error", "case.requirements-id", "Requirements ID is missing", case.case_id
                )
            )

        if intent_path:
            findings.extend(self._validate_intent(case))

        return findings

    def _load_method(self) -> MethodSpec:
        try:
            path_value = str(self.method_reference["path"])
        except (KeyError, TypeError) as exc:
            raise FrameworkError("Catalog method path is missing") from exc
        path = resolve_relative(self.root, path_value, label="method record")
        return MethodSpec.from_dict(self._load_json(path, label="method coordination record"))

    def _load_cases(self, framework_record: dict[str, Any]) -> list[Any]:
        """Load upstream cases separately from the reusable framework manifest."""

        if self.case_catalog_reference is None:
            return deepcopy(framework_record.get("cases", []))
        if not isinstance(self.case_catalog_reference, str):
            raise FrameworkError("framework.json field 'case_catalog' must be a path")
        path = resolve_relative(
            self.root,
            self.case_catalog_reference,
            label="case catalog",
        )
        record = self._load_json(path, label="case catalog")
        if record.get("schema_version") != 1:
            raise FrameworkError("Case catalog must use schema version 1")
        return deepcopy(record.get("cases", []))

    def _validate_intent(self, case: CaseSpec) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []

        def error(code: str, message: str) -> None:
            findings.append(ValidationFinding("error", code, message, case.case_id))

        try:
            intent = self.get_intent(case)
        except FrameworkError as exc:
            error("case.intent-read", str(exc))
            return findings
        if intent.method_id != self.method.method_id:
            error("case.intent-method", "Intent and philosophical method IDs differ")
        if intent.case_id != case.case_id:
            error("case.intent-case", "Intent and catalog case IDs differ")
        if intent.requirements_id != case.requirements.get("id"):
            error("case.intent-requirements", "Intent and requirements IDs differ")
        if not intent.presentation_question.strip():
            error("case.presentation-question", "Presentation question is empty")

        return findings

    @staticmethod
    def _load_json(path: Path, *, label: str) -> dict[str, Any]:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise FrameworkError(f"{label} not found: {path}") from exc
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise FrameworkError(f"Invalid {label}: {exc}") from exc
        if not isinstance(raw, dict):
            raise FrameworkError(f"{label} must contain a JSON object")
        return raw
