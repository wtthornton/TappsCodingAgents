"""
Implementer Agent Handler

Handles execution of implementer agent steps for both greenfield and brownfield projects.

Epic 20: Complexity Reduction - Story 20.1
"""

import shutil
from pathlib import Path
from typing import Any

from ..models import WorkflowStep, WorkflowType
from .base import AgentExecutionHandler


class ImplementerHandler(AgentExecutionHandler):
    """Handler for implementer agent execution."""
    
    def supports(self, agent_name: str, action: str) -> bool:
        """Check if this handler supports implementer agent."""
        return (
            agent_name == "implementer"
            and action in {"write_code", "fix", "implement"}
        )
    
    async def execute(
        self,
        step: WorkflowStep,
        action: str,
        target_path: Path | None,
    ) -> list[dict[str, Any]]:
        """
        Execute implementer step.
        
        Args:
            step: Workflow step definition
            action: Normalized action name
            target_path: Target file path
            
        Returns:
            List of created artifacts
        """
        # Check if this is a greenfield project
        workflow_type = getattr(self.workflow, "type", None) if self.workflow else None
        is_greenfield = (
            workflow_type == WorkflowType.GREENFIELD
            or (isinstance(workflow_type, str) and workflow_type.lower() == "greenfield")
            or (hasattr(workflow_type, "value") and workflow_type.value == "greenfield")
        )
        user_prompt = self.state.variables.get("user_prompt", "")
        
        created_artifacts: list[dict[str, Any]] = []
        
        if is_greenfield and (not target_path or not target_path.exists()):
            # Greenfield project: create new code from scratch
            created_artifacts = await self._handle_greenfield(step, user_prompt)
        elif target_path and target_path.exists():
            # Brownfield project: refactor existing code
            created_artifacts = await self._handle_brownfield(step, target_path)
        else:
            raise ValueError(
                "Implementer step requires either a target file for brownfield projects "
                "or a greenfield workflow type for new projects."
            )
        
        return created_artifacts
    
    async def _handle_greenfield(
        self,
        step: WorkflowStep,
        user_prompt: str,
    ) -> list[dict[str, Any]]:
        """Handle greenfield project implementation."""
        requirements_path = self.project_root / "requirements.md"
        architecture_path = self.project_root / "architecture.md"
        
        # Build implementation specification
        spec_parts = []
        if user_prompt:
            spec_parts.append(user_prompt)
        if requirements_path.exists():
            req_content = requirements_path.read_text(encoding='utf-8')
            spec_parts.append(f"\n\nRequirements:\n{req_content[:3000]}")
        if architecture_path.exists():
            arch_content = architecture_path.read_text(encoding='utf-8')
            spec_parts.append(f"\n\nArchitecture:\n{arch_content[:3000]}")
        
        specification = "\n".join(spec_parts) or "Create the application based on requirements and architecture"
        
        # Build context from stories if available
        stories_dir = self.project_root / "stories"
        context_parts = []
        if stories_dir.exists():
            story_files = list(stories_dir.glob("*.md"))
            if story_files:
                context_parts.append("User Stories:")
                for story_file in story_files[:5]:  # Limit to first 5 stories
                    context_parts.append(story_file.read_text(encoding='utf-8')[:500])
        context = "\n\n".join(context_parts) if context_parts else None
        
        # Determine output directory and main file from step.creates
        output_dir = self.project_root / "src"
        if step.creates:
            for create_item in step.creates:
                if create_item.endswith("/") or create_item.endswith("\\"):
                    output_dir = self.project_root / create_item.rstrip("/\\")
                    break
        
        output_dir.mkdir(parents=True, exist_ok=True)
        main_file = output_dir / "app.py"
        
        # Use implement command for greenfield projects
        implement_result = await self.run_agent(
            "implementer",
            "implement",
            specification=specification,
            file_path=str(main_file),
            context=context,
        )
        self.state.variables["implementer_result"] = implement_result
        self.state.variables["target_file"] = str(main_file)
        
        return [{"name": "src/", "path": str(output_dir)}]
    
    async def _handle_brownfield(
        self,
        step: WorkflowStep,
        target_path: Path,
    ) -> list[dict[str, Any]]:
        """Handle brownfield project refactoring."""
        debug_report_path = self.project_root / "debug-report.md"
        debug_context = (
            debug_report_path.read_text(encoding="utf-8")
            if debug_report_path.exists()
            else ""
        )
        instruction = (
            f"Fix the bugs in {target_path.name}. "
            "Add robust input validation and handle missing keys safely. "
            "Do not change behavior beyond fixing the crashes.\n\n"
            "Context:\n"
            f"{debug_context[:4000]}"
        )
        
        fix_result = await self.run_agent(
            "implementer",
            "refactor",
            file=str(target_path),
            instruction=instruction,
        )
        self.state.variables["implementer_result"] = fix_result
        
        created_artifacts: list[dict[str, Any]] = []
        
        # Create fixed-code/ artifact if requested by preset
        if "fixed-code/" in (step.creates or []):
            fixed_dir = self.project_root / "fixed-code"
            fixed_dir.mkdir(parents=True, exist_ok=True)
            fixed_copy = fixed_dir / target_path.name
            shutil.copy2(target_path, fixed_copy)
            self.state.variables["fixed_file"] = str(fixed_copy)
            created_artifacts.append(
                {"name": "fixed-code/", "path": str(fixed_dir)}
            )
        
        return created_artifacts

