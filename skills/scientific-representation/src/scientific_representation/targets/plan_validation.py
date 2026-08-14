"""Target-neutral plan envelope, identity, and readiness validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..domain import FrameworkError
from ..ports import TargetPlanningRequest
from .traceability import pivotal_requirement_ids, target_profile_id
from .validation_support import load_validation_extension


def validate_target_plan(
    planning: TargetPlanningRequest, plan: dict[str, Any]
) -> None:
    """Validate the common plan envelope, then delegate target semantics."""

    contract = planning.plan_contract
    if not isinstance(contract, dict) or not contract.get("contract_id"):
        raise FrameworkError("Target realizer has no declared plan contract")
    required_fields = contract.get("required_fields")
    if not isinstance(required_fields, list) or not all(
        isinstance(field, str) and field for field in required_fields
    ):
        raise FrameworkError("Target plan contract has invalid required fields")
    missing = [field for field in required_fields if field not in plan]
    if missing:
        raise FrameworkError(f"Target plan is missing required fields: {missing}")
    if plan.get("schema_version") != contract.get("plan_schema_version"):
        raise FrameworkError("Target plan schema version does not match its contract")
    empty = [
        field for field in contract.get("required_nonempty_fields", []) if not plan.get(field)
    ]
    if empty:
        raise FrameworkError(f"Target plan has empty required fields: {empty}")
    _validate_declared_shapes(contract, plan)

    if plan.get("target") != planning.target:
        raise FrameworkError("Target plan identity does not match the selected target")
    if plan.get("representation_intent_id") != planning.representation_intent_id:
        raise FrameworkError("Target plan and representation intent IDs differ")
    if plan.get("requirements_id") != planning.requirements_id:
        raise FrameworkError("Target plan and requirements IDs differ")
    if plan.get("interface") != planning.interface_spec:
        raise FrameworkError(
            "Target plan interface snapshot differs from the accepted requirements interface"
        )

    profiles = {
        item.get("id"): item
        for item in planning.capability_catalog.get("profiles", [])
        if isinstance(item, dict) and item.get("id")
    }
    profile_id = target_profile_id(planning, plan)
    if profile_id not in profiles:
        raise FrameworkError(
            f"Target plan selects an unknown capability profile: {profile_id}"
        )

    inventory = plan.get("artifact_inventory", [])
    if len(inventory) != len(set(inventory)):
        raise FrameworkError("Target plan artifact inventory contains duplicates")
    for relative in inventory:
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise FrameworkError(
                f"Target plan artifact path must remain relative: {relative}"
            )

    coverage = plan.get("requirement_capability_coverage", [])
    coverage_keys = [
        (
            record["requirement_id"],
            record["capability_domain"],
            record["capability"],
        )
        for record in coverage
    ]
    if len(coverage_keys) != len(set(coverage_keys)):
        raise FrameworkError("Target plan requirement coverage entries are not unique")
    missing_coverage = sorted(
        pivotal_requirement_ids(planning)
        - {record["requirement_id"] for record in coverage}
    )
    if missing_coverage:
        raise FrameworkError(
            f"Target plan does not cover pivotal requirements: {missing_coverage}"
        )
    allowed_statuses = set(contract.get("allowed_coverage_statuses", []))
    invalid_statuses = [
        record.get("status")
        for record in coverage
        if record.get("status") not in allowed_statuses
    ]
    if invalid_statuses:
        raise FrameworkError(
            f"Target plan has invalid coverage statuses: {invalid_statuses}"
        )

    dependencies = plan.get("dependencies", [])
    dependency_names = [record["name"] for record in dependencies]
    if len(dependency_names) != len(set(dependency_names)):
        raise FrameworkError("Target plan dependency names are not unique")

    extension = load_validation_extension(contract, "validate_target_plan")
    extension.validate_target_plan(planning, plan, profiles[profile_id])


def validate_target_plan_implementation_ready(
    planning: TargetPlanningRequest, plan: dict[str, Any]
) -> None:
    """Block implementation only for explicitly unmet pivotal obligations."""

    pivotal = pivotal_requirement_ids(planning)
    explicitly_unmet = {
        record["requirement_id"]
        for record in plan.get("requirement_capability_coverage", [])
        if record.get("requirement_id") in pivotal and record.get("status") == "unmet"
    }
    declared_unmet = {
        requirement_id
        for requirement_id in plan.get("unmet_requirements", [])
        if requirement_id in pivotal
    }
    unresolved = sorted(explicitly_unmet | declared_unmet)
    if unresolved:
        raise FrameworkError(
            "Target plan cannot be implemented with unmet pivotal requirements: "
            f"{unresolved}"
        )


def _validate_declared_shapes(
    contract: dict[str, Any], plan: dict[str, Any]
) -> None:
    for field, fields in contract.get("object_fields", {}).items():
        value = plan.get(field)
        if not isinstance(value, dict) or any(name not in value for name in fields):
            raise FrameworkError(f"Target plan object field is incomplete: {field}")
    for field, fields in contract.get("record_list_fields", {}).items():
        value = plan.get(field)
        if not isinstance(value, list) or not all(
            isinstance(record, dict)
            and all(
                isinstance(record.get(name), str) and record[name]
                for name in fields
            )
            for record in value
        ):
            raise FrameworkError(f"Target plan record list is incomplete: {field}")
    for field in contract.get("string_list_fields", []):
        value = plan.get(field)
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item for item in value
        ):
            raise FrameworkError(f"Target plan string list is invalid: {field}")
