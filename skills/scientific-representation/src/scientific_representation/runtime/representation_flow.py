"""Resume representation inquiry from a persisted TheoreticalAccount."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..domain import (
    FrameworkError,
    RepresentationFormationRequest,
    TheoreticalAccountRecord,
    WorkflowStatus,
)
from ..ports import RepresentationAgent
from .handoff_support import normalize_requirements
from .persistence import (
    create_staging_workspace,
    discard_staging_workspace,
    publish_workspace,
    read_json,
    read_text,
    write_json,
    write_text,
)


class AccountRequirementsCoordinator:
    """Form representation requirements without rerunning scientific inquiry."""

    def __init__(self, agent: RepresentationAgent, *, method_id: str = "") -> None:
        self.agent = agent
        self.method_id = method_id

    def realize(
        self,
        source_workspace: Path,
        destination: Path,
        *,
        presentation_direction: str = "",
        presentation_question: str | None = None,
    ) -> dict[str, Any]:
        direction = presentation_direction.strip()
        question = (
            presentation_question.strip()
            if presentation_question is not None
            else None
        )
        if not direction and not question:
            raise FrameworkError(
                "Representation requires a presentation direction or direct question"
            )
        source = source_workspace.resolve()
        destination = destination.resolve()
        if destination.exists():
            raise FrameworkError(f"Realization destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        account = read_text(
            source / "analysis" / "theoretical-account.md", "TheoreticalAccount"
        )
        account_record = TheoreticalAccountRecord.from_dict(
            read_json(
                source / "analysis" / "theoretical-account.json",
                "theoretical account lineage",
            )
        )
        account_record.verify_content(account)
        requirements_draft = self.agent.formulate_requirements(
            RepresentationFormationRequest(
                presentation_direction=direction,
                presentation_question=question,
            ),
            account,
        )
        requirements = normalize_requirements(
            requirements_draft,
            theoretical_account_id=account_record.account_id,
            method_id=self.method_id,
        )

        temporary = create_staging_workspace(destination)
        try:
            write_json(
                temporary / "request.json",
                {
                    "operation": "realize-account",
                    "provider_id": self.agent.provider_id,
                    "presentation_direction": direction,
                    "presentation_question": question,
                },
            )
            write_text(temporary / "analysis" / "theoretical-account.md", account)
            write_json(
                temporary / "analysis" / "theoretical-account.json",
                account_record.to_dict(),
            )
            if direction:
                write_text(
                    temporary / "input" / "presentation-direction.md", direction
                )
            if question:
                write_text(
                    temporary / "input" / "presentation-question.md", question
                )
            write_json(
                temporary / "representation" / "representation-intent.json",
                requirements.representation_intent,
            )
            write_text(
                temporary / "representation" / "representation-requirements.md",
                requirements.requirements_markdown,
            )
            write_json(
                temporary / "representation" / "representation-interface.json",
                requirements.interface_spec,
            )
            write_json(
                temporary / "representation" / "observations.json",
                requirements_draft.observations,
            )
            publish_workspace(temporary, destination)
        except Exception:
            discard_staging_workspace(temporary)
            raise

        return {
            "operation": "realize-account",
            "provider": self.agent.provider_id,
            "completed_stages": ["representation"],
            "workspace": str(destination),
            "status": WorkflowStatus().to_dict(),
        }
