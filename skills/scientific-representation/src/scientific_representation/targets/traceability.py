"""Shared target identity and pivotal-requirement traceability helpers."""

from __future__ import annotations

from typing import Any

from ..domain import FrameworkError
from ..ports import TargetPlanningRequest


def target_profile_id(
    planning: TargetPlanningRequest, plan: dict[str, Any]
) -> Any:
    field = str(planning.plan_contract.get("profile_field", "toolchain_profile_id"))
    return plan.get(field)


def pivotal_requirement_ids(planning: TargetPlanningRequest) -> set[str]:
    requirement_ids: set[str] = set()
    hypotheses = planning.representation_intent.get("pivotal_hypotheses", [])
    if not isinstance(hypotheses, list):
        raise FrameworkError("Representation intent pivotal hypotheses must be a list")
    for hypothesis in hypotheses:
        if not isinstance(hypothesis, dict):
            continue
        references = hypothesis.get("requirement_refs", [])
        if not isinstance(references, list):
            raise FrameworkError("Pivotal requirement references must be a list")
        requirement_ids.update(
            reference
            for reference in references
            if isinstance(reference, str) and reference
        )
    if not requirement_ids:
        raise FrameworkError(
            "Representation intent has no pivotal requirement references"
        )
    return requirement_ids


def target_requirement_coverage(plan: dict[str, Any]) -> str:
    """Summarize explicit plan coverage without judging scientific adequacy."""

    statuses = {
        record.get("status")
        for record in plan.get("requirement_capability_coverage", [])
        if isinstance(record, dict)
    }
    if "unmet" in statuses or plan.get("unmet_requirements"):
        return "unmet"
    if "conditional" in statuses:
        return "conditional"
    return "covered"
