"""
Review Orchestrator - Coordinates code review workflow.

Coordinates: Reviewer → Improver (if issues found)
"""

from pathlib import Path
from typing import Any

from tapps_agents.core.config import ProjectConfig
from tapps_agents.core.multi_agent_orchestrator import MultiAgentOrchestrator
from ..intent_parser import Intent
from .base import SimpleModeOrchestrator


class ReviewOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for code review."""

    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for review workflow."""
        return ["reviewer", "improver"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute review workflow.

        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input

        Returns:
            Dictionary with execution results
        """
        parameters = parameters or {}
        files = parameters.get("files", [])

        # Create multi-agent orchestrator
        orchestrator = MultiAgentOrchestrator(
            project_root=self.project_root,
            config=self.config,
            max_parallel=1,  # Sequential for review
        )

        # Prepare reviewer task
        target_file = files[0] if files else None
        reviewer_args = {}
        if target_file:
            reviewer_args["file"] = target_file

        agent_tasks = [
            {
                "agent_id": "reviewer-1",
                "agent": "reviewer",
                "command": "review",
                "args": reviewer_args,
            },
        ]

        # Execute review
        result = await orchestrator.execute_parallel(agent_tasks)

        # Check if review found issues and trigger improver if needed
        reviewer_result = result.get("results", {}).get("reviewer-1", {})
        if reviewer_result.get("success"):
            review_data = reviewer_result.get("result", {})
            # Check if issues were found (simplified check)
            has_issues = review_data.get("issues_count", 0) > 0 or review_data.get(
                "score", 100
            ) < 70

            if has_issues:
                # Add improver task
                agent_tasks.append(
                    {
                        "agent_id": "improver-1",
                        "agent": "improver",
                        "command": "improve",
                        "args": reviewer_args,
                    }
                )

                # Execute improver
                result = await orchestrator.execute_parallel(agent_tasks)

        return {
            "type": "review",
            "success": result.get("success", False),
            "agents_executed": result.get("total_agents", 0),
            "results": result.get("results", {}),
            "summary": result.get("summary", {}),
        }

