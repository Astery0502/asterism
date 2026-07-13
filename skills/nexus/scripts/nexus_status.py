#!/usr/bin/env python3
"""
nexus_status.py — report scaffold state for a target repository.

Usage:
    python nexus_status.py [--target /path/to/repo]

Output lines:
    STATE: fresh|partial|complete
    WILL_CREATE: .nexus/...    # only when partial
    WILL_SKIP: .nexus/...      # only when partial
"""

import argparse
import sys
from pathlib import Path


def collect_template_files(template_dir: Path) -> list[Path]:
    return sorted(p for p in template_dir.rglob("*") if p.is_file() and p.name != ".DS_Store")


def template_to_target_rel(template_file: Path, template_nexus: Path) -> Path:
    return template_file.relative_to(template_nexus.parent)


def classify(template_nexus: Path, target: Path) -> tuple[str, list[Path], list[Path]]:
    """Return (state, existing_targets, missing_targets)."""
    template_files = collect_template_files(template_nexus)
    existing, missing = [], []
    for tf in template_files:
        rel = template_to_target_rel(tf, template_nexus)
        dest = target / rel
        (existing if dest.exists() else missing).append(tf)
    if not existing and not (target / ".nexus").is_dir():
        state = "fresh"
    elif not missing:
        state = "complete"
    else:
        state = "partial"
    return state, existing, missing


def main() -> None:
    parser = argparse.ArgumentParser(description="Report .nexus/ scaffold state.")
    parser.add_argument("--target", default=".", help="Target repository root (default: cwd)")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    template_nexus = script_dir.parent / "template" / ".nexus"
    target = Path(args.target).resolve()

    if not template_nexus.is_dir():
        print(f"ERROR: template not found at {template_nexus}", file=sys.stderr)
        sys.exit(1)

    # Fast path: no .nexus/ dir at all
    if not (target / ".nexus").is_dir():
        print("STATE: fresh")
        return

    state, existing, missing = classify(template_nexus, target)
    print(f"STATE: {state}")

    if state == "partial":
        for tf in missing:
            print(f"WILL_CREATE: {template_to_target_rel(tf, template_nexus)}")
        for tf in existing:
            print(f"WILL_SKIP: {template_to_target_rel(tf, template_nexus)}")


if __name__ == "__main__":
    main()
