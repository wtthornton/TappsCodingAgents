"""
Refactor Orchestrator - Coordinates systematic code refactoring workflow.

Coordinates: Reviewer → Architect → Plan Generation → Implementer → Tester → Reviewer

This orchestrator provides systematic code modernization with pattern detection,
incremental refactoring, and safety checks to ensure behavior preservation.
"""

from typing import Any

from tapps_agents.core.multi_agent_orchestrator import MultiAgentOrchestrator

from ..intent_parser import Intent
from .base import SimpleModeOrchestrator


class RefactorOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for code refactoring."""

    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for refactor workflow."""
        return ["reviewer", "architect", "implementer", "tester", "reviewer"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute refactor workflow.

        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input

        Returns:
            Dictionary with execution results
        """
        parameters = parameters or {}
        files = parameters.get("files", [])
        pattern = parameters.get("pattern")
        modernize = parameters.get("modernize", False)
        refactor_target = parameters.get("description") or intent.original_input

        from ..beads_hooks import close_issue, create_refactor_issue

        beads_issue_id: str | None = None
        if self.config:
            beads_issue_id = create_refactor_issue(
                self.project_root,
                self.config,
                files[0] if files else "",
                refactor_target or "",
            )

        try:
            # Create multi-agent orchestrator
            orchestrator = MultiAgentOrchestrator(
                project_root=self.project_root,
                config=self.config,
                max_parallel=1,  # Sequential for refactoring
            )

            agent_tasks = []

            # Step 1: Review and identify legacy code patterns
            target_files = files if files else []
        
            if pattern:
                # Find files matching pattern
                from pathlib import Path
            
                pattern_files = list(Path(self.project_root).glob(pattern))
                target_files.extend([str(f) for f in pattern_files])

            reviewer_args = {
                "files": target_files if target_files else None,
                "analyze_patterns": True,
                "detect_deprecated": True,
            }

            agent_tasks.append(
                {
                    "agent_id": "reviewer-1",
                    "agent": "reviewer",
                    "command": "review",
                    "args": reviewer_args,
                }
            )

            # Execute initial review
            result = await orchestrator.execute_parallel(agent_tasks)

            # Extract legacy patterns from review
            reviewer_result = result.get("results", {}).get("reviewer-1", {})
            legacy_patterns = []
            issues = []

            if reviewer_result.get("success"):
                review_data = reviewer_result.get("result", {})
                issues = review_data.get("issues", [])
            
                # Identify legacy patterns
                for issue in issues:
                    if any(keyword in issue.get("message", "").lower() for keyword in 
                           ["deprecated", "legacy", "old", "outdated", "obsolete"]):
                        legacy_patterns.append(issue)

            # Step 2: Design modern patterns using architect
            if legacy_patterns or modernize:
                architect_args = {
                    "description": f"Modernize code patterns: {refactor_target}",
                    "context": f"Refactoring {len(target_files)} files with legacy patterns",
                }

                agent_tasks.append(
                    {
                        "agent_id": "architect-1",
                        "agent": "architect",
                        "command": "design",
                        "args": architect_args,
                    }
                )

                # Execute architect
                result = await orchestrator.execute_parallel(agent_tasks)

            # Step 3: Generate refactoring plan (read-only)
            plan_content = f"""# Refactoring Plan

## Target Files
{chr(10).join(f"- {f}" for f in target_files)}

## Legacy Patterns Identified
{chr(10).join(f"- {p.get('message', 'Unknown pattern')}" for p in legacy_patterns[:10])}

## Modern Patterns
See architect design results for modern patterns to apply.

## Refactoring Strategy
1. Incremental refactoring (file-by-file)
2. Maintain backward compatibility
3. Test-driven refactoring
4. Verify behavior preservation
"""

            plan_path = self.project_root / "docs" / "refactoring" / "refactor-plan.md"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text(plan_content, encoding="utf-8")

            # Step 4: Apply refactoring incrementally
            refactored_files = []
        
            for target_file in target_files[:10]:  # Limit to 10 files per run
                implementer_args = {
                    "file": target_file,
                    "instructions": f"Refactor to use modern patterns while maintaining backward compatibility. Focus on: {refactor_target}",
                }

                agent_tasks.append(
                    {
                        "agent_id": f"implementer-{len(refactored_files)}",
                        "agent": "implementer",
                        "command": "refactor",
                        "args": implementer_args,
                    }
                )

                # Execute refactoring
                result = await orchestrator.execute_parallel(agent_tasks[-1:])
            
                if result.get("success"):
                    refactored_files.append(target_file)

                    # Step 5: Verify with tests
                    tester_args = {
                        "file": target_file,
                    }

                    agent_tasks.append(
                        {
                            "agent_id": f"tester-{len(refactored_files)}",
                            "agent": "tester",
                            "command": "test",
                            "args": tester_args,
                        }
                    )

                    # Execute tests
                    await orchestrator.execute_parallel(agent_tasks[-1:])

            # Step 6: Final quality review
            final_reviewer_args = {
                "files": refactored_files,
            }

            agent_tasks.append(
                {
                    "agent_id": "reviewer-2",
                    "agent": "reviewer",
                    "command": "review",
                    "args": final_reviewer_args,
                }
            )

            # Execute final review
            final_result = await orchestrator.execute_parallel(agent_tasks[-1:])

            return {
                "type": "refactor",
                "success": final_result.get("success", False),
                "agents_executed": final_result.get("total_agents", 0),
                "results": final_result.get("results", {}),
                "summary": {
                    "files_refactored": refactored_files,
                    "legacy_patterns_found": len(legacy_patterns),
                    "plan_path": str(plan_path),
                },
            }
        finally:
            close_issue(self.project_root, beads_issue_id)
