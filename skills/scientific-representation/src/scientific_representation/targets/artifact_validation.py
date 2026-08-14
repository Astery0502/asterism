"""Target-neutral artifact envelope and traceability validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..domain import FrameworkError
from ..ports import TargetPlanningRequest
from .traceability import (
    pivotal_requirement_ids,
    target_requirement_coverage,
    target_profile_id,
)
from .validation_support import (
    contained_path,
    load_validation_extension,
    read_json_object,
)


def validate_target_application(
    planning: TargetPlanningRequest,
    plan: dict[str, Any],
    execution_status: str,
    manifest_record: str | None,
    application_root: Path,
) -> dict[str, Any]:
    """Validate the declared artifact/evidence envelope before conformance."""

    if execution_status != "completed":
        return {
            "status": "implementation-reported-failure",
            "artifact_contract_id": planning.artifact_contract.get("contract_id"),
            "target_requirement_coverage": target_requirement_coverage(plan),
            "pass": False,
        }
    contract = planning.artifact_contract
    if not isinstance(contract, dict) or not contract.get("contract_id"):
        raise FrameworkError("Target realizer has no declared artifact contract")
    required_records = contract.get("required_records")
    required_fields = contract.get("manifest_fields")
    pass_records = contract.get("required_pass_records", [])
    if not isinstance(required_records, list) or not isinstance(required_fields, list):
        raise FrameworkError("Target artifact contract is incomplete")
    resolved_records = {
        relative: contained_path(application_root, relative, "artifact record")
        for relative in required_records
    }
    missing_records = [
        relative for relative, path in resolved_records.items() if not path.is_file()
    ]
    if missing_records:
        raise FrameworkError(
            f"Target application is missing required records: {missing_records}"
        )
    inventory = plan.get("artifact_inventory", [])
    if len(inventory) != len(set(inventory)):
        raise FrameworkError("Target plan artifact inventory contains duplicates")
    unresolved_inventory = [
        relative
        for relative in inventory
        if not contained_path(
            application_root, relative, "planned artifact"
        ).is_file()
    ]
    if unresolved_inventory:
        raise FrameworkError(
            f"Target application is missing planned artifacts: {unresolved_inventory}"
        )
    missing_from_plan = sorted(
        set(required_records) - set(plan.get("artifact_inventory", []))
    )
    if missing_from_plan:
        raise FrameworkError(
            f"Target plan omits required artifact records: {missing_from_plan}"
        )
    expected_manifest_record = contract.get("manifest_record")
    if manifest_record != expected_manifest_record:
        raise FrameworkError(
            "Application result manifest differs from the artifact contract"
        )
    manifest_path = resolved_records.get(expected_manifest_record)
    if manifest_path is None:
        raise FrameworkError("Target artifact contract declares no application manifest")
    manifest = read_json_object(manifest_path, "application manifest")
    missing_fields = [field for field in required_fields if field not in manifest]
    if missing_fields:
        raise FrameworkError(
            f"Application manifest is missing required fields: {missing_fields}"
        )
    profile_id = target_profile_id(planning, plan)
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
        raise FrameworkError(f"Application manifest identity fields differ: {mismatched}")

    entry_point = manifest.get("entry_point")
    if not isinstance(entry_point, str) or not contained_path(
        application_root, entry_point, "entry point"
    ).is_file():
        raise FrameworkError("Application manifest entry point does not resolve")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise FrameworkError("Application manifest declares no artifacts")
    unresolved_artifacts = [
        item
        for item in artifacts
        if not isinstance(item, str)
        or not contained_path(application_root, item, "declared artifact").is_file()
    ]
    if unresolved_artifacts:
        raise FrameworkError(
            f"Application manifest artifacts do not resolve: {unresolved_artifacts}"
        )
    if len(artifacts) != len(set(artifacts)):
        raise FrameworkError("Application manifest artifacts contain duplicates")
    expected_manifest_artifacts = set(inventory) - {expected_manifest_record}
    if set(artifacts) != expected_manifest_artifacts:
        raise FrameworkError(
            "Application manifest artifacts differ from the target plan inventory"
        )
    if entry_point not in set(artifacts):
        raise FrameworkError("Application entry point is absent from artifact inventory")
    dependencies = manifest.get("dependencies")
    dependency_fields = contract.get("dependency_fields", [])
    if not isinstance(dependencies, list) or not all(
        isinstance(record, dict)
        and all(
            isinstance(record.get(field), str) and record[field]
            for field in dependency_fields
        )
        for record in dependencies
    ):
        raise FrameworkError("Application manifest dependency provenance is incomplete")
    if dependencies != plan.get("dependencies"):
        raise FrameworkError("Application and plan dependency provenance differ")

    validation_evidence = manifest.get("validation_evidence")
    if not isinstance(validation_evidence, list) or not all(
        isinstance(item, str) and item for item in validation_evidence
    ):
        raise FrameworkError("Application manifest validation evidence is invalid")
    missing_evidence_refs = sorted(set(pass_records) - set(validation_evidence))
    if missing_evidence_refs:
        raise FrameworkError(
            f"Application manifest omits required evidence: {missing_evidence_refs}"
        )
    for relative in validation_evidence:
        if relative not in set(artifacts):
            raise FrameworkError(
                f"Validation evidence is absent from artifact inventory: {relative}"
            )
        if not contained_path(
            application_root, relative, "validation evidence"
        ).is_file():
            raise FrameworkError(f"Validation evidence does not resolve: {relative}")

    validation_extension = load_validation_extension(
        contract, "validate_application_evidence"
    )
    target_validation = validation_extension.validate_application_evidence(
        planning=planning,
        plan=plan,
        application_root=application_root,
        manifest=manifest,
        artifacts=set(artifacts),
        resolved_records=resolved_records,
    )
    evidence_check_statuses = target_validation["check_statuses"]
    evidence_summaries = target_validation["evidence"]

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
        raise FrameworkError("Application manifest requirement traceability is incomplete")
    trace_ids = {record["requirement_id"] for record in traceability}
    pivotal_requirements = pivotal_requirement_ids(planning)
    missing_traceability = sorted(pivotal_requirements - trace_ids)
    if missing_traceability:
        raise FrameworkError(
            f"Application manifest omits pivotal requirements: {missing_traceability}"
        )
    for record in traceability:
        if record["artifact"] not in set(artifacts):
            raise FrameworkError(
                "Traceability artifact is absent from artifact inventory: "
                f"{record['artifact']}"
            )
        if not contained_path(
            application_root, record["artifact"], "traceability artifact"
        ).is_file():
            raise FrameworkError(
                f"Traceability artifact does not resolve: {record['artifact']}"
            )
        if evidence_check_statuses.get(record["check"]) != "passed":
            raise FrameworkError(
                "Traceability check is absent or did not pass in evidence: "
                f"{record['check']}"
            )

    coordinator_checks = [
        {"id": "entry-point-resolves", "status": "passed"},
        {"id": "manifest-paths-resolve", "status": "passed"},
        {"id": "dependency-and-license-provenance", "status": "passed"},
    ] + target_validation.get("coordinator_checks", [])
    return {
        "status": "artifact-contract-validated",
        "plan_contract_id": planning.plan_contract.get("contract_id"),
        "artifact_contract_id": contract.get("contract_id"),
        "profile_id": profile_id,
        "target_requirement_coverage": target_requirement_coverage(plan),
        "required_record_count": len(required_records),
        "evidence": evidence_summaries,
        "coordinator_checks": coordinator_checks,
        "pass": True,
    }
