"""
Epic Orchestrator - Coordinates Epic-level workflow execution.

Executes all stories in an Epic document in dependency order with progress tracking.
"""

import logging
from pathlib import Path
from typing import Any

from tapps_agents.epic import EpicOrchestrator as CoreEpicOrchestrator

from ..intent_parser import Intent
from .base import SimpleModeOrchestrator

logger = logging.getLogger(__name__)


class EpicOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for Epic-level workflow execution."""

    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for Epic workflow."""
        # Epic workflow uses multiple agents per story
        return ["epic-orchestrator"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute Epic workflow.

        Args:
            intent: Parsed user intent (should contain epic_path)
            parameters: Additional parameters (epic_path, quality_threshold, etc.)

        Returns:
            Dictionary with Epic execution results
        """
        parameters = parameters or {}

        # Extract Epic path from intent or parameters
        epic_path = parameters.get("epic_path") or intent.original_input

        if not epic_path:
            return {
                "success": False,
                "error": "Epic path required. Usage: @simple-mode *epic <epic-doc.md>",
            }

        # Resolve Epic path
        epic_path = Path(epic_path)
        if not epic_path.is_absolute():
            # Try relative to project root, then docs/prd/
            if (self.project_root / epic_path).exists():
                epic_path = self.project_root / epic_path
            elif (self.project_root / "docs" / "prd" / epic_path.name).exists():
                epic_path = self.project_root / "docs" / "prd" / epic_path.name
            else:
                epic_path = self.project_root / epic_path

        if not epic_path.exists():
            return {
                "success": False,
                "error": f"Epic document not found: {epic_path}",
            }

        # Get configuration
        quality_threshold = parameters.get("quality_threshold", 70.0)
        critical_service_threshold = parameters.get("critical_service_threshold", 80.0)
        enforce_quality_gates = parameters.get("enforce_quality_gates", True)
        auto_mode = parameters.get("auto_mode", False)
        max_iterations = parameters.get("max_iterations", 3)

        try:
            # Initialize Epic orchestrator
            orchestrator = CoreEpicOrchestrator(
                project_root=self.project_root,
                config=self.config,
                quality_threshold=quality_threshold,
                critical_service_threshold=critical_service_threshold,
                enforce_quality_gates=enforce_quality_gates,
            )

            # Load Epic
            epic = orchestrator.load_epic(epic_path)

            logger.info(
                f"Starting Epic {epic.epic_number} execution: "
                f"{len(epic.stories)} stories"
            )

            # Execute Epic
            report = await orchestrator.execute_epic(
                max_iterations=max_iterations,
                auto_mode=auto_mode,
            )

            # Save report
            report_path = orchestrator.save_report()

            return {
                "success": True,
                "epic_number": epic.epic_number,
                "epic_title": epic.title,
                "completion_percentage": report["completion_percentage"],
                "total_stories": report["total_stories"],
                "done_stories": report["done_stories"],
                "failed_stories": report["failed_stories"],
                "is_complete": report["is_complete"],
                "report_path": str(report_path),
                "report": report,
            }

        except Exception as e:
            logger.error(f"Error executing Epic: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }

