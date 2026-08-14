"""Coarse contract between the outer skill and its embedded Prototype."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL_FILE = SKILL_ROOT / "SKILL.md"
CREATE_WORKSPACE = SKILL_ROOT / "scripts" / "create-workspace.py"
ARTIFACT_CONTRACT = "adapters/scientific-html/artifact-contract.json"
WORK_PRODUCT_VALIDATOR = (
    "adapters/scientific-html/scripts/validate-work-product.py"
)

OUTER_SEAMS = (
    "scripts/create-workspace.py",
    "scientific-html",
    "validate-work-product.py",
    "product/index.html",
)

PROTOTYPE_SEAMS = (
    "AGENTS.md",
    "modules/scientific-analysis/AGENT-GUIDE.md",
    "method.json",
    "adapters/scientific-html/AGENT-GUIDE.md",
    ARTIFACT_CONTRACT,
    WORK_PRODUCT_VALIDATOR,
    "prototype.py",
)

FORBIDDEN_SNAPSHOT_PATHS = (
    "cases",
    "tests",
    "docs",
    "provenance",
    "adapters/wolfram",
)


def run(*command: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class OuterPrototypeFrameworkContractTests(unittest.TestCase):
    def test_outer_skill_connects_to_a_relocated_prototype(self) -> None:
        skill_text = SKILL_FILE.read_text(encoding="utf-8")
        for seam in OUTER_SEAMS:
            with self.subTest(outer_seam=seam):
                self.assertIn(seam, skill_text)

        with tempfile.TemporaryDirectory(
            prefix="scientific-representation-contract-"
        ) as temporary:
            workspace = Path(temporary) / "workspace with spaces"
            created = run(
                sys.executable,
                str(CREATE_WORKSPACE),
                str(workspace),
                cwd=SKILL_ROOT,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            receipt = json.loads(created.stdout)
            self.assertTrue(receipt["pass"])
            self.assertEqual(receipt["default_target"], "scientific-html")
            self.assertTrue((workspace / "work").is_dir())

            for seam in PROTOTYPE_SEAMS:
                with self.subTest(prototype_seam=seam):
                    self.assertTrue((workspace / seam).is_file(), seam)

            for relative in FORBIDDEN_SNAPSHOT_PATHS:
                with self.subTest(forbidden_snapshot_path=relative):
                    self.assertFalse((workspace / relative).exists(), relative)

            manifest = json.loads(
                (workspace / "prototype.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["default_target"], "scientific-html")
            self.assertEqual(set(manifest["targets"]), {"scientific-html"})
            self.assertEqual(manifest["cases"], [])

            bundle = json.loads(
                (workspace / "BUNDLE.json").read_text(encoding="utf-8")
            )
            self.assertEqual(bundle["profile"], "skill-framework")

            doctor = run(
                sys.executable,
                "prototype.py",
                "doctor",
                "--target",
                "scientific-html",
                "--json",
                cwd=workspace,
            )
            self.assertIn(doctor.returncode, (0, 1), doctor.stderr)
            observation = json.loads(doctor.stdout)
            self.assertEqual(observation["operation"], "doctor")
            self.assertEqual(observation["target"]["id"], "scientific-html")
            self.assertTrue(observation["target"]["planning_available"])

            validator = workspace / WORK_PRODUCT_VALIDATOR
            validator_help = run(
                sys.executable,
                str(validator),
                "--help",
                cwd=workspace,
            )
            self.assertEqual(validator_help.returncode, 0, validator_help.stderr)
            self.assertIn("case_root", validator_help.stdout)
            self.assertIn("--write-receipt", validator_help.stdout)

            artifact_contract = json.loads(
                (workspace / ARTIFACT_CONTRACT).read_text(encoding="utf-8")
            )
            self.assertIn(
                "product/index.html",
                artifact_contract["required_records"],
            )


if __name__ == "__main__":
    unittest.main()
