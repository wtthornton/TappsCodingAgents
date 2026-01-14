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
        # Try to get enhanced prompt from enhancer if available
        from ...workflow.output_passing import WorkflowOutputPasser
        output_passer = WorkflowOutputPasser(self.state)
        
        # Prepare inputs with outputs from previous steps (e.g., enhancer)
        base_inputs: dict[str, Any] = {}
        enhanced_inputs = output_passer.prepare_agent_inputs(
            step_id=step.id,
            agent_name="planner",
            command=action,
            base_inputs=base_inputs,
        )
        
        # Get description from enhanced inputs or fallback to requirements file
        plan_description = enhanced_inputs.get("description") or enhanced_inputs.get("enhancer_description")
        
        if not plan_description:
            # Read requirements if available
            requirements_path = self.project_root / "requirements.md"
            plan_description = (
                requirements_path.read_text(encoding="utf-8")
                if requirements_path.exists()
                else "Create user stories for this project"
            )
        
        # Run planner agent with enhanced inputs
        planner_result = await self.run_agent(
            "planner",
            "plan",
            description=plan_description,
            **{k: v for k, v in enhanced_inputs.items() if k not in ("description", "enhancer_description")},
        )
        self.state.variables["planner_result"] = planner_result
        
        # Store output for next steps
        output_passer.store_agent_output(
            step_id=step.id,
            agent_name="planner",
            command=action,
            output=planner_result if isinstance(planner_result, dict) else {"result": planner_result},
        )
        
        # Create stories directory if it doesn't exist
        stories_dir = self.project_root / "stories"
        stories_dir.mkdir(parents=True, exist_ok=True)
        
        # Create stories/ artifact if requested
        created_artifacts: list[dict[str, Any]] = []
        if "stories/" in (step.creates or []):
            if stories_dir.exists():
                created_artifacts.append({"name": "stories/", "path": str(stories_dir)})
        
        return created_artifacts

