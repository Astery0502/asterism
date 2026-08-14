"""Validate an Agent-produced Scientific HTML work case.

The script intentionally assumes only the small consumer workspace convention
documented by the prototype.  It does not prescribe an HTML template, a model
shape, or a visualization grammar.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROTOTYPE_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROTOTYPE_ROOT))

from portable_prototype import PrototypeApp  # noqa: E402
from portable_prototype.targets.contracts import (  # noqa: E402
    validate_target_application,
    validate_target_plan,
    validate_target_plan_implementation_ready,
)
from portable_prototype.targets.realization import TargetPlanningRequest  # noqa: E402


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SystemExit(f"Missing required work-product file: {path}") from error
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid JSON in work-product file: {path}: {error}") from error
    if not isinstance(value, dict):
        raise SystemExit(f"Work-product JSON must contain an object: {path}")
    return value


def validate_work_product(case_root: Path) -> dict:
    """Validate one conventional work case and return the contract receipt."""

    case_root = case_root.resolve()
    app = PrototypeApp(PROTOTYPE_ROOT)
    context = app._target_planning_context("scientific-html")
    intent = _read_json(
        case_root / "representation" / "representation-intent.json"
    )
    planning = TargetPlanningRequest(
        target="scientific-html",
        theoretical_account=(
            case_root / "analysis" / "theoretical-account.md"
        ).read_text(encoding="utf-8"),
        representation_intent_id=intent["intent_id"],
        requirements_id=intent["requirements_id"],
        representation_intent=intent,
        requirements_markdown=(
            case_root / "representation" / "representation-requirements.md"
        ).read_text(encoding="utf-8"),
        interface_spec=_read_json(
            case_root / "representation" / "representation-interface.json"
        ),
        capability_catalog=context["capabilities"],
        runtime_observation=context["runtime_observation"],
        plan_contract=context["plan_contract"],
        artifact_contract=context["artifact_contract"],
    )
    plan = _read_json(
        case_root / "targets" / "scientific-html" / "native-plan.json"
    )
    validate_target_plan(planning, plan)
    validate_target_plan_implementation_ready(planning, plan)
    receipt = validate_target_application(
        planning,
        plan,
        {"pass": True},
        case_root / "application",
    )
    entry_point = case_root / "application" / "product" / "index.html"
    return {
        "pass": bool(receipt.get("pass")),
        "case": case_root.name,
        "plan": plan["plan_id"],
        "contract_validation": receipt,
        "entry_point": str(entry_point),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a conventional Scientific HTML work product."
    )
    parser.add_argument(
        "case_root",
        type=Path,
        help=(
            "Path to work/<case> containing analysis, representation, target, "
            "and application records."
        ),
    )
    parser.add_argument(
        "--write-receipt",
        action="store_true",
        help="Also write the result to <case-root>/trial-result.json.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    result = validate_work_product(args.case_root)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.write_receipt:
        (args.case_root.resolve() / "trial-result.json").write_text(
            rendered, encoding="utf-8"
        )
    print(rendered, end="")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
