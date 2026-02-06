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
    
    def _resolve_spec(self) -> str:
        """
        Resolve the best available specification from workflow state variables.

        Fallback order: user_prompt -> enhanced_prompt -> description -> story_description.
        Acceptance criteria are appended when present.

        Returns:
            Resolved specification string (may be empty).
        """
        for key in ("user_prompt", "enhanced_prompt", "description", "story_description"):
            value = self.state.variables.get(key, "")
            if value and value.strip():
                spec = value.strip()
                # Append acceptance criteria when available (Epic story-only context)
                ac = self.state.variables.get("acceptance_criteria", "")
                if ac and ac.strip():
                    spec += f"\n\nAcceptance Criteria:\n{ac.strip()}"
                # Append prior work context when available (Epic memory)
                prior_work = self.state.variables.get("epic_prior_work", "")
                if prior_work and prior_work.strip():
                    spec += f"\n\nPrior Work Context:\n{prior_work.strip()}"
                return spec
        return ""

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
        user_prompt = self._resolve_spec()
        
        created_artifacts: list[dict[str, Any]] = []
        
        # Determine project type:
        # - Greenfield: explicitly marked as greenfield AND no target_path provided
        # - Brownfield: target_path provided (even if file doesn't exist yet - we're enhancing existing service)
        if is_greenfield and not target_path:
            # Greenfield project: create new code from scratch
            created_artifacts = await self._handle_greenfield(step, user_prompt)
        elif target_path:
            # Brownfield project: enhance/refactor existing code
            # File may not exist yet if we're adding new functionality to an existing service
            created_artifacts = await self._handle_brownfield(step, target_path, user_prompt)
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
        user_prompt: str = "",
    ) -> list[dict[str, Any]]:
        """
        Handle brownfield project refactoring/enhancement.
        
        Supports both existing files (refactor) and new files in existing services (implement).
        """
        file_exists = target_path.exists()
        
        # Build instruction based on whether file exists
        if file_exists:
            # Existing file: refactor/enhance
            debug_report_path = self.project_root / "debug-report.md"
            debug_context = (
                debug_report_path.read_text(encoding="utf-8")
                if debug_report_path.exists()
                else ""
            )
            instruction = (
                f"Enhance {target_path.name} according to the requirements. "
                f"{user_prompt}\n\n"
                "Maintain backward compatibility with existing functionality. "
                "Add robust input validation and handle edge cases safely.\n\n"
                "Context:\n"
                f"{debug_context[:4000]}"
            )
            
            # Read existing file content for context
            existing_content = target_path.read_text(encoding="utf-8")
            instruction += f"\n\nExisting code:\n{existing_content[:5000]}"
            
            action = "refactor"
            agent_params = {
                "file": str(target_path),
                "instruction": instruction,
            }
        else:
            # New file in existing service: implement with context
            # Ensure parent directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build specification from user prompt and workflow context
            spec_parts = []
            if user_prompt:
                spec_parts.append(user_prompt)
            
            # Add context from workflow state if available
            enhanced_prompt = self.state.variables.get("enhanced_prompt", "")
            if enhanced_prompt:
                spec_parts.append(f"\n\nEnhanced Requirements:\n{enhanced_prompt[:3000]}")
            
            architecture = self.state.variables.get("architecture", "")
            if architecture:
                spec_parts.append(f"\n\nArchitecture:\n{architecture[:3000]}")
            
            specification = "\n".join(spec_parts) or f"Implement {target_path.name} according to requirements"
            
            action = "implement"
            agent_params = {
                "specification": specification,
                "file_path": str(target_path),
            }
        
        # Execute appropriate agent action
        result = await self.run_agent(
            "implementer",
            action,
            **agent_params,
        )
        self.state.variables["implementer_result"] = result
        self.state.variables["target_file"] = str(target_path)

        created_artifacts: list[dict[str, Any]] = []

        # Add the target file as an artifact (for both new and existing files)
        # This ensures workflow steps can track what was created/modified
        if target_path.exists():
            created_artifacts.append(
                {"name": str(target_path.relative_to(self.project_root)), "path": str(target_path)}
            )

            # Also add "src/" artifact for workflow compatibility
            # Many workflow presets expect "src/" as a generic source code artifact
            # We use the parent directory of the target file as "src/"
            src_dir = target_path.parent
            created_artifacts.append(
                {"name": "src/", "path": str(src_dir)}
            )

        # Create fixed-code/ artifact if requested by preset (only for existing files)
        if file_exists and "fixed-code/" in (step.creates or []):
            fixed_dir = self.project_root / "fixed-code"
            fixed_dir.mkdir(parents=True, exist_ok=True)
            fixed_copy = fixed_dir / target_path.name
            shutil.copy2(target_path, fixed_copy)
            self.state.variables["fixed_file"] = str(fixed_copy)
            created_artifacts.append(
                {"name": "fixed-code/", "path": str(fixed_dir)}
            )

        return created_artifacts

