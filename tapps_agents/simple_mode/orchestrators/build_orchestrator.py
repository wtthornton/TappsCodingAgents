"""
Build Orchestrator - Coordinates feature development workflow.

Coordinates: Planner → Architect → Designer → Implementer
"""

from pathlib import Path
from typing import Any

from tapps_agents.core.config import ProjectConfig
from tapps_agents.core.multi_agent_orchestrator import MultiAgentOrchestrator
from ..intent_parser import Intent
from .base import SimpleModeOrchestrator


class BuildOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for building new features."""

    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for build workflow."""
        return ["planner", "architect", "designer", "implementer"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute build workflow.

        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input

        Returns:
            Dictionary with execution results
        """
        parameters = parameters or {}
        description = parameters.get("description") or intent.original_input

        # Create multi-agent orchestrator
        orchestrator = MultiAgentOrchestrator(
            project_root=self.project_root,
            config=self.config,
            max_parallel=2,  # Allow some parallelization
        )

        # Prepare agent tasks
        agent_tasks = [
            {
                "agent_id": "planner-1",
                "agent": "planner",
                "command": "create-story",
                "args": {"description": description},
            },
            {
                "agent_id": "architect-1",
                "agent": "architect",
                "command": "design",
                "args": {"specification": description},
            },
            {
                "agent_id": "designer-1",
                "agent": "designer",
                "command": "design-api",
                "args": {"specification": description},
            },
            {
                "agent_id": "implementer-1",
                "agent": "implementer",
                "command": "implement",
                "args": {"specification": description},
            },
        ]

        # Execute in sequence (some steps can run in parallel)
        result = await orchestrator.execute_parallel(agent_tasks)

        return {
            "type": "build",
            "success": result.get("success", False),
            "agents_executed": result.get("total_agents", 0),
            "results": result.get("results", {}),
            "summary": result.get("summary", {}),
        }

