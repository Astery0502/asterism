"""Contract-backed validation for detached target realizations."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from ..models import PrototypeError
from .realization import TargetPlanningRequest


def validate_target_plan(
    planning: TargetPlanningRequest, plan: dict[str, Any]
) -> None:
    """Validate identity, capability selection, and target-plan shape."""

    contract = planning.plan_contract
    if not isinstance(contract, dict) or not contract.get("contract_id"):
        raise PrototypeError("Target realizer has no declared plan contract")
    required_fields = contract.get("required_fields")
    if not isinstance(required_fields, list) or not all(
        isinstance(field, str) and field for field in required_fields
    ):
        raise PrototypeError("Target plan contract has invalid required fields")
    missing = [field for field in required_fields if field not in plan]
    if missing:
        raise PrototypeError(f"Target plan is missing required fields: {missing}")
    if plan.get("schema_version") != contract.get("plan_schema_version"):
        raise PrototypeError("Target plan schema version does not match its contract")
    empty = [
        field
        for field in contract.get("required_nonempty_fields", [])
        if not plan.get(field)
    ]
    if empty:
        raise PrototypeError(f"Target plan has empty required fields: {empty}")
    for field, fields in contract.get("object_fields", {}).items():
        value = plan.get(field)
        if not isinstance(value, dict) or any(name not in value for name in fields):
            raise PrototypeError(f"Target plan object field is incomplete: {field}")
    for field, fields in contract.get("record_list_fields", {}).items():
        value = plan.get(field)
        if not isinstance(value, list) or not all(
            isinstance(record, dict) and all(name in record for name in fields)
            for record in value
        ):
            raise PrototypeError(f"Target plan record list is incomplete: {field}")
        if not all(
            all(isinstance(record[name], str) and record[name] for name in fields)
            for record in value
        ):
            raise PrototypeError(f"Target plan record values are invalid: {field}")
    for field in contract.get("string_list_fields", []):
        value = plan.get(field)
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item for item in value
        ):
            raise PrototypeError(f"Target plan string list is invalid: {field}")
    if plan.get("target") != planning.target:
        raise PrototypeError("Target plan identity does not match the selected target")
    if plan.get("representation_intent_id") != planning.representation_intent_id:
        raise PrototypeError("Target plan and representation intent IDs differ")
    if plan.get("requirements_id") != planning.requirements_id:
        raise PrototypeError("Target plan and requirements IDs differ")
    if plan.get("interface") != planning.interface_spec:
        raise PrototypeError(
            "Target plan interface snapshot differs from the accepted requirements interface"
        )

    profile_id = _target_profile_id(planning, plan)
    declared_profiles = {
        item.get("id"): item
        for item in planning.capability_catalog.get("profiles", [])
        if isinstance(item, dict)
    }
    if profile_id not in declared_profiles:
        raise PrototypeError(
            f"Target plan selects an unknown capability profile: {profile_id}"
        )
    selected_profile = declared_profiles[profile_id]
    verification_level = plan["verification"].get(
        "level", planning.artifact_contract.get("default_verification_level", "fast")
    )
    verification_levels = planning.artifact_contract.get("verification_levels", {})
    if verification_level not in verification_levels:
        raise PrototypeError(
            f"Target plan selects an unknown verification level: {verification_level}"
        )
    verification_requirements = planning.capability_catalog.get(
        "verification_requirements", {}
    )
    canonical_runner = verification_requirements.get("runner")
    if plan["verification"].get("runner") != canonical_runner:
        raise PrototypeError(
            "Target plan verification runner differs from the target capability contract"
        )
    dependency_names_for_recipes = {
        record["name"] for record in plan.get("dependencies", [])
    }
    recipe_fields = planning.plan_contract.get("verification_recipe_fields", [])
    for recipe_name, evidence_name in (
        ("numerical_recipe", "numerical"),
        ("browser_recipe", "browser"),
    ):
        recipe = plan["verification"].get(recipe_name)
        if recipe is None and verification_level == "fast":
            continue
        if (
            not isinstance(recipe, dict)
            or not isinstance(recipe_fields, list)
            or not all(field in recipe for field in recipe_fields)
            or not isinstance(recipe.get("executor"), str)
            or not recipe["executor"]
            or not isinstance(recipe.get("argv"), list)
            or not recipe["argv"]
            or not all(isinstance(item, str) and item for item in recipe["argv"])
            or not isinstance(recipe.get("script"), str)
            or not recipe["script"]
            or recipe["argv"][0] != recipe["script"]
            or recipe["script"] not in plan["artifact_inventory"]
            or recipe.get("expected_record")
            != plan["verification"].get(evidence_name)
            or (
                recipe["executor"] != "python"
                and recipe["executor"] not in dependency_names_for_recipes
            )
        ):
            raise PrototypeError(
                f"Target plan verification recipe is incomplete: {recipe_name}"
            )
    numeric_contract = plan["numeric_contract"]
    domains = numeric_contract.get("domains")
    tolerances = numeric_contract.get("tolerances")
    sampling = numeric_contract.get("sampling")
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
        or not isinstance(sampling, dict)
        or not sampling
        or not all(
            isinstance(record, dict)
            and record
            and isinstance(record.get("domain"), str)
            and record["domain"] in domains
            and (
                (
                    isinstance(record.get("count"), int)
                    and not isinstance(record.get("count"), bool)
                    and record["count"] > 0
                    and (
                        (
                            isinstance(record.get("spacing"), str)
                            and bool(record["spacing"])
                        )
                        or (
                            isinstance(record.get("generator"), str)
                            and bool(record["generator"])
                        )
                    )
                )
                or (
                    isinstance(record.get("points"), list)
                    and bool(record["points"])
                )
            )
            for record in sampling.values()
        )
        or not isinstance(numeric_contract.get("invariants"), list)
        or not isinstance(
            numeric_contract.get("boundary_or_initial_conditions"), list
        )
    ):
        raise PrototypeError("Target plan numerical contract is incomplete")
    delivery = plan["delivery"]
    if delivery not in selected_profile.get("delivery_modes", []):
        raise PrototypeError(
            "Target plan delivery mode is not supported by the selected profile"
        )
    computation = plan["computation"]
    computation_timing = computation.get("timing")
    if (
        not isinstance(computation_timing, list)
        or not computation_timing
        or not all(isinstance(item, str) and item for item in computation_timing)
        or not set(computation_timing).issubset(
            selected_profile.get("computation_timing", [])
        )
    ):
        raise PrototypeError(
            "Target plan computation timing is not supported by the selected profile"
        )
    computation_capabilities = computation.get("capabilities")
    if not isinstance(computation_capabilities, list) or not all(
        isinstance(item, str) and item for item in computation_capabilities
    ):
        raise PrototypeError("Target plan computation capabilities are invalid")
    unsupported_computation = sorted(
        set(computation_capabilities) - set(selected_profile.get("computation", []))
    )
    if unsupported_computation:
        raise PrototypeError(
            "Target plan selects unsupported computation capabilities: "
            f"{unsupported_computation}"
        )
    unsupported_views = sorted(
        {
            record["kind"]
            for record in plan["views"]
            if record["kind"] not in selected_profile.get("views", [])
        }
    )
    if unsupported_views:
        raise PrototypeError(
            f"Target plan selects unsupported views: {unsupported_views}"
        )
    unsupported_interactions = sorted(
        {
            record["kind"]
            for record in plan["interactions"]
            if record["kind"] not in selected_profile.get("interaction", [])
        }
    )
    if unsupported_interactions:
        raise PrototypeError(
            "Target plan selects unsupported interactions: "
            f"{unsupported_interactions}"
        )
    for relative in plan["artifact_inventory"]:
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise PrototypeError(
                f"Target plan artifact path must remain relative: {relative}"
            )

    coverage = plan["requirement_capability_coverage"]
    coverage_keys = [
        (
            record["requirement_id"],
            record["capability_domain"],
            record["capability"],
        )
        for record in coverage
    ]
    if len(coverage_keys) != len(set(coverage_keys)):
        raise PrototypeError("Target plan requirement coverage entries are not unique")
    coverage_ids = {record["requirement_id"] for record in coverage}
    expected_requirements = _pivotal_requirement_ids(planning)
    missing_coverage = sorted(expected_requirements - coverage_ids)
    if missing_coverage:
        raise PrototypeError(
            f"Target plan does not cover pivotal requirements: {missing_coverage}"
        )
    allowed_statuses = set(contract.get("allowed_coverage_statuses", []))
    invalid_statuses = [
        record.get("status")
        for record in coverage
        if record.get("status") not in allowed_statuses
    ]
    if invalid_statuses:
        raise PrototypeError(
            f"Target plan has invalid coverage statuses: {invalid_statuses}"
        )
    supported_capabilities = _profile_capabilities(selected_profile)
    invalid_capabilities = [
        {
            "domain": record["capability_domain"],
            "capability": record["capability"],
        }
        for record in coverage
        if record["capability_domain"] not in supported_capabilities
        or record["capability"]
        not in supported_capabilities.get(record["capability_domain"], set())
    ]
    if invalid_capabilities:
        raise PrototypeError(
            f"Target plan coverage cites unsupported capabilities: {invalid_capabilities}"
        )
    selected_capabilities = _selected_plan_capabilities(plan)
    unselected_coverage = [
        {
            "domain": record["capability_domain"],
            "capability": record["capability"],
        }
        for record in coverage
        if record["capability"]
        not in selected_capabilities.get(record["capability_domain"], set())
    ]
    if unselected_coverage:
        raise PrototypeError(
            "Target plan coverage cites capabilities not selected by the plan: "
            f"{unselected_coverage}"
        )

    if verification_level == "full":
        _validate_evidence_applicability(planning, plan, selected_capabilities)

    dependencies = plan["dependencies"]
    dependency_names = [record["name"] for record in dependencies]
    if len(dependency_names) != len(set(dependency_names)):
        raise PrototypeError("Target plan dependency names are not unique")
    required_dependency_names = (
        set(selected_profile.get("required_python_packages", []))
        | set(selected_profile.get("required_external_tools", []))
        | set(verification_requirements.get("python_packages", []))
    )
    capability_dependencies = selected_profile.get("capability_dependencies", {})
    if not isinstance(capability_dependencies, dict):
        raise PrototypeError("Selected profile capability dependencies are invalid")
    for domain, capabilities in selected_capabilities.items():
        domain_dependencies = capability_dependencies.get(domain, {})
        if not isinstance(domain_dependencies, dict):
            raise PrototypeError(
                f"Selected profile capability dependencies are invalid: {domain}"
            )
        for capability in capabilities:
            dependency_names_for_capability = domain_dependencies.get(capability, [])
            if not isinstance(dependency_names_for_capability, list) or not all(
                isinstance(item, str) and item
                for item in dependency_names_for_capability
            ):
                raise PrototypeError(
                    "Selected profile capability dependency declaration is invalid: "
                    f"{domain}/{capability}"
                )
            required_dependency_names.update(dependency_names_for_capability)
    missing_dependencies = sorted(required_dependency_names - set(dependency_names))
    if missing_dependencies:
        raise PrototypeError(
            "Target plan omits selected-profile dependencies: "
            f"{missing_dependencies}"
        )


def validate_target_plan_implementation_ready(
    planning: TargetPlanningRequest, plan: dict[str, Any]
) -> None:
    """Block implementation when pivotal obligations remain conditional or unmet."""

    pivotal = _pivotal_requirement_ids(planning)
    unresolved = sorted(
        {
            record["requirement_id"]
            for record in plan.get("requirement_capability_coverage", [])
            if record.get("requirement_id") in pivotal
            and record.get("status") != "covered"
        }
    )
    declared_unmet = plan.get("unmet_requirements", [])
    if unresolved or declared_unmet:
        raise PrototypeError(
            "Target plan cannot be implemented while pivotal requirements are "
            f"conditional or unmet: {sorted(set(unresolved) | set(declared_unmet))}"
        )


def validate_target_application(
    planning: TargetPlanningRequest,
    plan: dict[str, Any],
    result: dict[str, Any],
    application_root: Path,
) -> dict[str, Any]:
    """Validate the declared artifact/evidence envelope before conformance."""

    if result.get("pass") is not True:
        return {
            "status": "implementation-reported-failure",
            "artifact_contract_id": planning.artifact_contract.get("contract_id"),
            "pass": False,
        }
    contract = planning.artifact_contract
    if not isinstance(contract, dict) or not contract.get("contract_id"):
        raise PrototypeError("Target realizer has no declared artifact contract")
    required_records = contract.get("required_records")
    required_fields = contract.get("manifest_fields")
    pass_records = contract.get("required_pass_records", [])
    if not isinstance(required_records, list) or not isinstance(required_fields, list):
        raise PrototypeError("Target artifact contract is incomplete")
    resolved_records = {
        relative: _contained_path(application_root, relative, "artifact record")
        for relative in required_records
    }
    missing_records = [
        relative for relative, path in resolved_records.items() if not path.is_file()
    ]
    if missing_records:
        raise PrototypeError(
            f"Target application is missing required records: {missing_records}"
        )
    inventory = plan.get("artifact_inventory", [])
    if len(inventory) != len(set(inventory)):
        raise PrototypeError("Target plan artifact inventory contains duplicates")
    unresolved_inventory = [
        relative
        for relative in inventory
        if not _contained_path(
            application_root, relative, "planned artifact"
        ).is_file()
    ]
    if unresolved_inventory:
        raise PrototypeError(
            f"Target application is missing planned artifacts: {unresolved_inventory}"
        )
    missing_from_plan = sorted(
        set(required_records) - set(plan.get("artifact_inventory", []))
    )
    if missing_from_plan:
        raise PrototypeError(
            f"Target plan omits required artifact records: {missing_from_plan}"
        )
    verification_paths = {
        plan.get("verification", {}).get("numerical"),
        plan.get("verification", {}).get("browser"),
    }
    if verification_paths != set(pass_records):
        raise PrototypeError(
            "Target plan verification paths do not match the artifact contract"
        )

    manifest_path = resolved_records.get("application-manifest.json")
    if manifest_path is None:
        raise PrototypeError("Target artifact contract declares no application manifest")
    manifest = _read_contract_json(manifest_path, "application manifest")
    missing_fields = [field for field in required_fields if field not in manifest]
    if missing_fields:
        raise PrototypeError(
            f"Application manifest is missing required fields: {missing_fields}"
        )
    profile_id = _target_profile_id(planning, plan)
    expected_identity = {
        "plan_id": plan.get("plan_id"),
        "target_id": planning.target,
        "toolchain_profile_id": profile_id,
        "representation_intent_id": planning.representation_intent_id,
        "requirements_id": planning.requirements_id,
    }
    mismatched = [
        key for key, value in expected_identity.items() if manifest.get(key) != value
    ]
    if mismatched:
        raise PrototypeError(f"Application manifest identity fields differ: {mismatched}")

    entry_point = manifest.get("entry_point")
    if not isinstance(entry_point, str) or not _contained_path(
        application_root, entry_point, "entry point"
    ).is_file():
        raise PrototypeError("Application manifest entry point does not resolve")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise PrototypeError("Application manifest declares no artifacts")
    unresolved_artifacts = [
        item
        for item in artifacts
        if not isinstance(item, str)
        or not _contained_path(application_root, item, "declared artifact").is_file()
    ]
    if unresolved_artifacts:
        raise PrototypeError(
            f"Application manifest artifacts do not resolve: {unresolved_artifacts}"
        )
    if len(artifacts) != len(set(artifacts)):
        raise PrototypeError("Application manifest artifacts contain duplicates")
    expected_manifest_artifacts = set(inventory) - {"application-manifest.json"}
    if set(artifacts) != expected_manifest_artifacts:
        raise PrototypeError(
            "Application manifest artifacts differ from the target plan inventory"
        )
    if entry_point not in set(artifacts):
        raise PrototypeError("Application entry point is absent from artifact inventory")
    referenced_assets = _validate_asset_closure(
        application_root,
        entry_point,
        set(artifacts),
        offline=plan.get("delivery", {}).get("connectivity") == "offline",
    )

    dependencies = manifest.get("dependencies")
    dependency_fields = contract.get("dependency_fields", [])
    if not isinstance(dependencies, list) or not dependencies or not all(
        isinstance(record, dict)
        and all(
            isinstance(record.get(field), str) and record[field]
            for field in dependency_fields
        )
        for record in dependencies
    ):
        raise PrototypeError("Application manifest dependency provenance is incomplete")
    if dependencies != plan.get("dependencies"):
        raise PrototypeError("Application and plan dependency provenance differ")

    validation_evidence = manifest.get("validation_evidence")
    if not isinstance(validation_evidence, list) or not all(
        isinstance(item, str) and item for item in validation_evidence
    ):
        raise PrototypeError("Application manifest validation evidence is invalid")
    missing_evidence_refs = sorted(set(pass_records) - set(validation_evidence))
    if missing_evidence_refs:
        raise PrototypeError(
            f"Application manifest omits required evidence: {missing_evidence_refs}"
        )
    for relative in validation_evidence:
        if relative not in set(artifacts):
            raise PrototypeError(
                f"Validation evidence is absent from artifact inventory: {relative}"
            )
        if not _contained_path(
            application_root, relative, "validation evidence"
        ).is_file():
            raise PrototypeError(f"Validation evidence does not resolve: {relative}")

    evidence_check_statuses: dict[str, str] = {}
    evidence_summaries: list[dict[str, Any]] = []
    evidence_contract = contract.get("evidence_record_contract", {})
    verification_level = plan.get("verification", {}).get(
        "level", contract.get("default_verification_level", "fast")
    )
    level_checks = contract.get("verification_levels", {}).get(verification_level)
    if not isinstance(level_checks, dict):
        raise PrototypeError(
            f"Application selects an unknown verification level: {verification_level}"
        )
    for relative in pass_records:
        path = resolved_records.get(relative) or _contained_path(
            application_root, relative, "evidence record"
        )
        summary = _validate_evidence_record(
            path,
            relative,
            evidence_contract,
            level_checks,
            contract.get("structured_check_details", {}),
            application_root,
            planning=planning,
            plan=plan,
        )
        evidence_summaries.append(summary)
        for check_id, status in summary["check_statuses"].items():
            existing = evidence_check_statuses.get(check_id)
            if existing is not None and existing != status:
                raise PrototypeError(
                    f"Evidence check status is inconsistent: {check_id}"
                )
            evidence_check_statuses[check_id] = status
    reported_asset_references = {
        item
        for summary in evidence_summaries
        for item in summary.get("asset_references", [])
    }
    if "assets-resolve" in evidence_check_statuses and (
        reported_asset_references != set(referenced_assets)
    ):
        raise PrototypeError(
            "Browser asset ledger differs from the statically resolved asset closure"
        )
    observed_local_requests = {
        item
        for summary in evidence_summaries
        for item in summary.get("observed_local_requests", [])
    }
    undeclared_observed_requests = sorted(observed_local_requests - set(artifacts))
    if undeclared_observed_requests:
        raise PrototypeError(
            "Browser requested local assets absent from artifact inventory: "
            f"{undeclared_observed_requests}"
        )
    asset_request_counts = [
        count
        for summary in evidence_summaries
        for count in summary.get("asset_request_counts", [])
    ]
    if asset_request_counts and any(
        count < len(observed_local_requests) for count in asset_request_counts
    ):
        raise PrototypeError(
            "Browser asset request count is smaller than its observed local ledger"
        )
    evidence_artifacts = {
        item
        for summary in evidence_summaries
        for item in summary.get("artifacts", [])
    }
    undeclared_evidence_artifacts = sorted(evidence_artifacts - set(artifacts))
    if undeclared_evidence_artifacts:
        raise PrototypeError(
            "Evidence attachments are absent from artifact inventory: "
            f"{undeclared_evidence_artifacts}"
        )

    traceability = manifest.get("requirement_traceability")
    traceability_fields = contract.get("traceability_fields", [])
    if not isinstance(traceability, list) or not traceability or not all(
        isinstance(record, dict)
        and all(
            isinstance(record.get(field), str) and record[field]
            for field in traceability_fields
        )
        for record in traceability
    ):
        raise PrototypeError("Application manifest requirement traceability is incomplete")
    trace_ids = {record["requirement_id"] for record in traceability}
    pivotal_requirements = _pivotal_requirement_ids(planning)
    missing_traceability = sorted(pivotal_requirements - trace_ids)
    if missing_traceability:
        raise PrototypeError(
            f"Application manifest omits pivotal requirements: {missing_traceability}"
        )
    for record in traceability:
        if record["artifact"] not in set(artifacts):
            raise PrototypeError(
                "Traceability artifact is absent from artifact inventory: "
                f"{record['artifact']}"
            )
        if not _contained_path(
            application_root, record["artifact"], "traceability artifact"
        ).is_file():
            raise PrototypeError(
                f"Traceability artifact does not resolve: {record['artifact']}"
            )
        if evidence_check_statuses.get(record["check"]) != "passed":
            raise PrototypeError(
                "Traceability check is absent or did not pass in evidence: "
                f"{record['check']}"
            )

    coverage = plan["requirement_capability_coverage"]
    uncovered = [
        record["requirement_id"]
        for record in coverage
        if record["requirement_id"] in pivotal_requirements
        and record["status"] != "covered"
    ]
    if uncovered or plan.get("unmet_requirements"):
        raise PrototypeError(
            "Target application cannot conform with unmet or conditional pivotal requirements"
        )
    coordinator_checks = [
        {"id": "entry-point-resolves", "status": "passed"},
        {"id": "local-asset-closure-resolves", "status": "passed"},
        {"id": "manifest-paths-resolve", "status": "passed"},
        {"id": "dependency-and-license-provenance", "status": "passed"},
    ]
    return {
        "status": "artifact-contract-validated",
        "plan_contract_id": planning.plan_contract.get("contract_id"),
        "artifact_contract_id": contract.get("contract_id"),
        "profile_id": profile_id,
        "required_record_count": len(required_records),
        "evidence": evidence_summaries,
        "coordinator_checks": coordinator_checks,
        "pass": True,
    }


def _target_profile_id(
    planning: TargetPlanningRequest, plan: dict[str, Any]
) -> Any:
    field = str(planning.plan_contract.get("profile_field", "toolchain_profile_id"))
    return plan.get(field)


def _pivotal_requirement_ids(planning: TargetPlanningRequest) -> set[str]:
    requirement_ids: set[str] = set()
    hypotheses = planning.representation_intent.get("pivotal_hypotheses", [])
    if not isinstance(hypotheses, list):
        raise PrototypeError("Representation intent pivotal hypotheses must be a list")
    for hypothesis in hypotheses:
        if not isinstance(hypothesis, dict):
            continue
        references = hypothesis.get("requirement_refs", [])
        if not isinstance(references, list):
            raise PrototypeError("Pivotal requirement references must be a list")
        requirement_ids.update(
            reference
            for reference in references
            if isinstance(reference, str) and reference
        )
    if not requirement_ids:
        raise PrototypeError(
            "Representation intent has no pivotal requirement references"
        )
    return requirement_ids


def _validate_evidence_record(
    path: Path,
    relative: str,
    evidence_contract: dict[str, Any],
    mechanical_checks: dict[str, Any],
    structured_check_details: dict[str, Any],
    application_root: Path,
    *,
    planning: TargetPlanningRequest,
    plan: dict[str, Any],
) -> dict[str, Any]:
    if not path.is_file():
        raise PrototypeError(f"Target application evidence is missing: {relative}")
    record = _read_contract_json(path, relative)
    required_record_fields = evidence_contract.get("required_record_fields", [])
    if any(field not in record for field in required_record_fields):
        raise PrototypeError(f"Evidence record is incomplete: {relative}")
    if record.get("schema_version") != evidence_contract.get("schema_version"):
        raise PrototypeError(f"Evidence schema version is invalid: {relative}")
    expected_type = evidence_contract.get("record_types", {}).get(relative)
    if record.get("record_type") != expected_type:
        raise PrototypeError(f"Evidence record type is invalid: {relative}")
    runner = record.get("runner")
    if not isinstance(runner, str) or not runner:
        raise PrototypeError(f"Evidence runner is invalid: {relative}")
    if (
        expected_type == "browser"
        and runner
        != planning.capability_catalog.get("verification_requirements", {}).get(
            "runner"
        )
    ):
        raise PrototypeError(
            f"Browser evidence runner differs from the target contract: {relative}"
        )
    if record.get("pass") is not True:
        raise PrototypeError(f"Target application evidence did not pass: {relative}")
    checks = record.get("checks")
    check_fields = evidence_contract.get("required_check_fields", [])
    if not isinstance(checks, list) or not checks or not all(
        isinstance(check, dict)
        and all(field in check for field in check_fields)
        for check in checks
    ):
        raise PrototypeError(f"Evidence checks are incomplete: {relative}")
    if not all(
        isinstance(check["id"], str)
        and check["id"]
        and isinstance(check["status"], str)
        and check["status"]
        for check in checks
    ):
        raise PrototypeError(f"Evidence check identities are invalid: {relative}")
    check_ids = [check["id"] for check in checks]
    if len(check_ids) != len(set(check_ids)):
        raise PrototypeError(f"Evidence check IDs are not unique: {relative}")
    required_categories = evidence_contract.get("coverage", {}).get(relative, [])
    required_ids = {
        check_id
        for category in required_categories
        for check_id in mechanical_checks.get(category, [])
    }
    missing_ids = sorted(required_ids - set(check_ids))
    if missing_ids:
        raise PrototypeError(
            f"Evidence record omits declared checks in {relative}: {missing_ids}"
        )
    accepted_statuses = set(evidence_contract.get("accepted_statuses", []))
    for check in checks:
        if check["status"] not in accepted_statuses:
            raise PrototypeError(
                f"Evidence check status is invalid in {relative}: {check['id']}"
            )
        if not isinstance(check["method"], str) or not check["method"]:
            raise PrototypeError(f"Evidence check method is empty: {check['id']}")
        if not isinstance(check["details"], dict) or not check["details"]:
            raise PrototypeError(f"Evidence check details are empty: {check['id']}")
        applicable = _check_is_applicable(check["id"], planning, plan)
        if applicable and check["status"] != "passed":
            raise PrototypeError(
                f"Required evidence check did not pass in {relative}: {check['id']}"
            )
        if not applicable and check["status"] != "not_applicable":
            raise PrototypeError(
                f"Conditional evidence status differs from the plan in {relative}: "
                f"{check['id']}"
            )
        if check["status"] == "not_applicable":
            justification = check["details"].get("justification")
            if not isinstance(justification, str) or not justification:
                raise PrototypeError(
                    f"Evidence check cannot be not_applicable in {relative}: "
                    f"{check['id']}"
                )
        _validate_structured_check_details(check, plan, structured_check_details)
        evidence_artifacts = check.get("artifacts", [])
        if not isinstance(evidence_artifacts, list) or not all(
            isinstance(item, str)
            and _contained_path(application_root, item, "evidence artifact").is_file()
            for item in evidence_artifacts
        ):
            raise PrototypeError(f"Evidence artifacts are invalid: {check['id']}")
        if check["id"] == "review-screenshot" and not evidence_artifacts:
            raise PrototypeError("Review-screenshot evidence declares no screenshot")
    return {
        "path": relative,
        "record_type": expected_type,
        "check_ids": check_ids,
        "check_statuses": {check["id"]: check["status"] for check in checks},
        "asset_references": sorted(
            {
                item
                for check in checks
                if check.get("id") == "assets-resolve"
                for item in check.get("details", {}).get("local_references", [])
                if isinstance(item, str)
            }
        ),
        "observed_local_requests": sorted(
            {
                item
                for check in checks
                if check.get("id") == "assets-resolve"
                for item in check.get("details", {}).get(
                    "observed_local_requests", []
                )
                if isinstance(item, str)
            }
        ),
        "asset_request_counts": [
            check.get("details", {}).get("request_count")
            for check in checks
            if check.get("id") == "assets-resolve"
            and isinstance(check.get("details", {}).get("request_count"), int)
        ],
        "artifacts": sorted(
            {
                item
                for check in checks
                for item in check.get("artifacts", [])
                if isinstance(item, str)
            }
        ),
        "pass": True,
    }


def _validate_structured_check_details(
    check: dict[str, Any],
    plan: dict[str, Any],
    structured_check_details: dict[str, Any],
) -> None:
    if check.get("status") == "not_applicable":
        return
    check_id = check["id"]
    details = check["details"]
    required_fields = structured_check_details.get(check_id, [])
    if not isinstance(required_fields, list) or any(
        field not in details for field in required_fields
    ):
        raise PrototypeError(
            f"Structured evidence details are incomplete: {check_id}"
        )
    if check_id == "fresh-load" and (
        details.get("loaded") is not True
        or details.get("document_ready_state") not in {"interactive", "complete"}
    ):
        raise PrototypeError("Fresh-load evidence has no successful browser state")
    if check_id == "no-console-errors" and details.get("console_errors") != []:
        raise PrototypeError("No-console-errors evidence reports browser errors")
    if check_id == "assets-resolve" and (
        not isinstance(details.get("request_count"), int)
        or details["request_count"] < 0
        or not isinstance(details.get("local_references"), list)
        or not isinstance(details.get("observed_local_requests"), list)
        or not all(
            isinstance(item, str) and item
            for item in (
                details.get("local_references", [])
                + details.get("observed_local_requests", [])
            )
        )
        or details.get("failed_requests") != []
    ):
        raise PrototypeError("Assets-resolve evidence lacks a clean request ledger")
    if check_id == "offline-network-block-when-declared" and (
        plan.get("delivery", {}).get("connectivity") == "offline"
        and (
            details.get("network_blocked") is not True
            or details.get("unexpected_requests") != []
        )
    ):
        raise PrototypeError("Offline evidence does not demonstrate a blocked network")
    numeric_contract = plan.get("numeric_contract", {})
    if check_id in {
        "identities-or-residuals",
        "invariants",
        "boundary-or-initial-conditions",
    } and (
        details.get("sampling_ref") not in numeric_contract.get("sampling", {})
        or details.get("tolerance_ref")
        not in numeric_contract.get("tolerances", {})
        or not _finite_number(details.get("measured_value"))
        or details["measured_value"] < 0
        or details["measured_value"]
        > numeric_contract.get("tolerances", {}).get(
            details.get("tolerance_ref"), float("-inf")
        )
        or not isinstance(details.get("norm"), str)
        or not details["norm"]
        or not isinstance(details.get("reference_method"), str)
        or not details["reference_method"]
    ):
        raise PrototypeError(
            f"Numerical evidence does not cite the declared contract: {check_id}"
        )
    if check_id == "declared-tolerances" and (
        not isinstance(details.get("sampling_refs"), list)
        or set(details["sampling_refs"])
        != set(numeric_contract.get("sampling", {}))
        or not isinstance(details.get("tolerance_refs"), list)
        or set(details["tolerance_refs"])
        != set(numeric_contract.get("tolerances", {}))
    ):
        raise PrototypeError(
            "Declared-tolerances evidence does not cover the numerical contract"
        )
    if check_id == "review-screenshot":
        mappings = details.get("anchor_screenshots")
        expected_anchors = plan.get("interface", {}).get("anchors", [])
        if (
            not isinstance(mappings, list)
            or not all(
                isinstance(item, dict)
                and "anchor" in item
                and isinstance(item.get("artifact"), str)
                and item["artifact"] in check.get("artifacts", [])
                for item in mappings
            )
            or Counter(_canonical_json(item["anchor"]) for item in mappings)
            != Counter(_canonical_json(anchor) for anchor in expected_anchors)
        ):
            raise PrototypeError(
                "Review-screenshot evidence does not map every declared anchor"
            )


def _profile_capabilities(profile: dict[str, Any]) -> dict[str, set[str]]:
    delivery = {
        value
        for mode in profile.get("delivery_modes", [])
        if isinstance(mode, dict)
        for value in (mode.get("topology"), mode.get("connectivity"))
        if isinstance(value, str) and value
    }
    return {
        "computation": set(profile.get("computation", [])),
        "view": set(profile.get("views", [])),
        "interaction": set(profile.get("interaction", [])),
        "delivery": delivery,
    }


def _selected_plan_capabilities(plan: dict[str, Any]) -> dict[str, set[str]]:
    views = {record["kind"] for record in plan.get("views", [])}
    state_bindings = [
        record.get("state_binding")
        for record in plan.get("views", [])
        if isinstance(record.get("state_binding"), str)
        and record.get("state_binding")
    ]
    if len(state_bindings) > 1 and len(set(state_bindings)) < len(state_bindings):
        views.add("linked-views")
    delivery = plan.get("delivery", {})
    return {
        "computation": set(plan.get("computation", {}).get("capabilities", [])),
        "view": views,
        "interaction": {
            record["kind"] for record in plan.get("interactions", [])
        },
        "delivery": {
            value
            for value in (
                delivery.get("topology"),
                delivery.get("connectivity"),
            )
            if isinstance(value, str) and value
        },
    }


def _validate_evidence_applicability(
    planning: TargetPlanningRequest,
    plan: dict[str, Any],
    selected_capabilities: dict[str, set[str]],
) -> None:
    contract = planning.plan_contract
    conditional_checks = contract.get("conditional_evidence_checks", [])
    allowed_statuses = set(contract.get("allowed_applicability_statuses", []))
    required_fields = contract.get("evidence_applicability_fields", [])
    records = plan.get("evidence_applicability")
    if (
        not isinstance(conditional_checks, list)
        or not conditional_checks
        or not isinstance(records, list)
        or not isinstance(required_fields, list)
        or not required_fields
    ):
        raise PrototypeError("Target plan evidence applicability contract is invalid")
    if not all(
        isinstance(record, dict)
        and all(field in record for field in required_fields)
        for record in records
    ):
        raise PrototypeError("Target plan evidence applicability records are incomplete")
    check_ids = [record["check_id"] for record in records]
    if len(check_ids) != len(set(check_ids)) or set(check_ids) != set(
        conditional_checks
    ):
        raise PrototypeError(
            "Target plan evidence applicability does not cover each conditional check"
        )
    pivotal = _pivotal_requirement_ids(planning)
    expected = _expected_evidence_applicability(
        planning, plan, selected_capabilities
    )
    for record in records:
        check_id = record["check_id"]
        status = record["status"]
        basis = record["basis"]
        references = record["requirement_refs"]
        if status not in allowed_statuses:
            raise PrototypeError(
                f"Target plan evidence applicability status is invalid: {check_id}"
            )
        if not isinstance(basis, str) or not basis:
            raise PrototypeError(
                f"Target plan evidence applicability basis is empty: {check_id}"
            )
        if not isinstance(references, list) or not all(
            isinstance(item, str) and item in pivotal for item in references
        ):
            raise PrototypeError(
                f"Target plan evidence applicability references are invalid: {check_id}"
            )
        expected_status = "required" if expected[check_id] else "not_applicable"
        if status != expected_status:
            raise PrototypeError(
                "Target plan evidence applicability contradicts the accepted "
                f"interface or selected capabilities: {check_id}"
            )
        if (status == "required") != bool(references):
            raise PrototypeError(
                f"Target plan evidence applicability traceability is invalid: {check_id}"
            )


def _expected_evidence_applicability(
    planning: TargetPlanningRequest,
    plan: dict[str, Any],
    selected_capabilities: dict[str, set[str]],
) -> dict[str, bool]:
    interface = planning.interface_spec
    numeric = plan.get("numeric_contract", {})
    controls = bool(interface.get("controls", []))
    return {
        "invariants": bool(numeric.get("invariants")),
        "boundary-or-initial-conditions": bool(
            numeric.get("boundary_or_initial_conditions")
        ),
        "bounds": controls,
        "steps": controls,
        "defaults": controls,
        "named-anchors": bool(interface.get("anchors", [])),
        "linked-view-updates": "linked-views"
        in selected_capabilities.get("view", set()),
        "invalid-state-handling": controls,
        "control-causes-expected-state-change": controls,
        "offline-network-block-when-declared": (
            plan.get("delivery", {}).get("connectivity") == "offline"
        ),
    }


def _check_is_applicable(
    check_id: str,
    planning: TargetPlanningRequest,
    plan: dict[str, Any],
) -> bool:
    applicability = {
        record.get("check_id"): record.get("status") == "required"
        for record in plan.get("evidence_applicability", [])
        if isinstance(record, dict)
    }
    return applicability.get(check_id, True)


class _HtmlAssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []
        self.styles: list[str] = []
        self._inside_style = False

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        for name, value in attrs:
            if not value:
                continue
            if name in {"src", "poster", "data-src"} or (
                tag == "link" and name == "href"
            ):
                self.references.append(value)
            elif name == "srcset":
                self.references.extend(
                    candidate.strip().split()[0]
                    for candidate in value.split(",")
                    if candidate.strip()
                )
            elif name == "style":
                self.styles.append(value)
        if tag == "style":
            self._inside_style = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "style":
            self._inside_style = False

    def handle_data(self, data: str) -> None:
        if self._inside_style:
            self.styles.append(data)


_CSS_REFERENCE_RE = re.compile(
    r"url\(\s*['\"]?([^'\")]+)|@import\s+(?:url\()?\s*['\"]([^'\"]+)",
    re.IGNORECASE,
)
_JS_REFERENCE_RE = re.compile(
    r"(?:import\s*(?:[^'\"]*?\sfrom\s*)?|export\s+[^'\"]*?\sfrom\s*|"
    r"import\s*\(|fetch\s*\()\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)


def _validate_asset_closure(
    application_root: Path,
    entry_point: str,
    declared_artifacts: set[str],
    *,
    offline: bool,
) -> list[str]:
    scannable_suffixes = {".html", ".htm", ".css", ".js", ".mjs"}
    queue = [entry_point] + sorted(
        item
        for item in declared_artifacts
        if Path(item).suffix.lower() in scannable_suffixes and item != entry_point
    )
    scanned: set[str] = set()
    discovered: set[str] = set()
    while queue:
        relative = queue.pop(0)
        if relative in scanned:
            continue
        scanned.add(relative)
        source = _contained_path(application_root, relative, "web asset")
        if source.suffix.lower() not in scannable_suffixes:
            continue
        try:
            content = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise PrototypeError(f"Web asset cannot be inspected: {relative}: {exc}") from exc
        references = _extract_asset_references(source.suffix.lower(), content)
        for reference in references:
            resolved = _resolve_asset_reference(
                application_root, source, reference, offline=offline
            )
            if resolved is None:
                continue
            resolved_relative = resolved.relative_to(application_root.resolve()).as_posix()
            if resolved_relative not in declared_artifacts:
                raise PrototypeError(
                    "Referenced local asset is absent from artifact inventory: "
                    f"{resolved_relative}"
                )
            discovered.add(resolved_relative)
            if resolved.suffix.lower() in scannable_suffixes:
                queue.append(resolved_relative)
    return sorted(discovered)


def _extract_asset_references(suffix: str, content: str) -> set[str]:
    references: set[str] = set()
    if suffix in {".html", ".htm"}:
        parser = _HtmlAssetParser()
        parser.feed(content)
        references.update(parser.references)
        references.update(
            first or second
            for first, second in _CSS_REFERENCE_RE.findall("\n".join(parser.styles))
            if first or second
        )
    if suffix == ".css":
        references.update(
            first or second
            for first, second in _CSS_REFERENCE_RE.findall(content)
            if first or second
        )
    if suffix in {".js", ".mjs"}:
        references.update(_JS_REFERENCE_RE.findall(content))
    return references


def _resolve_asset_reference(
    application_root: Path,
    source: Path,
    reference: str,
    *,
    offline: bool,
) -> Path | None:
    stripped = reference.strip()
    if not stripped or stripped.startswith("#"):
        return None
    parsed = urlsplit(stripped)
    if parsed.scheme in {"data", "blob", "about"}:
        return None
    if parsed.scheme in {"http", "https", "ws", "wss"} or parsed.netloc:
        if offline:
            raise PrototypeError(
                f"Offline application references a network asset: {reference}"
            )
        return None
    if parsed.scheme:
        raise PrototypeError(
            f"Web asset uses a non-portable URI scheme: {reference}"
        )
    path_text = unquote(parsed.path)
    if not path_text:
        return None
    candidate = (
        application_root / path_text.lstrip("/\\")
        if path_text.startswith(("/", "\\"))
        else source.parent / path_text
    ).resolve()
    try:
        candidate.relative_to(application_root.resolve())
    except ValueError as exc:
        raise PrototypeError(
            f"Web asset reference leaves the application root: {reference}"
        ) from exc
    if candidate.is_dir():
        candidate = candidate / "index.html"
    if not candidate.is_file():
        raise PrototypeError(f"Referenced web asset does not resolve: {reference}")
    return candidate


def _contained_path(root: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise PrototypeError(f"{label} path must be a non-empty relative string")
    candidate = Path(relative)
    if candidate.is_absolute():
        raise PrototypeError(f"{label} path must be relative: {relative}")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise PrototypeError(
            f"{label} path leaves the application root: {relative}"
        ) from exc
    return resolved


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise PrototypeError(f"Evidence contains a non-JSON anchor: {exc}") from exc


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _read_contract_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PrototypeError(f"Invalid {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise PrototypeError(f"{label} must contain an object")
    return value
