"""Scientific HTML target-definition contract-record validation."""

from __future__ import annotations

import math
from typing import Any

from scientific_representation.domain import FrameworkError
from scientific_representation.ports import TargetPlanningRequest


def validate_contract_records(
    capabilities: dict[str, Any],
    plan_contract: dict[str, Any],
    artifact_contract: dict[str, Any],
    *,
    target_id: str,
) -> None:
    """Validate the identity and profile envelope of bundled target records."""

    profiles = capabilities.get("profiles")
    profile_ids = [
        profile.get("id") for profile in profiles if isinstance(profile, dict)
    ] if isinstance(profiles, list) else []
    if (
        capabilities.get("schema_version") != 1
        or capabilities.get("target_id") != target_id
        or not profile_ids
        or len(profile_ids) != len(set(profile_ids))
        or capabilities.get("default_profile_id") not in profile_ids
    ):
        raise FrameworkError("Scientific HTML capability catalog is invalid")

    verification = capabilities.get("verification_requirements")
    if (
        not isinstance(verification, dict)
        or not isinstance(verification.get("python_packages"), list)
        or not isinstance(verification.get("browser"), bool)
    ):
        raise FrameworkError("Scientific HTML verification requirements are incomplete")

    if (
        plan_contract.get("schema_version") != 1
        or plan_contract.get("contract_id") != "scientific-html-plan-v1"
        or not isinstance(plan_contract.get("validation_extension"), str)
        or not plan_contract["validation_extension"]
    ):
        raise FrameworkError("Scientific HTML plan contract is invalid")
    if (
        artifact_contract.get("schema_version") != 2
        or artifact_contract.get("contract_id") != "scientific-html-artifact-v2"
        or not isinstance(artifact_contract.get("validation_extension"), str)
        or not artifact_contract["validation_extension"]
    ):
        raise FrameworkError("Scientific HTML artifact contract is invalid")


def validate_target_plan(
    planning: TargetPlanningRequest,
    plan: dict[str, Any],
    profile: dict[str, Any],
) -> None:
    """Validate Scientific HTML choices without leaking them into the core."""

    verification = plan["verification"]
    level = verification.get(
        "level", planning.artifact_contract.get("default_verification_level", "fast")
    )
    if level not in planning.artifact_contract.get("verification_levels", {}):
        raise FrameworkError(
            f"Target plan selects an unknown verification level: {level}"
        )
    verification_requirements = planning.capability_catalog.get(
        "verification_requirements", {}
    )
    if verification.get("runner") != verification_requirements.get("runner"):
        raise FrameworkError(
            "Target plan verification runner differs from the target capability contract"
        )
    _validate_verification_recipes(planning, plan, level)
    _validate_numeric_contract(plan["numeric_contract"])

    if plan["delivery"] not in profile.get("delivery_modes", []):
        raise FrameworkError(
            "Target plan delivery mode is not supported by the selected profile"
        )
    timing = plan["computation"].get("timing")
    if (
        not isinstance(timing, list)
        or not timing
        or not set(timing).issubset(profile.get("computation_timing", []))
    ):
        raise FrameworkError(
            "Target plan computation timing is not supported by the selected profile"
        )

    selected = _selected_capabilities(plan)
    supported = _profile_capabilities(profile)
    for domain, capabilities in selected.items():
        unsupported = sorted(capabilities - supported.get(domain, set()))
        if unsupported:
            raise FrameworkError(
                f"Target plan selects unsupported {domain} capabilities: {unsupported}"
            )
    invalid_coverage = [
        {
            "domain": record["capability_domain"],
            "capability": record["capability"],
        }
        for record in plan["requirement_capability_coverage"]
        if record["capability"]
        not in selected.get(record["capability_domain"], set())
    ]
    if invalid_coverage:
        raise FrameworkError(
            "Target plan coverage cites capabilities not selected by the plan: "
            f"{invalid_coverage}"
        )

    if level == "full":
        _validate_evidence_applicability(planning, plan)
    _validate_dependencies(planning, plan, profile, selected)


def _validate_numeric_contract(contract: dict[str, Any]) -> None:
    domains = contract.get("domains")
    tolerances = contract.get("tolerances")
    sampling = contract.get("sampling")
    valid_sampling = isinstance(sampling, dict) and bool(sampling) and all(
        isinstance(record, dict)
        and record.get("domain") in domains
        and (
            (
                isinstance(record.get("count"), int)
                and not isinstance(record.get("count"), bool)
                and record["count"] > 0
                and bool(record.get("spacing") or record.get("generator"))
            )
            or bool(record.get("points"))
        )
        for record in sampling.values()
    ) if isinstance(domains, dict) else False
    if (
        not isinstance(domains, dict)
        or not domains
        or not isinstance(tolerances, dict)
        or not tolerances
        or not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            and value >= 0
            for value in tolerances.values()
        )
        or not valid_sampling
        or not isinstance(contract.get("invariants"), list)
        or not isinstance(contract.get("boundary_or_initial_conditions"), list)
    ):
        raise FrameworkError("Target plan numerical contract is incomplete")


