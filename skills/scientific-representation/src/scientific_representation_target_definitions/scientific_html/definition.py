"""Scientific HTML definition for planning and contract validation."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from scientific_representation.domain import FrameworkError
from scientific_representation.runtime import resolve_relative

from .environment import observe_environment
from .plan_validation import validate_contract_records


class ScientificHtmlTargetDefinition:
    """Expose Scientific HTML capabilities, contracts, and runtime readiness."""

    target_id = "scientific-html"

    def __init__(self, root: Path, definition_path: Path) -> None:
        self.root = root.resolve()
        self.definition_path = definition_path.resolve()
        self.definition = self._load_json(self.definition_path, "target definition")
        if self.definition.get("target_id") != self.target_id:
            raise FrameworkError("Scientific HTML definition has the wrong target ID")
        self.capabilities_path = resolve_relative(
            self.root,
            str(self.definition["capabilities"]),
            label="Scientific HTML capabilities",
        )
        self.plan_contract_path = resolve_relative(
            self.root,
            str(self.definition["plan_contract"]),
            label="Scientific HTML plan contract",
        )
        self.artifact_contract_path = resolve_relative(
            self.root,
            str(self.definition["artifact_contract"]),
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

    def observe_runtime(self) -> dict[str, Any]:
        return observe_environment(
            self.capabilities,
            target_id=self.target_id,
            display_name=self.definition.get("display_name"),
            implementation_status=self.definition.get("implementation_status"),
        )

    def describe(self) -> dict[str, Any]:
        return {
            "id": self.target_id,
            "display_name": self.definition.get("display_name"),
            "implementation_status": self.definition.get("implementation_status"),
            "realizer_ownership": self.definition.get("realizer_ownership"),
            "realizer_interface": self.definition.get("realizer_interface"),
            "default_profile": self.capabilities.get("default_profile_id"),
            "capabilities": deepcopy(self.capabilities),
            "plan_contract": deepcopy(self.plan_contract),
            "artifact_contract": deepcopy(self.artifact_contract),
            "agent_guide": self.definition.get("agent_guide"),
            "work_product_validator": self.definition.get(
                "work_product_validator"
            ),
            "runtime": self.observe_runtime(),
        }

    def _validate_records(self) -> None:
        required_definition_fields = (
            "display_name",
            "implementation_status",
            "realizer_ownership",
            "realizer_interface",
            "capabilities",
            "plan_contract",
            "artifact_contract",
            "agent_guide",
            "work_product_validator",
        )
        for field in required_definition_fields:
            if not isinstance(
                self.definition.get(field), str
            ) or not self.definition[field]:
                raise FrameworkError(
                    f"Scientific HTML definition field is invalid: {field}"
                )

        required_resources = (
            ("agent_guide", "Scientific HTML agent guide"),
            ("work_product_validator", "Scientific HTML work-product validator"),
        )
        for field, label in required_resources:
            resource = resolve_relative(
                self.root,
                self.definition[field],
                label=label,
            )
            if not resource.is_file():
                raise FrameworkError(f"{label} is missing: {resource}")

        validate_contract_records(
            self.capabilities,
            self.plan_contract,
            self.artifact_contract,
            target_id=self.target_id,
        )

    @staticmethod
    def _load_json(path: Path, label: str) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise FrameworkError(f"Invalid {label}: {exc}") from exc
        if not isinstance(value, dict):
            raise FrameworkError(f"{label} must contain an object")
        return value
