"""
Explore Orchestrator - Coordinates codebase exploration workflow.

Coordinates: Analyst → Code Discovery → Architecture Analysis → Flow Tracing → Summary Generation

This orchestrator helps developers understand and navigate existing codebases,
find relevant code, and trace execution flows without making modifications.
"""

from pathlib import Path
from typing import Any

from tapps_agents.core.config import ProjectConfig
from tapps_agents.core.multi_agent_orchestrator import MultiAgentOrchestrator
from ..intent_parser import Intent
from .base import SimpleModeOrchestrator


class ExploreOrchestrator(SimpleModeOrchestrator):
    """Orchestrator for codebase exploration."""

    def get_agent_sequence(self) -> list[str]:
        """Get the sequence of agents for explore workflow."""
        return ["analyst", "reviewer"]

    async def execute(
        self, intent: Intent, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute explore workflow.

        Args:
            intent: Parsed user intent
            parameters: Additional parameters from user input

        Returns:
            Dictionary with execution results
        """
        parameters = parameters or {}
        query = parameters.get("description") or parameters.get("query") or intent.original_input
        files = parameters.get("files", [])
        find_pattern = parameters.get("find")
        trace_pattern = parameters.get("trace")

        # Create multi-agent orchestrator
        orchestrator = MultiAgentOrchestrator(
            project_root=self.project_root,
            config=self.config,
            max_parallel=1,  # Sequential for exploration
        )

        # Step 1: Analyze exploration goals using analyst
        analyst_args = {
            "description": query,
            "context": f"Codebase exploration: {query}",
        }

        agent_tasks = [
            {
                "agent_id": "analyst-1",
                "agent": "analyst",
                "command": "gather-requirements",
                "args": analyst_args,
            },
        ]

        # Execute analyst for requirements understanding
        result = await orchestrator.execute_parallel(agent_tasks)

        # Step 2: Code discovery using file search
        # If specific find pattern is provided, search for it
        if find_pattern:
            # Use glob to find relevant files
            import glob
            
            pattern_files = list(Path(self.project_root).glob(f"**/*{find_pattern}*"))
            discovery_result = {
                "files_found": [str(f.relative_to(self.project_root)) for f in pattern_files[:20]],
                "patterns": [find_pattern],
            }
        elif files:
            # Use provided files
            discovery_result = {
                "files_found": files,
                "patterns": [],
            }
        else:
            # General exploration - find files matching query keywords
            import glob
            
            # Search for common patterns in query
            keywords = query.lower().split()
            found_files = set()
            
            for keyword in keywords[:3]:  # Limit to first 3 keywords
                # Search in common code directories
                for pattern in [f"**/*{keyword}*.py", f"**/*{keyword}*.ts", f"**/*{keyword}*.js"]:
                    pattern_files = Path(self.project_root).glob(pattern)
                    found_files.update([str(f.relative_to(self.project_root)) for f in pattern_files])
            
            discovery_result = {
                "files_found": list(found_files)[:20],
                "patterns": keywords[:3],
            }

        # Step 3: Architecture analysis using reviewer
        if discovery_result["files_found"]:
            reviewer_args = {
                "files": discovery_result["files_found"][:5],  # Analyze top 5 files
                "analyze_structure": True,
            }

            agent_tasks.append(
                {
                    "agent_id": "reviewer-1",
                    "agent": "reviewer",
                    "command": "analyze-project",
                    "args": reviewer_args,
                }
            )

            # Execute reviewer for architecture analysis
            result = await orchestrator.execute_parallel(agent_tasks)

        # Step 4: Flow tracing (if trace pattern provided)
        trace_result = None
        if trace_pattern:
            # Find files related to trace pattern
            import glob
            
            trace_keywords = trace_pattern.lower().split()
            trace_files = set()
            
            for keyword in trace_keywords[:3]:
                for pattern in [f"**/*{keyword}*.py", f"**/*{keyword}*.ts", f"**/*{keyword}*.js"]:
                    pattern_files = Path(self.project_root).glob(pattern)
                    trace_files.update([str(f.relative_to(self.project_root)) for f in pattern_files])
            
            trace_result = {
                "execution_path": list(trace_files)[:10],
                "flow_description": f"Trace flow for: {trace_pattern}",
            }

        # Step 5: Generate summary
        summary = {
            "query": query,
            "discovery": discovery_result,
            "trace": trace_result,
            "files_analyzed": discovery_result.get("files_found", [])[:10],
            "exploration_complete": True,
        }

        # Create exploration report
        report_path = self.project_root / "docs" / "exploration" / f"explore-{intent.type.value}.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        report_content = f"""# Codebase Exploration Report

## Query
{query}

## Files Discovered
{chr(10).join(f"- {f}" for f in discovery_result.get('files_found', [])[:20])}

## Architecture Analysis
See reviewer analysis results in workflow execution.

## Flow Tracing
{trace_result.get('flow_description', 'No flow tracing requested') if trace_result else 'No flow tracing requested'}

## Summary
Exploration completed successfully. Found {len(discovery_result.get('files_found', []))} relevant files.
"""

        report_path.write_text(report_content, encoding="utf-8")

        return {
            "type": "explore",
            "success": result.get("success", True),
            "agents_executed": result.get("total_agents", 0),
            "results": result.get("results", {}),
            "summary": summary,
            "report_path": str(report_path),
        }