def _validate_verification_recipes(
    planning: TargetPlanningRequest,
    plan: dict[str, Any],
    level: str,
) -> None:
    fields = planning.plan_contract.get("verification_recipe_fields", [])
    dependency_names = {record["name"] for record in plan["dependencies"]}
    for recipe_name, record_name in (
        ("numerical_recipe", "numerical"),
        ("browser_recipe", "browser"),
    ):
        recipe = plan["verification"].get(recipe_name)
        if recipe is None and level == "fast":
            continue
        if (
            not isinstance(recipe, dict)
            or not all(field in recipe for field in fields)
            or not isinstance(recipe.get("argv"), list)
            or not recipe["argv"]
            or recipe["argv"][0] != recipe.get("script")
            or recipe.get("script") not in plan["artifact_inventory"]
            or recipe.get("expected_record") != plan["verification"].get(record_name)
            or (
                recipe.get("executor") != "python"
                and recipe.get("executor") not in dependency_names
            )
        ):
            raise FrameworkError(
                f"Target plan verification recipe is incomplete: {recipe_name}"
            )


def _validate_evidence_applicability(
    planning: TargetPlanningRequest, plan: dict[str, Any]
) -> None:
    contract = planning.plan_contract
    checks = contract.get("conditional_evidence_checks", [])
    fields = contract.get("evidence_applicability_fields", [])
    records = plan.get("evidence_applicability")
    if not isinstance(records, list) or not all(
        isinstance(record, dict) and all(field in record for field in fields)
        for record in records
    ):
        raise FrameworkError("Target plan evidence applicability records are incomplete")
    if {record["check_id"] for record in records} != set(checks) or len(records) != len(checks):
        raise FrameworkError(
            "Target plan evidence applicability does not cover each conditional check"
        )
    pivotal = {
        ref
        for hypothesis in planning.representation_intent.get(
            "pivotal_hypotheses", []
        )
        for ref in hypothesis.get("requirement_refs", [])
    }
    allowed = set(contract.get("allowed_applicability_statuses", []))
    for record in records:
        if record["status"] not in allowed or not isinstance(record["basis"], str) or not record["basis"]:
            raise FrameworkError(
                f"Target plan evidence applicability is invalid: {record['check_id']}"
            )
        references = record["requirement_refs"]
        if not isinstance(references, list) or not all(
            isinstance(ref, str) and ref in pivotal for ref in references
        ):
            raise FrameworkError(
                f"Target plan evidence applicability references are invalid: {record['check_id']}"
            )


def _validate_dependencies(
    planning: TargetPlanningRequest,
    plan: dict[str, Any],
    profile: dict[str, Any],
    selected: dict[str, set[str]],
) -> None:
    required = (
        set(profile.get("required_python_packages", []))
        | set(profile.get("required_external_tools", []))
        | set(
            planning.capability_catalog.get("verification_requirements", {}).get(
                "python_packages", []
            )
        )
    )
    dependency_map = profile.get("capability_dependencies", {})
    for domain, capabilities in selected.items():
        for capability in capabilities:
            required.update(dependency_map.get(domain, {}).get(capability, []))
    actual = {record["name"] for record in plan["dependencies"]}
    missing = sorted(required - actual)
    if missing:
        raise FrameworkError(
            f"Target plan omits selected-profile dependencies: {missing}"
        )


def _profile_capabilities(profile: dict[str, Any]) -> dict[str, set[str]]:
    return {
        "computation": set(profile.get("computation", [])),
        "view": set(profile.get("views", [])),
        "interaction": set(profile.get("interaction", [])),
        "delivery": {
            value
            for mode in profile.get("delivery_modes", [])
            if isinstance(mode, dict)
            for value in (mode.get("topology"), mode.get("connectivity"))
            if value
        },
    }


def _selected_capabilities(plan: dict[str, Any]) -> dict[str, set[str]]:
    views = {record["kind"] for record in plan["views"]}
    bindings = [
        record["state_binding"]
        for record in plan["views"]
        if isinstance(record.get("state_binding"), str)
        and record["state_binding"]
    ]
    if len(bindings) > 1 and len(set(bindings)) < len(bindings):
        views.add("linked-views")
    return {
        "computation": set(plan["computation"].get("capabilities", [])),
        "view": views,
        "interaction": {record["kind"] for record in plan["interactions"]},
        "delivery": {
            value
            for value in (
                plan["delivery"].get("topology"),
                plan["delivery"].get("connectivity"),
            )
            if value
        },
    }
