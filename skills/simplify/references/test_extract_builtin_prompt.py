#!/usr/bin/env python3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("extract-builtin-prompt.py")
MARKER = "# Simplify: Code Review and Cleanup"


class ExtractBuiltinPromptTest(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_extracts_prompt_from_explicit_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "cli.js"
            bundle.write_text(f"const prompt = `{MARKER}\nReview changes.`;", encoding="utf-8")

            result = self.run_script(str(bundle))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f"{MARKER}\nReview changes.\n")

    def test_reports_missing_bundle(self) -> None:
        result = self.run_script("/path/that/does/not/exist/cli.js")

        self.assertEqual(result.returncode, 1)
        self.assertIn("No such file or directory", result.stderr)

    def test_reports_missing_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "cli.js"
            bundle.write_text("const prompt = `different`;", encoding="utf-8")

            result = self.run_script(str(bundle))

        self.assertEqual(result.returncode, 1)
        self.assertIn("Marker not found", result.stderr)


if __name__ == "__main__":
    unittest.main()
