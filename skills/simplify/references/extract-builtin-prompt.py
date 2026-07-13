#!/usr/bin/env python3
"""Extract a built-in slash command prompt from the Claude Code CLI bundle.

Usage:
    python3 extract-builtin-prompt.py BUNDLE [--marker MARKER]

    BUNDLE  Path to the Claude Code CLI bundle.
    MARKER  Heading that starts the prompt (default: "# Simplify: Code Review and Cleanup").

Example:
    python3 extract-builtin-prompt.py /path/to/claude-code/cli.js
    python3 extract-builtin-prompt.py /path/to/claude-code/cli.js --marker "# Simplify"
"""

import argparse
import re
import sys
from typing import Optional

DEFAULT_MARKER = "# Simplify: Code Review and Cleanup"


def extract(path: str, marker: str) -> str:
    with open(path) as f:
        content = f.read()

    start = content.find(marker)
    if start == -1:
        raise ValueError(f"Marker not found: {marker!r}")

    i = start
    while i < len(content):
        c = content[i]
        if c == "\\":
            i += 2
            continue
        if c == "`":
            break
        i += 1

    raw = content[start:i]
    return re.sub(r"\\(.)", lambda m: m.group(1), raw)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", help="path to the Claude Code CLI bundle")
    parser.add_argument("--marker", default=DEFAULT_MARKER, help="prompt heading to extract")
    args = parser.parse_args(argv)

    try:
        print(extract(args.bundle, args.marker))
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
