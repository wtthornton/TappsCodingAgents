"""
Documenter Agent Handler

Handles execution of documenter agent steps for documentation generation.

Epic 20: Complexity Reduction - Story 20.1
"""

from pathlib import Path
from typing import Any

from ..models import WorkflowStep
from .base import AgentExecutionHandler


class DocumenterHandler(AgentExecutionHandler):
    """Handler for documenter agent execution."""
    
    def supports(self, agent_name: str, action: str) -> bool:
        """Check if this handler supports documenter agent."""
        return agent_name == "documenter" and action in {
            "generate_docs",
            "generate-docs",
            "document",
            "generate_project_docs",
            "generate-project-docs",
        }
    
    async def execute(
        self,
        step: WorkflowStep,
        action: str,
        target_path: Path | None,
    ) -> list[dict[str, Any]]:
        """
        Execute documenter step.
        
        Args:
            step: Workflow step definition
            action: Normalized action name
            target_path: Target file path (not used for documenter)
            
        Returns:
            List of created artifacts
        """
        created_artifacts: list[dict[str, Any]] = []
        
        # Support both single-file and project-level documentation
        if action in {"generate_project_docs", "generate-project-docs"}:
            # Project-level documentation
            output_dir = step.metadata.get("output_dir") if step.metadata else None
            output_format = (
                step.metadata.get("output_format", "markdown")
                if step.metadata
                else "markdown"
            )
            
            doc_result = await self.run_agent(
                "documenter",
                "generate-project-docs",
                project_root=str(self.project_root),
                output_dir=output_dir,
                output_format=output_format,
            )
            self.state.variables["documenter_result"] = doc_result
            
            # Capture docs/api/ directory as artifact
            docs_api_dir = self.project_root / "docs" / "api"
            if docs_api_dir.exists():
                created_artifacts.append({"name": "docs/api/", "path": str(docs_api_dir)})
        else:
            # Single-file documentation (backward compatible)
            requirements_path = self.project_root / "requirements.md"
            requirements = (
                requirements_path.read_text(encoding="utf-8")
                if requirements_path.exists()
                else ""
            )
            
            doc_result = await self.run_agent(
                "documenter",
                "generate-docs",
                requirements=requirements,
                project_root=str(self.project_root),
            )
            self.state.variables["documenter_result"] = doc_result
            
            if "docs/" in (step.creates or []):
                docs_dir = self.project_root / "docs"
                if docs_dir.exists():
                    created_artifacts.append({"name": "docs/", "path": str(docs_dir)})
        
        return created_artifacts

