"""Create a writable workspace from the embedded representation framework."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_SNAPSHOT = SKILL_ROOT / "assets" / "prototype"


def create_workspace(destination: Path) -> dict[str, object]:
    destination = destination.resolve()
    if destination.exists():
        raise SystemExit(f"Workspace destination already exists: {destination}")
    if not (PROTOTYPE_SNAPSHOT / "prototype.json").is_file():
        raise SystemExit(
            f"Embedded framework snapshot is incomplete: {PROTOTYPE_SNAPSHOT}"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        PROTOTYPE_SNAPSHOT,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    (destination / "work").mkdir(exist_ok=True)
    files = [path for path in destination.rglob("*") if path.is_file()]
    return {
        "pass": True,
        "workspace": str(destination),
        "prototype_version": json.loads(
            (destination / "prototype.json").read_text(encoding="utf-8")
        )["application_version"],
        "file_count": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "default_target": "scientific-html",
        "next": [
            (
                "Preserve the scientific source and presentation direction "
                "as separate inputs."
            ),
            (
                "Read AGENTS.md, the analysis guide, method.json, the "
                "Scientific HTML guide, and its contracts in order."
            ),
            "Inspect Scientific HTML readiness with prototype.py doctor.",
            "Execute the complete Agent workflow under work/<case>/.",
            (
                "Run fast verification and deliver "
                "work/<case>/application/product/index.html."
            ),
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a scientific-representation workspace."
    )
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(create_workspace(args.destination), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
