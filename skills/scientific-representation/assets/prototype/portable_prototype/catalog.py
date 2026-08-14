"""Tool-agnostic catalog and requirements-layer validation."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .models import MethodSpec, PrototypeError, RepresentationIntent, ValidationFinding


HYPOTHESIS_FIELDS = (
    "id",
    "requirement_refs",
    "theory_anchor",
    "researcher_capability",
    "controlled_contrast",
    "held_fixed",
    "observables",
    "expected_signature",
    "explanatory_bridge",
    "representation",
    "interaction_contract",
    "warrant",
    "review_probe",
)


def resolve_relative(root: Path, value: str, *, label: str = "path") -> Path:
    """Resolve a manifest path while keeping it inside the prototype root."""

    candidate = Path(value)
    if candidate.is_absolute():
        raise PrototypeError(f"{label} must be relative: {value}")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise PrototypeError(f"{label} leaves the prototype root: {value}") from exc
    return resolved


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    title: str
    analysis: dict[str, str]
    representation: dict[str, str]
    requirements: dict[str, str]
    interface: dict[str, Any]
    target_bindings: dict[str, str]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "CaseSpec":
        try:
            return cls(
                case_id=str(raw["id"]),
                title=str(raw["title"]),
                analysis=dict(raw["analysis"]),
                representation=dict(raw["representation"]),
                requirements=dict(raw["requirements"]),
                interface=deepcopy(raw.get("interface", {})),
                target_bindings=dict(raw["target_bindings"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise PrototypeError(f"Invalid case record: {raw!r}") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.case_id,
            "title": self.title,
            "analysis": deepcopy(self.analysis),
            "representation": deepcopy(self.representation),
            "requirements": deepcopy(self.requirements),
            "interface": deepcopy(self.interface),
            "target_bindings": deepcopy(self.target_bindings),
        }


class PrototypeCatalog:
    """Immutable view of the portable, target-agnostic case catalog."""

    def __init__(self, root: Path, raw: dict[str, Any]) -> None:
        self.root = root.resolve()
        self.schema_version = raw.get("schema_version")
        self.application_id = str(raw.get("application_id", ""))
        self.application_version = str(raw.get("application_version", ""))
        self.compatibility_contract = str(raw.get("compatibility_contract", ""))
        method_record = raw.get("method", {})
        if not isinstance(method_record, dict):
            raise PrototypeError("prototype.json field 'method' must be an object")
        self.method_reference = deepcopy(method_record)
        self.method = self._load_method()
        self.default_target = str(raw.get("default_target", ""))
        self.targets = deepcopy(raw.get("targets", {}))
        raw_cases = raw.get("cases", [])
        if not isinstance(raw_cases, list):
            raise PrototypeError("prototype.json field 'cases' must be a list")
        self.cases = tuple(CaseSpec.from_dict(item) for item in raw_cases)
        self._cases_by_id = {case.case_id: case for case in self.cases}
        self._intent_cache: dict[str, RepresentationIntent] = {}

    @classmethod
    def load(cls, root: Path) -> "PrototypeCatalog":
        manifest_path = root.resolve() / "prototype.json"
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise PrototypeError(f"Prototype manifest not found: {manifest_path}") from exc
        except json.JSONDecodeError as exc:
            raise PrototypeError(f"Invalid prototype manifest: {exc}") from exc
        if not isinstance(raw, dict):
            raise PrototypeError("prototype.json must contain a JSON object")
        return cls(root, raw)

    def get_case(self, case_id: str) -> CaseSpec:
        try:
            return self._cases_by_id[case_id]
        except KeyError as exc:
            choices = ", ".join(sorted(self._cases_by_id))
            raise PrototypeError(f"Unknown case '{case_id}'. Available cases: {choices}") from exc

    def get_intent(self, case: CaseSpec | str) -> RepresentationIntent:
        spec = self.get_case(case) if isinstance(case, str) else case
        if spec.case_id not in self._intent_cache:
            relative = spec.requirements.get("intent")
            if not relative:
                raise PrototypeError(f"Case '{spec.case_id}' has no representation intent")
            path = resolve_relative(self.root, relative, label=f"{spec.case_id} intent")
            self._intent_cache[spec.case_id] = RepresentationIntent.from_dict(
                self._load_json(path, label=f"{spec.case_id} representation intent")
            )
        return self._intent_cache[spec.case_id]

    def select_cases(self, selector: str) -> tuple[CaseSpec, ...]:
        return self.cases if selector == "all" else (self.get_case(selector),)

    def target_descriptor(self, target: str) -> tuple[str, Path]:
        record = self.target_record(target)
        try:
            adapter = str(record["adapter"])
            descriptor = resolve_relative(
                self.root, str(record["descriptor"]), label=f"{target} descriptor"
            )
        except (KeyError, TypeError) as exc:
            raise PrototypeError(f"Target '{target}' is not configured") from exc
        return adapter, descriptor

    def target_record(self, target: str) -> dict[str, Any]:
        try:
            record = self.targets[target]
        except KeyError as exc:
            choices = ", ".join(sorted(self.targets))
            raise PrototypeError(
                f"Target '{target}' is not configured. Available targets: {choices}"
            ) from exc
        if not isinstance(record, dict):
            raise PrototypeError(f"Target '{target}' configuration must be an object")
        return deepcopy(record)

    def validate(self) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        if self.schema_version != 1:
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
        if self.method_reference.get("id") != self.method.method_id:
            findings.append(
                ValidationFinding(
                    "error",
                    "method.id",
                    "Catalog and method-record IDs differ",
                )
            )
        stage_ids = [stage["id"] for stage in self.method.inquiry_cycle]
        if len(stage_ids) != len(set(stage_ids)):
            findings.append(
                ValidationFinding("error", "method.inquiry-cycle", "Inquiry stage IDs are not unique")
            )
        if len(self.method.translation_chain) != len(set(self.method.translation_chain)):
            findings.append(
                ValidationFinding(
                    "error", "method.translation-chain", "Translation-chain entries are not unique"
                )
            )
        phase_ids = [phase["id"] for phase in self.method.phases]
        if phase_ids != ["analysis", "representation"]:
            findings.append(
                ValidationFinding(
                    "error",
                    "method.phases",
                    "Method phases must declare analysis followed by representation",
                )
            )
        default_analysis_module = self.method.phases[0].get("default_module")
        if not isinstance(default_analysis_module, str) or not default_analysis_module:
            findings.append(
                ValidationFinding(
                    "error",
                    "method.default-analysis-module",
                    "The analysis phase has no bundled default module",
                )
            )
        else:
            try:
                module_path = resolve_relative(
                    self.root,
                    default_analysis_module,
                    label="default analysis module",
                )
                if not module_path.is_file():
                    findings.append(
                        ValidationFinding(
                            "error",
                            "method.default-analysis-module",
                            f"Default analysis module is missing: {default_analysis_module}",
                        )
                    )
            except PrototypeError as exc:
                findings.append(
                    ValidationFinding(
                        "error", "method.default-analysis-module", str(exc)
                    )
                )
        entry_mode_ids = [mode["id"] for mode in self.method.entry_modes]
        if entry_mode_ids != ["account_available", "analysis_needed"]:
            findings.append(
                ValidationFinding(
                    "error",
                    "method.entry-modes",
                    "Method entry modes must distinguish an available scientific account from input that still needs analysis",
                )
            )
        handoff = self.method.handoff
        if (
            handoff.get("artifact") != "TheoreticalAccount"
            or handoff.get("producer") != "analysis"
            or handoff.get("consumer") != "representation"
        ):
            findings.append(
                ValidationFinding(
                    "error",
                    "method.handoff",
                    "The phase handoff must be TheoreticalAccount from analysis to representation",
                )
            )
        branch = self.method.realization_branch
        if (
            branch.get("resume_artifact") != "RepresentationRequirementsPackage"
            or branch.get("output") != "TargetNativeDecisionPlan"
            or branch.get("default_target") not in self.targets
            or "TargetCapabilityCatalog" not in branch.get("inputs", [])
            or "delivery_connectivity" not in branch.get("selection_basis", [])
        ):
            findings.append(
                ValidationFinding(
                    "error",
                    "method.realization-branch",
                    "The downstream realization branch is incomplete",
                )
            )

        for target, record in self.targets.items():
            try:
                descriptor = resolve_relative(
                    self.root, str(record["descriptor"]), label=f"{target} descriptor"
                )
                if not descriptor.is_file():
                    findings.append(
                        ValidationFinding(
                            "error",
                            "catalog.target-descriptor",
                            f"Target descriptor is missing: {record['descriptor']}",
                            target=target,
                        )
                    )
            except (PrototypeError, KeyError, TypeError) as exc:
                findings.append(
                    ValidationFinding(
                        "error", "catalog.target-descriptor", str(exc), target=target
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
        if set(case.analysis) != {"theoretical_account"}:
            findings.append(
                ValidationFinding(
                    "error",
                    "case.analysis-boundary",
                    "Analysis phase must expose only the TheoreticalAccount handoff",
                    case.case_id,
                )
            )
        if not case.representation.get("presentation_brief"):
            findings.append(
                ValidationFinding(
                    "error",
                    "case.representation-brief",
                    "Representation phase presentation brief is missing",
                    case.case_id,
                )
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
            except PrototypeError as exc:
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
        elif requirements_path:
            try:
                text = resolve_relative(self.root, requirements_path).read_text(encoding="utf-8")
                if requirements_id not in text:
                    findings.append(
                        ValidationFinding(
                            "error",
                            "case.requirements-id",
                            f"Requirements file does not declare {requirements_id}",
                            case.case_id,
                        )
                    )
            except (OSError, UnicodeError, PrototypeError) as exc:
                findings.append(
                    ValidationFinding(
                        "error", "case.requirements-read", str(exc), case.case_id
                    )
                )

        if intent_path:
            findings.extend(
                self._validate_intent(case, requirements_path=requirements_path)
            )

        if not case.interface.get("controls"):
            findings.append(
                ValidationFinding(
                    "warning", "case.controls", "No portable controls are declared", case.case_id
                )
            )
        if not case.interface.get("anchors"):
            findings.append(
                ValidationFinding(
                    "warning", "case.anchors", "No portable anchors are declared", case.case_id
                )
            )
        return findings

    def _load_method(self) -> MethodSpec:
        try:
            path_value = str(self.method_reference["path"])
        except (KeyError, TypeError) as exc:
            raise PrototypeError("Catalog method path is missing") from exc
        path = resolve_relative(self.root, path_value, label="method record")
        return MethodSpec.from_dict(self._load_json(path, label="philosophical method"))

    def _validate_intent(
        self, case: CaseSpec, *, requirements_path: str | None
    ) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []

        def error(code: str, message: str) -> None:
            findings.append(ValidationFinding("error", code, message, case.case_id))

        try:
            intent = self.get_intent(case)
        except PrototypeError as exc:
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

        expected_stages = {stage["id"] for stage in self.method.inquiry_cycle}
        actual_stages = set(intent.inquiry_path)
        missing_stages = sorted(expected_stages - actual_stages)
        if missing_stages:
            error(
                "case.inquiry-path",
                "Inquiry path is missing stages: " + ", ".join(missing_stages),
            )

        hypothesis_ids: list[str] = []
        requirement_text = ""
        if requirements_path:
            try:
                requirement_text = resolve_relative(self.root, requirements_path).read_text(
                    encoding="utf-8"
                )
            except (OSError, UnicodeError, PrototypeError):
                pass
        for index, hypothesis in enumerate(intent.pivotal_hypotheses, start=1):
            if not isinstance(hypothesis, dict):
                error("case.hypothesis-shape", f"Hypothesis {index} is not an object")
                continue
            missing = [field for field in HYPOTHESIS_FIELDS if not hypothesis.get(field)]
            if missing:
                error(
                    "case.hypothesis-fields",
                    f"Hypothesis {index} is missing semantic fields: {', '.join(missing)}",
                )
            hypothesis_id = str(hypothesis.get("id", ""))
            hypothesis_ids.append(hypothesis_id)
            warrant = hypothesis.get("warrant")
            if not isinstance(warrant, dict) or any(
                not warrant.get(field)
                for field in ("evidence_kinds", "supports", "cannot_establish")
            ):
                error("case.hypothesis-warrant", f"Hypothesis {hypothesis_id} has incomplete warrant")
            for requirement_id in hypothesis.get("requirement_refs", []):
                if requirement_text and str(requirement_id) not in requirement_text:
                    error(
                        "case.hypothesis-requirement",
                        f"Hypothesis {hypothesis_id} references undeclared requirement {requirement_id}",
                    )
        if len(hypothesis_ids) != len(set(hypothesis_ids)):
            error("case.hypothesis-id", "Pivotal hypothesis IDs are not unique")
        return findings

    @staticmethod
    def _load_json(path: Path, *, label: str) -> dict[str, Any]:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise PrototypeError(f"{label} not found: {path}") from exc
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise PrototypeError(f"Invalid {label}: {exc}") from exc
        if not isinstance(raw, dict):
            raise PrototypeError(f"{label} must contain a JSON object")
        return raw
