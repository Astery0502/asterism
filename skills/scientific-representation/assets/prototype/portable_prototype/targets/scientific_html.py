"""Framework adapter for Scientific HTML planning and contract validation."""

from __future__ import annotations

import importlib.util
import json
import platform
import shutil
import sys
from copy import deepcopy
from importlib import metadata
from pathlib import Path
from typing import Any, Sequence

from ..catalog import resolve_relative
from ..models import PrototypeError


class ScientificHtmlAdapter:
    """Expose Scientific HTML capabilities, contracts, and runtime readiness."""

    target_id = "scientific-html"

    def __init__(self, root: Path, descriptor_path: Path) -> None:
        self.root = root.resolve()
        self.descriptor_path = descriptor_path.resolve()
        self.descriptor = self._load_json(self.descriptor_path, "target descriptor")
        if self.descriptor.get("target_id") != self.target_id:
            raise PrototypeError("Scientific HTML descriptor has the wrong target ID")
        self.capabilities_path = resolve_relative(
            self.root,
            str(self.descriptor["capabilities"]),
            label="Scientific HTML capabilities",
        )
        self.plan_contract_path = resolve_relative(
            self.root,
            str(self.descriptor["plan_contract"]),
            label="Scientific HTML plan contract",
        )
        self.artifact_contract_path = resolve_relative(
            self.root,
            str(self.descriptor["artifact_contract"]),
            label="Scientific HTML artifact contract",
        )
        self.capabilities = self._load_json(
            self.capabilities_path, "Scientific HTML capabilities"
        )
        self.plan_contract = self._load_json(
            self.plan_contract_path, "Scientific HTML plan contract"
        )
        self.artifact_contract = self._load_json(
            self.artifact_contract_path, "Scientific HTML artifact contract"
        )
        self._validate_records()

    def doctor(self) -> dict[str, Any]:
        verification = self.capabilities.get("verification_requirements", {})
        packages = sorted(
            {
                package
                for profile in self.capabilities.get("profiles", [])
                for package in (
                    profile.get("required_python_packages", [])
                    + profile.get("optional_python_packages", [])
                )
            }
            | set(verification.get("python_packages", []))
        )
        observations: dict[str, dict[str, Any]] = {}
        for package in packages:
            installed = importlib.util.find_spec(package) is not None
            try:
                version = metadata.version(package) if installed else None
            except metadata.PackageNotFoundError:
                version = None
            observations[package] = {"installed": installed, "version": version}

        external_tools = sorted(
            {
                tool
                for profile in self.capabilities.get("profiles", [])
                for tool in profile.get("required_external_tools", [])
            }
        )
        tool_observations = {tool: shutil.which(tool) for tool in external_tools}
        browser = self._browser_observation()
        missing_verification_packages = [
            package
            for package in verification.get("python_packages", [])
            if not observations.get(package, {}).get("installed", False)
        ]
        browser_required = verification.get("browser") is True
        verification_ready = not missing_verification_packages and (
            not browser_required or browser["available"]
        )

        profiles = []
        for profile in self.capabilities.get("profiles", []):
            missing_packages = [
                package
                for package in profile.get("required_python_packages", [])
                if not observations.get(package, {}).get("installed", False)
            ]
            missing_optional = [
                package
                for package in profile.get("optional_python_packages", [])
                if not observations.get(package, {}).get("installed", False)
            ]
            missing_tools = [
                tool
                for tool in profile.get("required_external_tools", [])
                if not tool_observations[tool]
            ]
            build_ready = not missing_packages and not missing_tools
            profiles.append(
                {
                    "id": profile.get("id"),
                    "role": profile.get("role"),
                    "ready": build_ready and verification_ready,
                    "build_ready": build_ready,
                    "verification_ready": verification_ready,
                    "missing_python_packages": missing_packages,
                    "missing_optional_python_packages": missing_optional,
                    "missing_external_tools": missing_tools,
                }
            )

        default_profile = self.capabilities.get("default_profile_id")
        default_status = next(
            (profile for profile in profiles if profile["id"] == default_profile), None
        )
        build_ready = bool(default_status and default_status["build_ready"])
        ready = bool(default_status and default_status["ready"])
        return {
            "id": self.target_id,
            "display_name": self.descriptor.get("display_name"),
            "available": ready,
            "planning_available": True,
            "build_ready": build_ready,
            "verification_ready": verification_ready,
            "executable": sys.executable,
            "version": platform.python_version(),
            "python_packages": observations,
            "external_tools": tool_observations,
            "browser_test_executable": browser["executable"],
            "browser_observation": browser,
            "missing_verification_python_packages": missing_verification_packages,
            "default_profile": default_profile,
            "profiles": profiles,
            "implementation_status": self.descriptor.get("implementation_status"),
        }

    def describe_target(self) -> dict[str, Any]:
        return {
            "id": self.target_id,
            "display_name": self.descriptor.get("display_name"),
            "implementation_status": self.descriptor.get("implementation_status"),
            "default_profile": self.capabilities.get("default_profile_id"),
            "capabilities": deepcopy(self.capabilities),
            "plan_contract": deepcopy(self.plan_contract),
            "artifact_contract": deepcopy(self.artifact_contract),
            "agent_guide": self.descriptor.get("agent_guide"),
            "runtime": self.doctor(),
        }

    def bundle_excludes(
        self, profile: str, cases: Sequence[Any]
    ) -> set[Path]:
        """Return no exclusions because the framework carries no case artifacts."""

        return set()

    def _validate_records(self) -> None:
        required_descriptor_fields = (
            "display_name",
            "realizer_interface",
            "capabilities",
            "plan_contract",
            "artifact_contract",
            "agent_guide",
        )
        for field in required_descriptor_fields:
            if not isinstance(self.descriptor.get(field), str) or not self.descriptor[field]:
                raise PrototypeError(
                    f"Scientific HTML descriptor field is invalid: {field}"
                )

        agent_guide = resolve_relative(
            self.root,
            self.descriptor["agent_guide"],
            label="Scientific HTML agent guide",
        )
        if not agent_guide.is_file():
            raise PrototypeError(f"Scientific HTML agent guide is missing: {agent_guide}")

        profiles = self.capabilities.get("profiles")
        profile_ids = [
            profile.get("id") for profile in profiles if isinstance(profile, dict)
        ] if isinstance(profiles, list) else []
        if (
            self.capabilities.get("schema_version") != 1
            or self.capabilities.get("target_id") != self.target_id
            or not profile_ids
            or len(profile_ids) != len(set(profile_ids))
            or self.capabilities.get("default_profile_id") not in profile_ids
        ):
            raise PrototypeError("Scientific HTML capability catalog is invalid")

        verification = self.capabilities.get("verification_requirements")
        if (
            not isinstance(verification, dict)
            or not isinstance(verification.get("python_packages"), list)
            or not isinstance(verification.get("browser"), bool)
        ):
            raise PrototypeError(
                "Scientific HTML verification requirements are incomplete"
            )

        if (
            self.plan_contract.get("schema_version") != 1
            or self.plan_contract.get("contract_id") != "scientific-html-plan-v1"
        ):
            raise PrototypeError("Scientific HTML plan contract is invalid")
        if (
            self.artifact_contract.get("schema_version") != 2
            or self.artifact_contract.get("contract_id")
            != "scientific-html-artifact-v2"
        ):
            raise PrototypeError("Scientific HTML artifact contract is invalid")

    @staticmethod
    def _load_json(path: Path, label: str) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise PrototypeError(f"Invalid {label}: {exc}") from exc
        if not isinstance(value, dict):
            raise PrototypeError(f"{label} must contain an object")
        return value

    @staticmethod
    def _browser_observation() -> dict[str, Any]:
        if importlib.util.find_spec("playwright") is None:
            return {
                "available": False,
                "executable": None,
                "source": None,
                "probe_error": "Playwright is not installed",
            }

        errors: list[str] = []
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as playwright:
                attempts = [
                    ({"channel": "msedge", "headless": True}, "channel:msedge"),
                    ({"channel": "chrome", "headless": True}, "channel:chrome"),
                    (
                        {"headless": True},
                        str(Path(playwright.chromium.executable_path).resolve()),
                    ),
                ]
                for options, executable in attempts:
                    try:
                        browser = playwright.chromium.launch(**options)
                        version = browser.version
                        browser.close()
                        return {
                            "available": True,
                            "executable": executable,
                            "source": "playwright-launch-probe",
                            "version": version,
                            "probe_error": None,
                        }
                    except Exception as exc:  # pragma: no cover
                        errors.append(f"{executable}: {type(exc).__name__}: {exc}")
        except Exception as exc:  # pragma: no cover
            errors.append(f"Playwright initialization: {type(exc).__name__}: {exc}")
        return {
            "available": False,
            "executable": None,
            "source": None,
            "version": None,
            "probe_error": " | ".join(errors),
        }
