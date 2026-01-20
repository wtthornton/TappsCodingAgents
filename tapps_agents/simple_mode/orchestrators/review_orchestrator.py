"""
Review Orchestrator - Coordinates code review workflow.

Phase 2.3: Test Generation Workflow Integration

Coordinates: Reviewer → Tester (if coverage below threshold) → Quality Gate → Improver (if issues found)

Note: This orchestrator uses MultiAgentOrchestrator which executes agents directly.
Agents return Cursor Skill instructions via GenericInstruction/TestGenerationInstruction objects,
making this Cursor-first compatible. In Cursor mode, instructions are converted to Skill commands.
"""

from pathlib import Path
from typing import Any

from tapps_agents.core.config import ProjectConfig
from tapps_agents.core.multi_agent_orchestrator import MultiAgentOrchestrator
from ..intent_parser import Intent
from .base import SimpleModeOrchestrator


class ReviewOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for code review."""

    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for review workflow."""
        return ["reviewer", "tester", "improver"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute review workflow.

        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input

        Returns:
            Dictionary with execution results
        """
        parameters = parameters or {}
        files = parameters.get("files", [])

        from ..beads_hooks import create_review_issue, close_issue

        beads_issue_id: str | None = None
        if self.config:
            beads_issue_id = create_review_issue(
                self.project_root, self.config, files[0] if files else ""
            )

        try:
            # Create multi-agent orchestrator
            orchestrator = MultiAgentOrchestrator(
                project_root=self.project_root,
                config=self.config,
                max_parallel=1,  # Sequential for review
            )

            # Prepare reviewer task
            target_file = files[0] if files else None
            reviewer_args = {}
            if target_file:
                reviewer_args["file"] = target_file

            agent_tasks = [
                {
                    "agent_id": "reviewer-1",
                    "agent": "reviewer",
                    "command": "review",
                    "args": reviewer_args,
                },
            ]

            # Execute review
            result = await orchestrator.execute_parallel(agent_tasks)

            # Phase 2.3: Check coverage and generate tests if needed
            reviewer_result = result.get("results", {}).get("reviewer-1", {})
            if reviewer_result.get("success"):
                review_data = reviewer_result.get("result", {})
                
                # Check coverage threshold from quality gate
                coverage_below_threshold = False
                coverage_info = review_data.get("coverage_gate", {})
                quality_gate_info = review_data.get("quality_gate", {})
                
                # Check if coverage gate failed or test coverage is below threshold
                if coverage_info:
                    coverage_passed = coverage_info.get("coverage_passed", True)
                    coverage_percentage = coverage_info.get("coverage_percentage", 100.0)
                    coverage_threshold = coverage_info.get("coverage_threshold", 80.0)
                    coverage_below_threshold = not coverage_passed or coverage_percentage < coverage_threshold
                elif quality_gate_info:
                    # Fallback to quality gate test coverage check
                    test_coverage_passed = quality_gate_info.get("test_coverage_passed", True)
                    coverage_below_threshold = not test_coverage_passed
                
                # Generate tests if coverage is below threshold
                if coverage_below_threshold and target_file:
                    test_file_path = Path(target_file)
                    
                    # Add tester task to generate tests
                    agent_tasks.append(
                        {
                            "agent_id": "tester-1",
                            "agent": "tester",
                            "command": "generate-tests",
                            "args": {
                                "file": target_file,
                                "test_path": None,  # Auto-detect test path
                            },
                        }
                    )
                    
                    # Execute test generation
                    result = await orchestrator.execute_parallel(agent_tasks)
                    
                    # Re-check quality gate after test generation (optional)
                    # This would require re-running reviewer, but for now we just include test results
                    tester_result = result.get("results", {}).get("tester-1", {})
                    if tester_result.get("success"):
                        review_data["test_generation"] = {
                            "generated": True,
                            "test_result": tester_result.get("result", {}),
                        }
                
                # Check if review found issues and trigger improver if needed
                # Check quality gate status
                quality_gate_blocked = review_data.get("quality_gate_blocked", False)
                has_issues = (
                    review_data.get("issues_count", 0) > 0
                    or review_data.get("score", 100) < 70
                    or quality_gate_blocked
                )

                if has_issues:
                    # Add improver task
                    agent_tasks.append(
                        {
                            "agent_id": "improver-1",
                            "agent": "improver",
                            "command": "improve",
                            "args": reviewer_args,
                        }
                    )

                    # Execute improver
                    result = await orchestrator.execute_parallel(agent_tasks)

            return {
                "type": "review",
                "success": result.get("success", False),
                "agents_executed": result.get("total_agents", 0),
                "results": result.get("results", {}),
                "summary": result.get("summary", {}),
            }
        finally:
            close_issue(self.project_root, beads_issue_id)

