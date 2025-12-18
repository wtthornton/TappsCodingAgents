"""
Planner Agent Handler

Handles execution of planner agent steps for story creation.

Epic 20: Complexity Reduction - Story 20.1
"""

from pathlib import Path
from typing import Any

from ..models import WorkflowStep
from .base import AgentExecutionHandler


class PlannerHandler(AgentExecutionHandler):
    """Handler for planner agent execution."""
    
    def supports(self, agent_name: str, action: str) -> bool:
        """Check if this handler supports planner agent."""
        return agent_name == "planner" and action in {
            "create_stories",
            "create-stories",
            "plan",
            "breakdown",
        }
    
    async def execute(
        self,
        step: WorkflowStep,
        action: str,
        target_path: Path | None,
    ) -> list[dict[str, Any]]:
        """
        Execute planner step.
        
        Args:
            step: Workflow step definition
            action: Normalized action name
            target_path: Target file path (not used for planner)
            
        Returns:
            List of created artifacts
        """
        # Read requirements if available
        requirements_path = self.project_root / "requirements.md"
        requirements = (
            requirements_path.read_text(encoding="utf-8")
            if requirements_path.exists()
            else ""
        )
        
        # Use "plan" command which creates a plan with multiple stories
        plan_description = (
            requirements if requirements else "Create user stories for this project"
        )
        
        # Run planner agent
        planner_result = await self.run_agent(
            "planner",
            "plan",
            description=plan_description,
        )
        self.state.variables["planner_result"] = planner_result
        
        # Create stories directory if it doesn't exist
        stories_dir = self.project_root / "stories"
        stories_dir.mkdir(parents=True, exist_ok=True)
        
        # Create stories/ artifact if requested
        created_artifacts: list[dict[str, Any]] = []
        if "stories/" in (step.creates or []):
            if stories_dir.exists():
                created_artifacts.append({"name": "stories/", "path": str(stories_dir)})
        
        return created_artifacts

