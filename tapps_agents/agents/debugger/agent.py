"""
Debugger Agent - Analyzes errors and suggests fixes
"""

from pathlib import Path
from typing import Any

from ...core.agent_base import BaseAgent
from ...core.config import ProjectConfig, load_config
from ...core.mal import MAL
from .error_analyzer import ErrorAnalyzer


class DebuggerAgent(BaseAgent):
    """
    Debugger Agent - Error analysis and debugging.

    Permissions: Read, Write, Edit, Grep, Glob, Bash

    ⚠️ CRITICAL ACCURACY REQUIREMENT:
    - NEVER make up, invent, or fabricate information - Only report verified facts
    - ALWAYS verify claims by checking actual results, not just test pass/fail
    - Verify API calls succeed - inspect response data, status codes, error messages
    - Distinguish between code paths executing and actual functionality working
    - Admit uncertainty explicitly when you cannot verify
    """

    def __init__(self, mal: MAL | None = None, config: ProjectConfig | None = None):
        super().__init__(
            agent_id="debugger", agent_name="Debugger Agent", config=config
        )
        # Use config if provided, otherwise load defaults
        if config is None:
            config = load_config()
        self.config = config

        # Initialize MAL with config
        mal_config = config.mal if config else None
        self.mal = mal or MAL(
            ollama_url=mal_config.ollama_url if mal_config else "http://localhost:11434"
        )

        # Initialize error analyzer
        self.error_analyzer = ErrorAnalyzer(self.mal)

        # Get debugger config
        debugger_config = config.agents.debugger if config and config.agents else None
        self.include_code_examples = (
            debugger_config.include_code_examples if debugger_config else True
        )
        self.max_context_lines = (
            debugger_config.max_context_lines if debugger_config else 50
        )

    def get_commands(self) -> list[dict[str, str]]:
        """Return list of available commands."""
        commands = super().get_commands()
        commands.extend(
            [
                {"command": "*debug", "description": "Debug an error or issue"},
                {
                    "command": "*analyze-error",
                    "description": "Analyze error message and stack trace",
                },
                {"command": "*trace", "description": "Trace code execution path"},
            ]
        )
        return commands

    async def run(self, command: str, **kwargs) -> dict[str, Any]:
        """Execute a command."""
        if command == "debug":
            return await self.debug_command(**kwargs)
        elif command == "analyze-error":
            return await self.analyze_error_command(**kwargs)
        elif command == "trace":
            return await self.trace_command(**kwargs)
        elif command == "help":
            return await self._help()
        else:
            return {"error": f"Unknown command: {command}"}

    async def debug_command(
        self,
        error_message: str | None = None,
        file: str | None = None,
        line: int | None = None,
        stack_trace: str | None = None,
    ) -> dict[str, Any]:
        """
        Debug an error or issue.

        Args:
            error_message: Error message to debug
            file: Optional file path where error occurred
            line: Optional line number
            stack_trace: Optional stack trace
        """
        if not error_message:
            return {"error": "Error message required"}

        # Get code context if file provided
        code_context = None
        file_path = None

        if file:
            file_path = Path(file)
            if file_path.exists():
                self._validate_path(file_path)
                code = file_path.read_text(encoding="utf-8")
                # Extract context around error line
                if line:
                    lines = code.split("\n")
                    start = max(0, line - self.max_context_lines // 2)
                    end = min(len(lines), line + self.max_context_lines // 2)
                    code_context = "\n".join(lines[start:end])
                else:
                    # Use first 100 lines if no line specified
                    code_context = "\n".join(code.split("\n")[:100])

        # Analyze error
        analysis = await self.error_analyzer.analyze_error(
            error_message=error_message,
            stack_trace=stack_trace,
            code_context=code_context,
            file_path=file_path,
        )

        return {
            "type": "debug",
            "error_message": error_message,
            "analysis": analysis,
            "suggestions": analysis.get("suggestions", []),
            "fix_examples": (
                analysis.get("fix_examples", []) if self.include_code_examples else []
            ),
        }

    async def analyze_error_command(
        self,
        error_message: str,
        stack_trace: str | None = None,
        code_context: str | None = None,
    ) -> dict[str, Any]:
        """
        Analyze error message and stack trace.

        Args:
            error_message: Error message
            stack_trace: Stack trace
            code_context: Code context around error
        """
        if not error_message:
            return {"error": "Error message required"}

        analysis = await self.error_analyzer.analyze_error(
            error_message=error_message,
            stack_trace=stack_trace,
            code_context=code_context,
        )

        return {
            "type": "error_analysis",
            "error_type": analysis["error_type"],
            "error_message": error_message,
            "root_cause": analysis.get("root_cause"),
            "issue": analysis.get("analysis", {}).get("issue"),
            "suggestions": analysis.get("suggestions", []),
            "fix_examples": (
                analysis.get("fix_examples", []) if self.include_code_examples else []
            ),
        }

    async def trace_command(
        self, file: str, function: str | None = None, line: int | None = None
    ) -> dict[str, Any]:
        """
        Trace code execution path.

        Args:
            file: File path to trace
            function: Optional function name to trace from
            line: Optional line number to trace from
        """
        file_path = Path(file)
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        self._validate_path(file_path)

        trace_result = await self.error_analyzer.trace_code_path(
            file_path=file_path, function_name=function, line_number=line
        )

        return {
            "type": "trace",
            "file": str(file_path),
            "function": function,
            "line": line,
            "trace_analysis": trace_result.get("trace_analysis"),
            "execution_path": trace_result.get("execution_path", []),
        }

    async def _help(self) -> dict[str, Any]:
        """Generate help text."""
        help_text = self.format_help()
        help_text += "\n\nExamples:\n"
        help_text += '  *debug "ValueError: invalid literal" --file code.py --line 42\n'
        help_text += '  *analyze-error "IndexError: list index out of range" --stack-trace "..."\n'
        help_text += "  *trace code.py --function process_data\n"
        return {"type": "help", "content": help_text}

    async def close(self):
        """Close agent and clean up resources."""
        if self.mal:
            await self.mal.close()
