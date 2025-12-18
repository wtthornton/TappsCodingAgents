"""
Tester Agent Handler

Handles execution of tester agent steps for test generation.

Epic 20: Complexity Reduction - Story 20.1
"""

from pathlib import Path
from typing import Any

from ..models import WorkflowStep
from .base import AgentExecutionHandler


class TesterHandler(AgentExecutionHandler):
    """Handler for tester agent execution."""
    
    def supports(self, agent_name: str, action: str) -> bool:
        """Check if this handler supports tester agent."""
        return agent_name == "tester" and action in {"write_tests", "test"}
    
    async def execute(
        self,
        step: WorkflowStep,
        action: str,
        target_path: Path | None,
    ) -> list[dict[str, Any]]:
        """
        Execute tester step.
        
        Args:
            step: Workflow step definition
            action: Normalized action name
            target_path: Target file path
            
        Returns:
            List of created artifacts
        """
        # Determine test target
        test_target = self._find_test_target(target_path)
        if not test_target or not test_target.exists():
            raise ValueError("Tester step requires a target file to test.")
        
        # Run tester agent
        test_result = await self.run_agent("tester", "test", file=str(test_target))
        self.state.variables["tester_result"] = test_result
        
        # Create tests/ artifact if requested
        created_artifacts: list[dict[str, Any]] = []
        if "tests/" in (step.creates or []):
            tests_dir = self.project_root / "tests"
            created_artifacts.append({"name": "tests/", "path": str(tests_dir)})
        
        return created_artifacts
    
    def _find_test_target(self, target_path: Path | None) -> Path | None:
        """Find the target file to test."""
        fixed_file = self.state.variables.get("fixed_file")
        implementer_file = self.state.variables.get("target_file")
        
        if fixed_file:
            return Path(fixed_file)
        elif implementer_file:
            return Path(implementer_file)
        elif target_path:
            return target_path
        return None

