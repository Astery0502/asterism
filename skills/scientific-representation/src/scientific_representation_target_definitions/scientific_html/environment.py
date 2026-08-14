"""Scientific HTML target-definition runtime-capability observation."""

from __future__ import annotations

import importlib.util
import platform
import shutil
import sys
from importlib import metadata
from pathlib import Path
from typing import Any


def observe_environment(
    capabilities: dict[str, Any],
    *,
    target_id: str,
    display_name: str | None,
    implementation_status: str | None,
) -> dict[str, Any]:
    """Observe optional packages, tools, and browser readiness."""

    verification = capabilities.get("verification_requirements", {})
    packages = sorted(
        {
            package
            for profile in capabilities.get("profiles", [])
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
            for profile in capabilities.get("profiles", [])
            for tool in profile.get("required_external_tools", [])
        }
    )
    tool_observations = {tool: shutil.which(tool) for tool in external_tools}
    browser = browser_observation()
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
    for profile in capabilities.get("profiles", []):
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

    default_profile = capabilities.get("default_profile_id")
    default_status = next(
        (profile for profile in profiles if profile["id"] == default_profile), None
    )
    build_ready = bool(default_status and default_status["build_ready"])
    ready = bool(default_status and default_status["ready"])
    return {
        "id": target_id,
        "display_name": display_name,
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
        "implementation_status": implementation_status,
    }


def browser_observation() -> dict[str, Any]:
    """Probe a browser through Playwright without making it a core dependency."""

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
