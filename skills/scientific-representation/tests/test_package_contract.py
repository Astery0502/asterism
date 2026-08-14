"""Coarse contract for a relocated Scientific Representation Skill package."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = SKILL_ROOT / "scientific-representation.py"


def run(*command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=SKILL_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class RelocatedPackageContractTests(unittest.TestCase):
    def test_package_inventory_and_skill_entry_are_closed(self) -> None:
        manifest = json.loads(
            (SKILL_ROOT / "skill-package.json").read_text(encoding="utf-8")
        )
        expected = set(manifest["files"])
        actual = {
            str(path.relative_to(SKILL_ROOT))
            for path in SKILL_ROOT.rglob("*")
            if path.is_file()
            and path.name != "skill-package.json"
            and path.name != ".DS_Store"
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
        }
        self.assertEqual(actual, expected)
        for relative, identity in manifest["files"].items():
            with self.subTest(relative=relative):
                digest = hashlib.sha256(
                    (SKILL_ROOT / relative).read_bytes()
                ).hexdigest()
                self.assertEqual(digest, identity["sha256"])
        self.assertTrue((SKILL_ROOT / "SKILL.md").is_file())
        self.assertTrue((SKILL_ROOT / "agents" / "openai.yaml").is_file())
        self.assertFalse((SKILL_ROOT / "assets" / "prototype").exists())
        self.assertFalse((SKILL_ROOT / "scripts" / "create-workspace.py").exists())

    def test_packaged_project_is_structurally_valid_and_discoverable(self) -> None:
        structural = run(
            sys.executable,
            str(LAUNCHER),
            "validate",
            "--structural-only",
            "--json",
        )
        self.assertEqual(structural.returncode, 0, structural.stderr)
        self.assertTrue(json.loads(structural.stdout)["pass"])

        method = run(sys.executable, str(LAUNCHER), "method", "--json")
        self.assertEqual(method.returncode, 0, method.stderr)
        self.assertTrue(json.loads(method.stdout)["method"]["id"])

        targets = run(sys.executable, str(LAUNCHER), "targets", "--json")
        self.assertEqual(targets.returncode, 0, targets.stderr)
        target_records = json.loads(targets.stdout)["targets"]
        self.assertIn(
            "scientific-html", {record["id"] for record in target_records}
        )

    def test_packaged_target_validator_starts_from_a_relocated_path(self) -> None:
        definition = json.loads(
            (
                SKILL_ROOT
                / "target-definitions"
                / "scientific-html"
                / "definition.json"
            ).read_text(encoding="utf-8")
        )
        validator = SKILL_ROOT / definition["work_product_validator"]
        completed = run(sys.executable, str(validator), "--help")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("case_root", completed.stdout)
        self.assertIn("--write-receipt", completed.stdout)


if __name__ == "__main__":
    unittest.main()
