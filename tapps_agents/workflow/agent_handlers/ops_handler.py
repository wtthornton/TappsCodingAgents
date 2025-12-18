"""
Ops Agent Handler

Handles execution of ops agent steps for security scanning.

Epic 20: Complexity Reduction - Story 20.1
"""

from pathlib import Path
from typing import Any

from ..models import WorkflowStep
from .base import AgentExecutionHandler


class OpsHandler(AgentExecutionHandler):
    """Handler for ops agent execution."""
    
    def supports(self, agent_name: str, action: str) -> bool:
        """Check if this handler supports ops agent."""
        return agent_name == "ops" and action in {
            "security_scan",
            "security-scan",
            "audit",
        }
    
    async def execute(
        self,
        step: WorkflowStep,
        action: str,
        target_path: Path | None,
    ) -> list[dict[str, Any]]:
        """
        Execute ops step.
        
        Args:
            step: Workflow step definition
            action: Normalized action name
            target_path: Target file path (not used for ops)
            
        Returns:
            List of created artifacts
        """
        # Run ops agent security scan
        ops_result = await self.run_agent(
            "ops",
            "security-scan",
            project_root=str(self.project_root),
        )
        self.state.variables["ops_result"] = ops_result
        
        # Create security-report.md artifact if requested
        created_artifacts: list[dict[str, Any]] = []
        if "security-report.md" in (step.creates or []):
            security_path = self.project_root / "security-report.md"
            if security_path.exists():
                created_artifacts.append(
                    {"name": "security-report.md", "path": str(security_path)}
                )
        
        return created_artifacts

