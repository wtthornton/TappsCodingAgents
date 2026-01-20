"""
Analyst Agent Handler

Handles execution of analyst agent steps for requirements gathering.

Epic 20: Complexity Reduction - Story 20.1
"""

from pathlib import Path
from typing import Any

from ..models import WorkflowStep
from .base import AgentExecutionHandler


class AnalystHandler(AgentExecutionHandler):
    """Handler for analyst agent execution."""
    
    def supports(self, agent_name: str, action: str) -> bool:
        """Check if this handler supports analyst agent."""
        return agent_name == "analyst" and action in {
            "gather_requirements",
            "gather-requirements",
            "analyze",
        }
    
    async def execute(
        self,
        step: WorkflowStep,
        action: str,
        target_path: Path | None,
    ) -> list[dict[str, Any]]:
        """
        Execute analyst step.
        
        Args:
            step: Workflow step definition
            action: Normalized action name
            target_path: Target file path (not used for analyst)
            
        Returns:
            List of created artifacts
        """
        # Prefer enhanced text from enhancer when present (e.g. full-sdlc enhance step), else user_prompt
        user_prompt = (
            self.state.variables.get("enhanced_prompt")
            or self.state.variables.get("description")
            or self.state.variables.get("user_prompt")
            or ""
        )
        if not user_prompt:
            # Check if executor has auto_mode attribute
            auto_mode = getattr(self.executor, "auto_mode", False) if self.executor else False
            if not auto_mode:
                user_prompt = "Generate requirements for this project"
        
        # Run analyst agent
        requirements_result = await self.run_agent(
            "analyst",
            "gather-requirements",
            description=user_prompt,
            output_file="requirements.md",
        )
        self.state.variables["analyst_result"] = requirements_result
        
        # Create requirements.md artifact if requested
        created_artifacts: list[dict[str, Any]] = []
        if "requirements.md" in (step.creates or []):
            req_path = self.project_root / "requirements.md"
            # Analyst agent should have created this, but verify
            if req_path.exists():
                created_artifacts.append({"name": "requirements.md", "path": str(req_path)})
        
        return created_artifacts

