"""Internal normalization shared by resumable runtime coordinators."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ..domain import (
    FrameworkError,
    RepresentationIntent,
    RepresentationRequirementsPackage,
)
from ..ports import (
    ApplicationRealizer,
    RequirementsDraft,
    TargetPlanningRequest,
    TargetTranslator,
)


def normalize_requirements(
    requirements: RequirementsDraft,
    *,
    theoretical_account_id: str,
    method_id: str = "",
) -> RepresentationRequirementsPackage:
    """Normalize one provider draft at the representation handoff."""

    if not requirements.requirements_markdown.strip():
        raise FrameworkError("Requirements provider returned empty requirements")
    intent = deepcopy(requirements.representation_intent)
    if not isinstance(intent, dict) or not intent.get("presentation_question"):
        raise FrameworkError("Requirements provider returned no presentation question")
    if not intent.get("pivotal_hypotheses"):
        raise FrameworkError("Requirements provider returned no pivotal hypotheses")
    declared_ids = {
        value
        for value in (intent.get("intent_id"), intent.get("id"))
        if isinstance(value, str) and value.strip()
    }
    if len(declared_ids) > 1:
        raise FrameworkError("Representation intent identity fields disagree")
    if not declared_ids:
        raise FrameworkError("Requirements provider returned no representation intent ID")
    requirements_id = intent.get("requirements_id")
    if not isinstance(requirements_id, str) or not requirements_id.strip():
        raise FrameworkError("Requirements provider returned no requirements ID")
    intent["intent_id"] = next(iter(declared_ids))
    intent["id"] = intent["intent_id"]
    intent["schema_version"] = 2
    declared_account = intent.get("theoretical_account_id")
    if declared_account not in (None, "", theoretical_account_id):
        raise FrameworkError(
            "Requirements provider returned a different theoretical account ID"
        )
    intent["theoretical_account_id"] = theoretical_account_id
    if method_id:
        declared_method = intent.get("method_id")
        if declared_method not in (None, "", method_id):
            raise FrameworkError("Requirements provider returned a different method ID")
        intent["method_id"] = method_id
    interface = normalize_interface(requirements.interface_spec)
    return RepresentationRequirementsPackage(
        intent=RepresentationIntent.from_dict(intent),
        requirements_markdown=requirements.requirements_markdown,
        interface_spec=interface,
    )


def normalize_interface(interface_spec: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(interface_spec, dict):
        raise FrameworkError("Representation interface must be an object")
    normalized = deepcopy(interface_spec)
    for field in ("controls", "anchors", "views", "exports"):
        value = normalized.setdefault(field, [])
        if not isinstance(value, list):
            raise FrameworkError(f"Representation interface {field} must be a list")
    return normalized


def validate_realizer(
    target: str, realizer: TargetTranslator | ApplicationRealizer
) -> None:
    if realizer.target_id != target:
        raise FrameworkError(
            f"Target realizer '{realizer.realizer_id}' serves "
            f"'{realizer.target_id}', not '{target}'"
        )


def planning_request(
    target: str,
    theoretical_account: str,
    requirements: RepresentationRequirementsPackage,
    target_context: dict[str, Any] | None = None,
) -> TargetPlanningRequest:
    context = target_context or {}
    return TargetPlanningRequest(
        target=target,
        theoretical_account=theoretical_account,
        requirements=requirements,
        capability_catalog=deepcopy(context.get("capabilities", {})),
        runtime_observation=deepcopy(context.get("runtime_observation", {})),
        plan_contract=deepcopy(context.get("plan_contract", {})),
        artifact_contract=deepcopy(context.get("artifact_contract", {})),
    )
