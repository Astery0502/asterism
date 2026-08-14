"""Command-line delivery adapter for the integrated prototype."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .app import PrototypeApp
from .models import PrototypeError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prototype",
        description="Portable equation-analysis to scientific-representation application",
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="Prototype root containing prototype.json (defaults to this application)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available scientific cases")
    _json_flag(list_parser)

    method_parser = subparsers.add_parser(
        "method", help="Describe the target-agnostic scientific representation method"
    )
    _json_flag(method_parser)

    targets = subparsers.add_parser(
        "targets", help="Inspect target capabilities and local toolchain readiness"
    )
    targets.add_argument("target", nargs="?")
    _json_flag(targets)

    describe = subparsers.add_parser("describe", help="Describe all layers of one case")
    describe.add_argument("case")
    describe.add_argument("--target")
    _json_flag(describe)

    analysis = subparsers.add_parser(
        "analysis", help="Describe only the mathematical-physics analysis phase"
    )
    analysis.add_argument("case")
    _json_flag(analysis)

    representation = subparsers.add_parser(
        "representation",
        help="Describe the independent requirements-to-realization phase",
    )
    representation.add_argument("case")
    representation.add_argument("--target")
    _json_flag(representation)

    doctor = subparsers.add_parser("doctor", help="Inspect target runtime availability")
    doctor.add_argument("--target")
    _json_flag(doctor)

    validate = subparsers.add_parser("validate", help="Validate catalog and native plans")
    validate.add_argument("selector", nargs="?", default="all")
    validate.add_argument("--target")
    validate.add_argument(
        "--structural-only",
        action="store_true",
        help="Check the portable catalog and files without starting the target runtime",
    )
    _json_flag(validate)

    test = subparsers.add_parser("test", help="Build and run behavior-equivalence tests")
    test.add_argument("selector", nargs="?", default="all")
    test.add_argument("--target")
    _json_flag(test)

    build = subparsers.add_parser(
        "build", help="Materialize target applications and review artifacts"
    )
    build.add_argument("selector", nargs="?", default="all")
    build.add_argument("--target")
    build.add_argument("--output", type=Path)
    build.add_argument("--recompute-data", action="store_true")
    _json_flag(build)

    run = subparsers.add_parser(
        "run", help="Build a case and return its researcher entry point"
    )
    run.add_argument("case")
    run.add_argument("--target")
    run.add_argument("--output", type=Path)
    run.add_argument("--recompute-data", action="store_true")
    _json_flag(run)

    bundle = subparsers.add_parser("bundle", help="Create a movable copy of the prototype")
    bundle.add_argument("destination", type=Path)
    bundle.add_argument(
        "--profile", choices=("source", "runtime", "archive"), default="runtime"
    )
    _json_flag(bundle)

    realize = subparsers.add_parser(
        "realize",
        help="Orchestrate raw input through analysis and representation stages",
    )
    realize.add_argument("raw_input", type=Path)
    presentation = realize.add_mutually_exclusive_group()
    presentation.add_argument("--presentation-question")
    presentation.add_argument("--presentation-question-file", type=Path)
    presentation.add_argument("--direction")
    presentation.add_argument("--direction-file", type=Path)
    analysis_question = realize.add_mutually_exclusive_group()
    analysis_question.add_argument("--analysis-question")
    analysis_question.add_argument("--analysis-question-file", type=Path)
    realize.add_argument("--output", type=Path, required=True)
    realize.add_argument(
        "--provider",
        required=True,
        help="Injected scientific provider",
    )
    realize.add_argument(
        "--realizer",
        help="Optional injected target translator/implementer",
    )
    realize.add_argument("--reference-case")
    realize.add_argument(
        "--target",
        help="Visualization target (defaults to scientific-html)",
    )
    realize.add_argument(
        "--stop-after",
        choices=("analysis", "requirements", "application"),
        default="application",
    )
    _json_flag(realize)

    realize_account = subparsers.add_parser(
        "realize-account",
        help="Form requirements from an existing TheoreticalAccount",
    )
    realize_account.add_argument("account_workspace", type=Path)
    question = realize_account.add_mutually_exclusive_group(required=True)
    question.add_argument("--presentation-question")
    question.add_argument("--presentation-question-file", type=Path)
    realize_account.add_argument("--provider", required=True)
    realize_account.add_argument("--reference-case")
    realize_account.add_argument("--output", type=Path, required=True)
    _json_flag(realize_account)

    realize_target = subparsers.add_parser(
        "realize-target",
        help="Resume from persisted requirements without rerunning analysis",
    )
    realize_target.add_argument("requirements_workspace", type=Path)
    realize_target.add_argument("--target", required=True)
    realize_target.add_argument("--realizer", required=True)
    realize_target.add_argument("--output", type=Path, required=True)
    _json_flag(realize_target)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        app = PrototypeApp(args.root)
        result = _dispatch(app, args)
    except PrototypeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130

    if getattr(args, "json", False):
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _print_human(args.command, result)
    return 0 if result.get("pass", True) else 1


def _dispatch(app: PrototypeApp, args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "list":
        return {"operation": "list", "pass": True, "cases": app.list_cases()}
    if args.command == "method":
        return {"operation": "method", "pass": True, "method": app.describe_method()}
    if args.command == "targets":
        return {
            "operation": "targets",
            "pass": True,
            "targets": (
                [app.describe_target(args.target)]
                if args.target is not None
                else app.list_targets()
            ),
        }
    if args.command == "describe":
        return {
            "operation": "describe",
            "pass": True,
            "case": app.describe_case(args.case, args.target),
        }
    if args.command == "analysis":
        return {
            "operation": "analysis",
            "pass": True,
            "analysis": app.describe_analysis(args.case),
        }
    if args.command == "representation":
        return {
            "operation": "representation",
            "pass": True,
            "representation": app.describe_representation(args.case, args.target),
        }
    if args.command == "doctor":
        result = app.doctor(args.target)
        result.update({"operation": "doctor", "pass": result["target"]["available"]})
        return result
    if args.command == "validate":
        return app.validate(
            args.selector,
            target=args.target,
            structural_only=args.structural_only,
        )
    if args.command == "test":
        return app.test(args.selector, target=args.target)
    if args.command in {"build", "run"}:
        selector = args.case if args.command == "run" else args.selector
        result = app.build(
            selector,
            target=args.target,
            output_root=args.output,
            recompute_data=args.recompute_data,
        )
        if args.command == "run":
            result["operation"] = "run"
            case_result = result["results"][0]
            entry_point = case_result.get("entry_point") or case_result.get("notebook")
            if not entry_point:
                raise PrototypeError("Built application declares no entry point")
            result["entry_point"] = entry_point
            if case_result.get("notebook"):
                result["entry_notebook"] = case_result["notebook"]
        return result
    if args.command == "bundle":
        return app.bundle(args.destination, profile=args.profile)
    if args.command == "realize":
        presentation_question = args.presentation_question or args.direction
        question_file = args.presentation_question_file or args.direction_file
        if question_file is not None:
            presentation_question = _read_text(question_file, "presentation question")
        analysis_question = args.analysis_question
        if args.analysis_question_file is not None:
            analysis_question = _read_text(
                args.analysis_question_file, "analysis question"
            )
        return app.realize(
            args.raw_input,
            presentation_question,
            args.output,
            provider=args.provider,
            realizer=args.realizer,
            reference_case=args.reference_case,
            target=args.target,
            stop_after=args.stop_after,
            analysis_question=analysis_question,
            presentation_question=presentation_question,
        )
    if args.command == "realize-account":
        presentation_question = args.presentation_question
        if args.presentation_question_file is not None:
            presentation_question = _read_text(
                args.presentation_question_file, "presentation question"
            )
        return app.realize_account(
            args.account_workspace,
            args.output,
            presentation_question=presentation_question,
            provider=args.provider,
            reference_case=args.reference_case,
        )
    if args.command == "realize-target":
        return app.realize_requirements(
            args.requirements_workspace,
            args.output,
            target=args.target,
            realizer=args.realizer,
        )
    raise PrototypeError(f"Unsupported command: {args.command}")


def _json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Emit structured JSON")


def _read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise PrototypeError(f"Could not read {label}: {exc}") from exc


def _print_human(command: str, result: dict[str, Any]) -> None:
    if command == "list":
        for case in result["cases"]:
            print(f"{case['id']:<32} {case['title']}  [{', '.join(case['targets'])}]")
        return
    if command == "describe":
        print(json.dumps(result["case"], indent=2, ensure_ascii=False))
        return
    if command == "targets":
        for target in result["targets"]:
            runtime = target.get("runtime", {})
            readiness = (
                "ready"
                if runtime.get("available")
                else (
                    "build-only"
                    if runtime.get("build_ready")
                    else "planning-only"
                )
            )
            print(
                f"{target['id']:<24} {target.get('display_name', '')} "
                f"[{readiness}; {len(target.get('realized_cases', []))} realized cases]"
            )
        return
    if command == "doctor":
        target = result["target"]
        print(f"Prototype root: {result['prototype_root']}")
        print(f"Target: {target['display_name']}")
        print(f"Available: {target['available']}")
        print(f"Executable: {target['executable']}")
        print(f"Version: {target['version']}")
        if "build_ready" in target:
            print(f"Default profile build-ready: {target['build_ready']}")
            print(
                "Default profile verification-ready: "
                f"{target['verification_ready']}"
            )
        return
    if command == "validate":
        state = "PASS" if result["pass"] else "FAIL"
        print(
            f"Validation {state}: {result['selector']} on {result['target']} "
            f"({result['error_count']} errors, {result['warning_count']} warnings)"
        )
        for finding in result["findings"]:
            location = f" [{finding.get('case_id')}]" if finding.get("case_id") else ""
            print(f"- {finding['severity'].upper()}{location} {finding['message']}")
        for target_result in result["target_results"]:
            runtime = target_result.get("runtime") or {}
            runtime_passed = runtime.get("Pass", runtime.get("pass"))
            print(
                f"- {target_result['case_id']}: target plan "
                f"{'PASS' if runtime_passed else 'FAIL'}"
            )
        return
    if command == "test":
        print(f"Tests {'PASS' if result['pass'] else 'FAIL'}: {result['case_count']} cases")
        for case in result["results"]:
            focused = case["focused_tests"]
            self_count = sum(item.get("succeeded") or 0 for item in case["self_tests"])
            aggregated = focused.get("AggregateOf") == "self_tests"
            suffix = (
                f", {self_count} self-tests"
                if case["self_tests"] and not aggregated
                else ""
            )
            label = "target checks" if aggregated else "focused tests"
            print(
                f"- {case['case_id']}: {focused.get('Succeeded', 0)} {label}{suffix} "
                f"({'PASS' if case['pass'] else 'FAIL'})"
            )
        return
    if command in {"build", "run"}:
        print(f"Build {'PASS' if result['pass'] else 'FAIL'}: {result['output_root']}")
        for case in result["results"]:
            entry_point = case.get("entry_point") or case.get("notebook")
            print(f"- {case['case_id']}: {entry_point}")
        if command == "run":
            print(f"Researcher entry point: {result['entry_point']}")
        return
    if command == "bundle":
        print(
            f"Bundle PASS: {result['destination']} "
            f"({result['profile']}, {result['file_count']} files, {result['bytes']} bytes)"
        )
        return
    if command in {"realize", "realize-account", "realize-target"}:
        print(
            f"Realization {'PASS' if result['pass'] else 'FAIL'}: "
            f"{result['workspace']}"
        )
        print(f"Completed stages: {', '.join(result['completed_stages'])}")


if __name__ == "__main__":
    raise SystemExit(main())
