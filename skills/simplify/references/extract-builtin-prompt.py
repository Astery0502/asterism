#!/usr/bin/env python3
"""Extract a built-in slash command prompt from the Claude Code CLI bundle.

Usage:
    python3 extract-builtin-prompt.py [marker]

    marker  The heading that starts the prompt (default: "# Simplify: Code Review and Cleanup")

Example:
    python3 extract-builtin-prompt.py
    python3 extract-builtin-prompt.py "# Simplify"
"""

import re
import sys

CLI = "/usr/local/lib/node_modules/@anthropic-ai/claude-code/cli.js"
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


if __name__ == "__main__":
    marker = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MARKER
    print(extract(CLI, marker))
