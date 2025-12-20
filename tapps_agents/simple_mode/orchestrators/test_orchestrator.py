"""
Test Orchestrator - Coordinates test generation workflow.

Coordinates: Tester
"""

from pathlib import Path
from typing import Any

from tapps_agents.core.config import ProjectConfig
from tapps_agents.core.multi_agent_orchestrator import MultiAgentOrchestrator
from ..intent_parser import Intent
from .base import SimpleModeOrchestrator


class TestOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for test generation."""

    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for test workflow."""
        return ["tester"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute test workflow.

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
            max_parallel=1,
        )

        # Prepare tester task
        target_file = files[0] if files else None
        tester_args = {}
        if target_file:
            tester_args["file"] = target_file

        agent_tasks = [
            {
                "agent_id": "tester-1",
                "agent": "tester",
                "command": "test",
                "args": tester_args,
            },
        ]

        # Execute tester
        result = await orchestrator.execute_parallel(agent_tasks)

        return {
            "type": "test",
            "success": result.get("success", False),
            "agents_executed": result.get("total_agents", 0),
            "results": result.get("results", {}),
            "summary": result.get("summary", {}),
        }

