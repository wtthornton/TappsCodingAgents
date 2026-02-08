"""
Epic Orchestrator - Coordinates Epic-level workflow execution.

Executes all stories in an Epic document in dependency order with progress tracking.
"""

import logging
import os
from pathlib import Path
from typing import Any

from tapps_agents.core.progress_display import (
    generate_status_report,
    phases_from_step_dicts,
)
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

            # Phase-grid (process visuals) for Epic completion
            phase_grid = ""
            if report.get("stories"):
                steps_for_phases = [
                    {
                        "step_number": i + 1,
                        "step_name": s["story_id"],
                        "success": s.get("status") == "done",
                    }
                    for i, s in enumerate(report["stories"])
                ]
                phases = phases_from_step_dicts(
                    steps_for_phases,
                    name_key="step_name",
                    name_prefix="Story",
                    success_key="success",
                    index_key="step_number",
                )
                use_unicode = os.environ.get("TAPPS_PROGRESS", "auto").lower() != "plain"
                phase_grid = generate_status_report(
                    phases,
                    title="Epic Progress Summary",
                    use_unicode=use_unicode,
                    show_total=True,
                )
            output_summary_lines = [
                f"# Epic {epic.epic_number} Complete: {epic.title}",
                "",
                f"- **Completion:** {report['completion_percentage']:.1f}%",
                f"- **Stories done:** {report['done_stories']}/{report['total_stories']}",
                f"- **Failed:** {report['failed_stories']}",
                f"- **Report:** `{report_path}`",
                "",
            ]
            if phase_grid:
                output_summary_lines = [phase_grid, ""] + output_summary_lines

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
                "phase_grid": phase_grid,
                "output_summary": "\n".join(output_summary_lines),
            }

        except Exception as e:
            logger.error(f"Error executing Epic: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }

