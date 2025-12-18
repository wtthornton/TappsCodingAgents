"""
Debugger Agent Handler

Handles execution of debugger agent steps.

Epic 20: Complexity Reduction - Story 20.1
"""

import json
from pathlib import Path
from typing import Any

from ..models import WorkflowStep
from .base import AgentExecutionHandler


class DebuggerHandler(AgentExecutionHandler):
    """Handler for debugger agent execution."""
    
    def supports(self, agent_name: str, action: str) -> bool:
        """Check if this handler supports debugger agent."""
        return (
            agent_name == "debugger"
            and action in {"analyze_error", "analyze-error", "analyze"}
        )
    
    async def execute(
        self,
        step: WorkflowStep,
        action: str,
        target_path: Path | None,
    ) -> list[dict[str, Any]]:
        """
        Execute debugger step.
        
        Args:
            step: Workflow step definition
            action: Normalized action name
            target_path: Target file path
            
        Returns:
            List of created artifacts
        """
        if not target_path or not target_path.exists():
            raise ValueError(
                "Debugger step requires a target file. Provide --file <path> "
                "(or ensure example_bug.py exists)."
            )
        
        # Capture exception from target file
        if self.executor and hasattr(self.executor, "_capture_python_exception"):
            error_message, stack_trace = self.executor._capture_python_exception(target_path)
        else:
            error_message, stack_trace = None, None
        
        if not error_message:
            error_message = (
                f"Bug(s) reported in {target_path.name} "
                "(no runtime traceback captured)."
            )
        
        # Run debugger agent
        debug_result = await self.run_agent(
            "debugger",
            "analyze-error",
            error_message=error_message,
            stack_trace=stack_trace,
        )
        self.state.variables["debugger_result"] = debug_result
        
        # Create debug report artifact if requested
        created_artifacts: list[dict[str, Any]] = []
        if "debug-report.md" in (step.creates or []):
            report_path = self.project_root / "debug-report.md"
            report_lines = [
                "# Debug Report",
                "",
                f"## Target: `{target_path}`",
                "",
                "## Error message",
                "```",
                error_message or "",
                "```",
            ]
            if stack_trace:
                report_lines += ["", "## Stack trace", "```", stack_trace, "```"]
            report_lines += [
                "",
                "## Analysis (DebuggerAgent)",
                "```json",
                json.dumps(debug_result, indent=2),
                "```",
            ]
            report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
            created_artifacts.append(
                {"name": "debug-report.md", "path": str(report_path)}
            )
        
        return created_artifacts

