#!/usr/bin/env python3
"""Source-checkout entry point for the Scientific Representation framework."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scientific_representation.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
