#!/usr/bin/env python3
"""
nexus_install.py — copy .nexus/ scaffold files into a target repository.

Usage:
    python nexus_install.py [--target /path/to/repo] [--confirm]

Output lines:
    AWAITING_CONFIRM          # printed then script exits when partial + no --confirm
    CREATED: .nexus/...
    SKIPPED: .nexus/...
    SYNC_ROUTES_CREATED: true|false
    DONE
"""

import argparse
import shutil
import sys
from pathlib import Path

from nexus_status import classify, collect_template_files, template_to_target_rel

SHEBANG = "#!/usr/bin/env python3\n"


def ensure_shebang(path: Path) -> None:
    text = path.read_text()
    if not text.startswith("#!"):
        path.write_text(SHEBANG + text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold .nexus/ into a repository.")
    parser.add_argument("--target", default=".", help="Target repository root (default: cwd)")
    parser.add_argument("--confirm", action="store_true", help="Proceed without prompting on partial state")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    template_nexus = script_dir.parent / "template" / ".nexus"
    target = Path(args.target).resolve()

    if not template_nexus.is_dir():
        print(f"ERROR: template not found at {template_nexus}", file=sys.stderr)
        sys.exit(1)

    state, existing, missing = classify(template_nexus, target)

    if state == "partial" and not args.confirm:
        print("AWAITING_CONFIRM")
        return

    sync_routes_created = False
    for tf in collect_template_files(template_nexus):
        rel = template_to_target_rel(tf, template_nexus)
        dest = target / rel
        if dest.exists():
            print(f"SKIPPED: {rel}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tf, dest)
        if dest.suffix == ".py":
            ensure_shebang(dest)
        if rel == Path(".nexus/scripts/sync_routes.py"):
            sync_routes_created = True
        print(f"CREATED: {rel}")

    print(f"SYNC_ROUTES_CREATED: {'true' if sync_routes_created else 'false'}")
    print("DONE")


if __name__ == "__main__":
    main()
