"""
Plan Analysis Orchestrator - Coordinates safe, read-only code analysis workflow.

Coordinates: Analyst → Architect → Impact Analysis → Plan Generation

This orchestrator provides safe exploration of codebases and planning for complex
changes without executing any modifications (read-only mode).
"""

from pathlib import Path
from typing import Any

from tapps_agents.core.multi_agent_orchestrator import MultiAgentOrchestrator

from ..intent_parser import Intent
from .base import SimpleModeOrchestrator


class PlanAnalysisOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for safe, read-only code analysis and planning."""

    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for plan analysis workflow."""
        return ["analyst", "architect", "reviewer"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute plan analysis workflow (read-only).

        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input

        Returns:
            Dictionary with execution results (no code modifications)
        """
        parameters = parameters or {}
        query = parameters.get("description") or parameters.get("query") or intent.original_input
        explore = parameters.get("explore")
        plan_target = query

        # Create multi-agent orchestrator in read-only mode
        orchestrator = MultiAgentOrchestrator(
            project_root=self.project_root,
            config=self.config,
            max_parallel=1,  # Sequential for analysis
        )

        # Mark as read-only operation

        agent_tasks = []

        # Step 1: Analyze requirements using analyst (read-only)
        analyst_args = {
            "description": plan_target,
            "context": "Safe code analysis and planning - read-only mode",
        }

        agent_tasks.append(
            {
                "agent_id": "analyst-1",
                "agent": "analyst",
                "command": "gather-requirements",
                "args": analyst_args,
                "read_only": True,  # Ensure no modifications
            }
        )

        # Execute analyst
        result = await orchestrator.execute_parallel(agent_tasks)

        analyst_result = result.get("results", {}).get("analyst-1", {})
        requirements = analyst_result.get("result", {}) if analyst_result.get("success") else {}

        # Step 2: Code exploration (if explore is specified)
        exploration_results = None
        if explore:
            # Find files related to exploration query
            
            explore_keywords = explore.lower().split()
            found_files = set()
            
            for keyword in explore_keywords[:3]:
                for pattern in [f"**/*{keyword}*.py", f"**/*{keyword}*.ts", f"**/*{keyword}*.js"]:
                    pattern_files = Path(self.project_root).glob(pattern)
                    found_files.update([str(f.relative_to(self.project_root)) for f in pattern_files])
            
            exploration_results = {
                "files_found": list(found_files)[:20],
                "patterns": explore_keywords[:3],
            }

        # Step 3: Architecture planning using architect (read-only)
        architect_args = {
            "description": f"Plan architecture changes for: {plan_target}",
            "context": "Read-only architecture planning",
        }

        agent_tasks.append(
            {
                "agent_id": "architect-1",
                "agent": "architect",
                "command": "design",
                "args": architect_args,
                "read_only": True,  # Ensure no modifications
            }
        )

        # Execute architect
        result = await orchestrator.execute_parallel(agent_tasks[-1:])

        architect_result = result.get("results", {}).get("architect-1", {})
        architecture_plan = architect_result.get("result", {}) if architect_result.get("success") else {}

        # Step 4: Impact analysis using reviewer (read-only)
        if exploration_results and exploration_results.get("files_found"):
            reviewer_args = {
                "files": exploration_results["files_found"][:10],
                "analyze_impact": True,
                "read_only": True,
            }

            agent_tasks.append(
                {
                    "agent_id": "reviewer-1",
                    "agent": "reviewer",
                    "command": "analyze-project",
                    "args": reviewer_args,
                    "read_only": True,  # Ensure no modifications
                }
            )

            # Execute impact analysis
            result = await orchestrator.execute_parallel(agent_tasks[-1:])

            reviewer_result = result.get("results", {}).get("reviewer-1", {})
            impact_analysis = reviewer_result.get("result", {}) if reviewer_result.get("success") else {}
        else:
            impact_analysis = {}

        # Step 5: Generate comprehensive plan document
        plan_content = f"""# Plan Analysis Report

## Analysis Target
{plan_target}

## Requirements Analysis
{requirements.get('summary', 'See analyst results')}

## Architecture Plan
{architecture_plan.get('summary', 'See architect results')}

## Exploration Results
{chr(10).join(f"- {f}" for f in exploration_results.get('files_found', [])[:20]) if exploration_results else 'No exploration requested'}

## Impact Analysis
{impact_analysis.get('summary', 'See reviewer results')}

## Implementation Plan

### Step 1: Preparation
- Review all affected components
- Verify dependencies
- Check test coverage

### Step 2: Implementation
- Follow architecture plan
- Apply changes incrementally
- Maintain backward compatibility

### Step 3: Verification
- Run comprehensive tests
- Verify behavior preservation
- Check quality gates

## Read-Only Analysis Complete
This analysis was performed in read-only mode. No code modifications were made.

## Next Steps
1. Review this plan
2. Discuss with team if needed
3. Execute implementation when ready
"""

        plan_path = self.project_root / "docs" / "planning" / f"plan-analysis-{intent.type.value}.md"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(plan_content, encoding="utf-8")

        return {
            "type": "plan-analysis",
            "success": result.get("success", True),
            "read_only": True,
            "agents_executed": result.get("total_agents", 0),
            "results": result.get("results", {}),
            "summary": {
                "requirements": requirements,
                "architecture": architecture_plan,
                "impact": impact_analysis,
                "exploration": exploration_results,
                "plan_path": str(plan_path),
            },
        }
