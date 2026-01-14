"""
Architect Agent Handler

Handles execution of architect agent steps for system design.

Epic 20: Complexity Reduction - Story 20.1
"""

from pathlib import Path
from typing import Any

from ..models import WorkflowStep
from .base import AgentExecutionHandler


class ArchitectHandler(AgentExecutionHandler):
    """Handler for architect agent execution."""
    
    def supports(self, agent_name: str, action: str) -> bool:
        """Check if this handler supports architect agent."""
        return agent_name == "architect" and action in {
            "design_system",
            "design-system",
            "design_architecture",
        }
    
    async def execute(
        self,
        step: WorkflowStep,
        action: str,
        target_path: Path | None,
    ) -> list[dict[str, Any]]:
        """
        Execute architect step.
        
        Args:
            step: Workflow step definition
            action: Normalized action name
            target_path: Target file path (not used for architect)
            
        Returns:
            List of created artifacts
        """
        # Get outputs from previous steps (e.g., planner, enhancer)
        from ...workflow.output_passing import WorkflowOutputPasser
        output_passer = WorkflowOutputPasser(self.state)
        
        base_inputs: dict[str, Any] = {}
        enhanced_inputs = output_passer.prepare_agent_inputs(
            step_id=step.id,
            agent_name="architect",
            command=action,
            base_inputs=base_inputs,
        )
        
        # Get requirements from enhanced inputs or fallback to file
        requirements = enhanced_inputs.get("requirements") or enhanced_inputs.get("planner_requirements")
        if not requirements:
            requirements_path = self.project_root / "requirements.md"
            requirements = (
                requirements_path.read_text(encoding="utf-8")
                if requirements_path.exists()
                else ""
            )
        
        # Get context from enhanced inputs (user stories from planner) or build from files
        context = enhanced_inputs.get("context") or enhanced_inputs.get("planner_context")
        if not context:
            # Build context from stories if available
            stories_dir = self.project_root / "stories"
            context_parts = []
            if stories_dir.exists():
                story_files = list(stories_dir.glob("*.md"))
                if story_files:
                    context_parts.append("User Stories:")
                    for story_file in story_files[:10]:  # Limit to first 10 stories
                        context_parts.append(story_file.read_text(encoding="utf-8")[:1000])
            context = "\n\n".join(context_parts) if context_parts else ""
        
        # Run architect agent with enhanced inputs
        architect_result = await self.run_agent(
            "architect",
            "design-system",
            requirements=requirements,
            context=context,
            output_file="architecture.md",
            **{k: v for k, v in enhanced_inputs.items() if k not in ("requirements", "context", "planner_requirements", "planner_context")},
        )
        self.state.variables["architect_result"] = architect_result
        
        # Store output for next steps
        output_passer.store_agent_output(
            step_id=step.id,
            agent_name="architect",
            command=action,
            output=architect_result if isinstance(architect_result, dict) else {"result": architect_result},
        )
        
        # Create architecture.md artifact if requested
        created_artifacts: list[dict[str, Any]] = []
        if "architecture.md" in (step.creates or []):
            arch_path = self.project_root / "architecture.md"
            if arch_path.exists():
                created_artifacts.append({"name": "architecture.md", "path": str(arch_path)})
        
        return created_artifacts

