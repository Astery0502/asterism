"""Scientific HTML target-definition evidence and web-asset validation."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from scientific_representation.domain import FrameworkError
from scientific_representation.ports import TargetPlanningRequest
from scientific_representation.targets.validation_support import (
    contained_path,
    read_json_object,
)


def validate_application_evidence(
    *,
    planning: TargetPlanningRequest,
    plan: dict[str, Any],
    application_root: Path,
    manifest: dict[str, Any],
    artifacts: set[str],
    resolved_records: dict[str, Path],
) -> dict[str, Any]:
    """Validate Scientific HTML evidence, recipes, and local web assets."""

    contract = planning.artifact_contract
    pass_records = contract.get("required_pass_records", [])
    verification_paths = {
        plan.get("verification", {}).get("numerical"),
        plan.get("verification", {}).get("browser"),
    }
    if verification_paths != set(pass_records):
        raise FrameworkError(
            "Target plan verification paths do not match the artifact contract"
        )

    entry_point = manifest["entry_point"]
    referenced_assets = validate_asset_closure(
        application_root,
        entry_point,
        artifacts,
        offline=plan.get("delivery", {}).get("connectivity") == "offline",
    )
    level = plan.get("verification", {}).get(
        "level", contract.get("default_verification_level", "fast")
    )
    level_checks = contract.get("verification_levels", {}).get(level)
    if not isinstance(level_checks, dict):
        raise FrameworkError(
            f"Application selects an unknown verification level: {level}"
        )

    statuses: dict[str, str] = {}
    summaries: list[dict[str, Any]] = []
    for relative in pass_records:
        path = resolved_records.get(relative) or contained_path(
            application_root, relative, "evidence record"
        )
        summary = validate_evidence_record(
            path,
            relative,
            contract.get("evidence_record_contract", {}),
            level_checks,
            contract.get("structured_check_details", {}),
            application_root,
            planning=planning,
            plan=plan,
        )
        summaries.append(summary)
        for check_id, status in summary["check_statuses"].items():
            if check_id in statuses and statuses[check_id] != status:
                raise FrameworkError(
                    f"Evidence check status is inconsistent: {check_id}"
                )
            statuses[check_id] = status

    reported_assets = {
        item for summary in summaries for item in summary["asset_references"]
    }
    if "assets-resolve" in statuses and reported_assets != set(referenced_assets):
        raise FrameworkError(
            "Browser asset ledger differs from the statically resolved asset closure"
        )
    observed_requests = {
        item for summary in summaries for item in summary["observed_local_requests"]
    }
    undeclared_requests = sorted(observed_requests - artifacts)
    if undeclared_requests:
        raise FrameworkError(
            "Browser requested local assets absent from artifact inventory: "
            f"{undeclared_requests}"
        )
    request_counts = [
        count for summary in summaries for count in summary["asset_request_counts"]
    ]
    if request_counts and any(count < len(observed_requests) for count in request_counts):
        raise FrameworkError(
            "Browser asset request count is smaller than its observed local ledger"
        )
    evidence_artifacts = {
        item for summary in summaries for item in summary["artifacts"]
    }
    undeclared_attachments = sorted(evidence_artifacts - artifacts)
    if undeclared_attachments:
        raise FrameworkError(
            "Evidence attachments are absent from artifact inventory: "
            f"{undeclared_attachments}"
        )
    return {
        "check_statuses": statuses,
        "evidence": summaries,
        "coordinator_checks": [
            {"id": "local-asset-closure-resolves", "status": "passed"}
        ],
    }


def validate_evidence_record(
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
        raise FrameworkError(f"Target application evidence is missing: {relative}")
    record = read_json_object(path, relative)
    required_record_fields = evidence_contract.get("required_record_fields", [])
    if any(field not in record for field in required_record_fields):
        raise FrameworkError(f"Evidence record is incomplete: {relative}")
    if record.get("schema_version") != evidence_contract.get("schema_version"):
        raise FrameworkError(f"Evidence schema version is invalid: {relative}")
    expected_type = evidence_contract.get("record_types", {}).get(relative)
    if record.get("record_type") != expected_type:
        raise FrameworkError(f"Evidence record type is invalid: {relative}")
    runner = record.get("runner")
    if not isinstance(runner, str) or not runner:
        raise FrameworkError(f"Evidence runner is invalid: {relative}")
    if (
        expected_type == "browser"
        and runner
        != planning.capability_catalog.get("verification_requirements", {}).get(
            "runner"
        )
    ):
        raise FrameworkError(
            f"Browser evidence runner differs from the target contract: {relative}"
        )
    if record.get("pass") is not True:
        raise FrameworkError(f"Target application evidence did not pass: {relative}")
    checks = record.get("checks")
    check_fields = evidence_contract.get("required_check_fields", [])
    if not isinstance(checks, list) or not checks or not all(
        isinstance(check, dict)
        and all(field in check for field in check_fields)
        for check in checks
    ):
        raise FrameworkError(f"Evidence checks are incomplete: {relative}")
    if not all(
        isinstance(check["id"], str)
        and check["id"]
        and isinstance(check["status"], str)
        and check["status"]
        for check in checks
    ):
        raise FrameworkError(f"Evidence check identities are invalid: {relative}")
    check_ids = [check["id"] for check in checks]
    if len(check_ids) != len(set(check_ids)):
        raise FrameworkError(f"Evidence check IDs are not unique: {relative}")
    required_categories = evidence_contract.get("coverage", {}).get(relative, [])
    required_ids = {
        check_id
        for category in required_categories
        for check_id in mechanical_checks.get(category, [])
    }
    missing_ids = sorted(required_ids - set(check_ids))
    if missing_ids:
        raise FrameworkError(
            f"Evidence record omits declared checks in {relative}: {missing_ids}"
        )
    accepted_statuses = set(evidence_contract.get("accepted_statuses", []))
    for check in checks:
        if check["status"] not in accepted_statuses:
            raise FrameworkError(
                f"Evidence check status is invalid in {relative}: {check['id']}"
            )
        if not isinstance(check["method"], str) or not check["method"]:
            raise FrameworkError(f"Evidence check method is empty: {check['id']}")
        if not isinstance(check["details"], dict) or not check["details"]:
            raise FrameworkError(f"Evidence check details are empty: {check['id']}")
        applicable = _check_is_applicable(check["id"], planning, plan)
        if applicable and check["status"] != "passed":
            raise FrameworkError(
                f"Required evidence check did not pass in {relative}: {check['id']}"
            )
        if not applicable and check["status"] != "not_applicable":
            raise FrameworkError(
                f"Conditional evidence status differs from the plan in {relative}: "
                f"{check['id']}"
            )
        if check["status"] == "not_applicable":
            justification = check["details"].get("justification")
            if not isinstance(justification, str) or not justification:
                raise FrameworkError(
                    f"Evidence check cannot be not_applicable in {relative}: "
                    f"{check['id']}"
                )
        _validate_structured_check_details(check, plan, structured_check_details)
        evidence_artifacts = check.get("artifacts", [])
        if not isinstance(evidence_artifacts, list) or not all(
            isinstance(item, str)
            and contained_path(application_root, item, "evidence artifact").is_file()
            for item in evidence_artifacts
        ):
            raise FrameworkError(f"Evidence artifacts are invalid: {check['id']}")
        if check["id"] == "review-screenshot" and not evidence_artifacts:
            raise FrameworkError("Review-screenshot evidence declares no screenshot")
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
        raise FrameworkError(
            f"Structured evidence details are incomplete: {check_id}"
        )
    if check_id == "fresh-load" and (
        details.get("loaded") is not True
        or details.get("document_ready_state") not in {"interactive", "complete"}
    ):
        raise FrameworkError("Fresh-load evidence has no successful browser state")
    if check_id == "primary-view-exposure" and (
        details.get("scientific_object_visible") is not True
        or details.get("primary_contrast_visible") is not True
        or details.get("observable_response_visible") is not True
        or details.get("primary_elements_co_visible") is not True
    ):
        raise FrameworkError(
            "Primary-view evidence does not expose the declared explanatory elements"
        )
    if check_id == "no-console-errors" and details.get("console_errors") != []:
        raise FrameworkError("No-console-errors evidence reports browser errors")
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
        raise FrameworkError("Assets-resolve evidence lacks a clean request ledger")
    if check_id == "offline-network-block-when-declared" and (
        plan.get("delivery", {}).get("connectivity") == "offline"
        and (
            details.get("network_blocked") is not True
            or details.get("unexpected_requests") != []
        )
    ):
        raise FrameworkError("Offline evidence does not demonstrate a blocked network")
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
        raise FrameworkError(
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
        raise FrameworkError(
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
            raise FrameworkError(
                "Review-screenshot evidence does not map every declared anchor"
            )



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
    if check_id in applicability:
        return applicability[check_id]
    if check_id == "control-causes-expected-state-change":
        return bool(
            plan.get("interface", {}).get("controls") or plan.get("interactions")
        )
    return True


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


def validate_asset_closure(
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
        source = contained_path(application_root, relative, "web asset")
        if source.suffix.lower() not in scannable_suffixes:
            continue
        try:
            content = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise FrameworkError(f"Web asset cannot be inspected: {relative}: {exc}") from exc
        references = _extract_asset_references(source.suffix.lower(), content)
        for reference in references:
            resolved = _resolve_asset_reference(
                application_root, source, reference, offline=offline
            )
            if resolved is None:
                continue
            resolved_relative = resolved.relative_to(application_root.resolve()).as_posix()
            if resolved_relative not in declared_artifacts:
                raise FrameworkError(
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
            raise FrameworkError(
                f"Offline application references a network asset: {reference}"
            )
        return None
    if parsed.scheme:
        raise FrameworkError(
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
        raise FrameworkError(
            f"Web asset reference leaves the application root: {reference}"
        ) from exc
    if candidate.is_dir():
        candidate = candidate / "index.html"
    if not candidate.is_file():
        raise FrameworkError(f"Referenced web asset does not resolve: {reference}")
    return candidate


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise FrameworkError(f"Evidence contains a non-JSON anchor: {exc}") from exc


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )
