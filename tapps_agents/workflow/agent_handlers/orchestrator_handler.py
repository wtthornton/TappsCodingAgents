"""
Orchestrator Agent Handler

Handles execution of orchestrator agent steps for workflow finalization.

Epic 20: Complexity Reduction - Story 20.1
"""

from pathlib import Path
from typing import Any

from ..models import WorkflowStep
from .base import AgentExecutionHandler


class OrchestratorHandler(AgentExecutionHandler):
    """Handler for orchestrator agent execution."""
    
    def supports(self, agent_name: str, action: str) -> bool:
        """Check if this handler supports orchestrator agent."""
        return agent_name == "orchestrator" and action in {"finalize", "complete"}
    
    async def execute(
        self,
        step: WorkflowStep,
        action: str,
        target_path: Path | None,
    ) -> list[dict[str, Any]]:
        """
        Execute orchestrator step.
        
        Args:
            step: Workflow step definition
            action: Normalized action name
            target_path: Target file path (not used for orchestrator)
            
        Returns:
            List of created artifacts (empty for orchestrator)
        """
        # Nothing to do other than marking completion.
        # The orchestrator step is a no-op that just marks workflow completion.
        return []

