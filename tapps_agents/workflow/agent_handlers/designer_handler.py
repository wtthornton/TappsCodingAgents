"""
Designer Agent Handler

Handles execution of designer agent steps for API design.

Epic 20: Complexity Reduction - Story 20.1
"""

from pathlib import Path
from typing import Any

from ..models import WorkflowStep
from .base import AgentExecutionHandler


class DesignerHandler(AgentExecutionHandler):
    """Handler for designer agent execution."""
    
    def supports(self, agent_name: str, action: str) -> bool:
        """Check if this handler supports designer agent."""
        return agent_name == "designer" and action in {
            "api_design",
            "api-design",
            "design_api",
        }
    
    async def execute(
        self,
        step: WorkflowStep,
        action: str,
        target_path: Path | None,
    ) -> list[dict[str, Any]]:
        """
        Execute designer step.
        
        Args:
            step: Workflow step definition
            action: Normalized action name
            target_path: Target file path (not used for designer)
            
        Returns:
            List of created artifacts
        """
        # Get outputs from previous steps (e.g., architect, planner)
        from ...workflow.output_passing import WorkflowOutputPasser
        output_passer = WorkflowOutputPasser(self.state)
        
        base_inputs: dict[str, Any] = {}
        enhanced_inputs = output_passer.prepare_agent_inputs(
            step_id=step.id,
            agent_name="designer",
            command=action,
            base_inputs=base_inputs,
        )
        
        # Get requirements from enhanced inputs or fallback to file
        requirements = enhanced_inputs.get("requirements") or enhanced_inputs.get("planner_requirements")
        
        # Get architecture context from enhanced inputs or fallback to file
        context = enhanced_inputs.get("context") or enhanced_inputs.get("architect_context") or enhanced_inputs.get("architecture")
        
        if not requirements:
            requirements_path = self.project_root / "requirements.md"
            requirements = (
                requirements_path.read_text(encoding="utf-8")
                if requirements_path.exists()
                else ""
            )
        
        if not context:
            arch_path = self.project_root / "architecture.md"
            context = (
                arch_path.read_text(encoding="utf-8") if arch_path.exists() else ""
            )
        
        # Combine requirements and architecture for the design-api command
        api_requirements = (
            f"{requirements}\n\nArchitecture:\n{context}"
            if context
            else requirements
        )
        
        # Run designer agent with enhanced inputs
        designer_result = await self.run_agent(
            "designer",
            "design-api",
            requirements=api_requirements,
            **{k: v for k, v in enhanced_inputs.items() if k not in ("requirements", "context", "planner_requirements", "architect_context", "architecture")},
        )
        self.state.variables["designer_result"] = designer_result
        
        # Store output for next steps
        output_passer.store_agent_output(
            step_id=step.id,
            agent_name="designer",
            command=action,
            output=designer_result if isinstance(designer_result, dict) else {"result": designer_result},
        )
        
        # Create api-design.md artifact if requested
        created_artifacts: list[dict[str, Any]] = []
        if "api-design.md" in (step.creates or []):
            api_design_path = self.project_root / "api-design.md"
            if api_design_path.exists():
                created_artifacts.append(
                    {"name": "api-design.md", "path": str(api_design_path)}
                )
        
        return created_artifacts

