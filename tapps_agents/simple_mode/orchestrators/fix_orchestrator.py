"""
Fix Orchestrator - Coordinates bug fixing workflow.

Coordinates: Debugger → Implementer → Tester
"""

from pathlib import Path
from typing import Any

from ...core.config import ProjectConfig
from ...core.multi_agent_orchestrator import MultiAgentOrchestrator
from ..intent_parser import Intent
from .base import SimpleModeOrchestrator


class FixOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for fixing bugs and errors."""

    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for fix workflow."""
        return ["debugger", "implementer", "tester"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute fix workflow.

        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input

        Returns:
            Dictionary with execution results
        """
        parameters = parameters or {}
        files = parameters.get("files", [])
        error_message = parameters.get("error_message", "")

        # Create multi-agent orchestrator
        orchestrator = MultiAgentOrchestrator(
            project_root=self.project_root,
            config=self.config,
            max_parallel=1,  # Sequential for fix workflow
        )

        # Prepare agent tasks
        target_file = files[0] if files else None

        agent_tasks = [
            {
                "agent_id": "debugger-1",
                "agent": "debugger",
                "command": "analyze-error",
                "args": {
                    "error_message": error_message or intent.original_input,
                    "file": target_file,
                },
            },
        ]

        # Execute debugger first
        debug_result = await orchestrator.execute_parallel(agent_tasks)

        # If debugger found a solution, proceed with implementer
        debugger_result = debug_result.get("results", {}).get("debugger-1", {})
        if debugger_result.get("success"):
            # Add implementer task
            agent_tasks.append(
                {
                    "agent_id": "implementer-1",
                    "agent": "implementer",
                    "command": "implement",
                    "args": {
                        "specification": debugger_result.get("result", {}).get(
                            "fix_suggestion", ""
                        ),
                        "file": target_file,
                    },
                }
            )

            # Execute implementer
            result = await orchestrator.execute_parallel(agent_tasks)

            # Add tester task
            agent_tasks.append(
                {
                    "agent_id": "tester-1",
                    "agent": "tester",
                    "command": "test",
                    "args": {"file": target_file},
                }
            )

            # Execute tester
            result = await orchestrator.execute_parallel(agent_tasks)
        else:
            result = debug_result

        return {
            "type": "fix",
            "success": result.get("success", False),
            "agents_executed": result.get("total_agents", 0),
            "results": result.get("results", {}),
            "summary": result.get("summary", {}),
        }

