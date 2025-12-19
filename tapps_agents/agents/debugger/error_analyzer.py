"""
Error Analyzer - Prepares error analysis instructions for Cursor Skills
"""

import re
from pathlib import Path
from typing import Any

from ...core.instructions import ErrorAnalysisInstruction


class ErrorAnalyzer:
    """Prepares error analysis instructions for Cursor Skills execution."""

    def __init__(self):
        """Initialize error analyzer (no MAL dependency)."""
        pass

    def prepare_error_analysis(
        self,
        error_message: str,
        stack_trace: str | None = None,
        code_context: str | None = None,
        file_path: Path | None = None,
    ) -> ErrorAnalysisInstruction:
        """
        Prepare error analysis instruction for Cursor Skills.

        Args:
            error_message: The error message
            stack_trace: Optional stack trace
            code_context: Optional code context around the error
            file_path: Optional file path where error occurred

        Returns:
            ErrorAnalysisInstruction object for Cursor Skills execution
        """
        # Extract error info for context lines
        error_info = self._parse_error(error_message, stack_trace)
        context_lines = 50  # Default context lines

        return ErrorAnalysisInstruction(
            error_message=error_message,
            stack_trace=stack_trace,
            context_lines=context_lines,
        )

    def prepare_code_trace(
        self,
        file_path: Path,
        function_name: str | None = None,
        line_number: int | None = None,
    ) -> ErrorAnalysisInstruction:
        """
        Prepare code trace instruction for Cursor Skills.

        Args:
            file_path: Path to the file
            function_name: Optional function name to trace
            line_number: Optional line number to trace from

        Returns:
            ErrorAnalysisInstruction object for Cursor Skills execution
        """
        error_message = f"Trace code path in {file_path}"
        if function_name:
            error_message += f" starting from function {function_name}"
        if line_number:
            error_message += f" at line {line_number}"

        return ErrorAnalysisInstruction(
            error_message=error_message,
            stack_trace=None,
            context_lines=100,  # More context for tracing
        )

    def _parse_error(
        self, error_message: str, stack_trace: str | None = None
    ) -> dict[str, Any]:
        """Parse error message and stack trace to extract information."""
        error_info: dict[str, Any] = {
            "type": "Unknown",
            "message": error_message,
            "file": None,
            "line": None,
        }

        # Extract error type (e.g., "ValueError", "AttributeError")
        type_match = re.search(r"^(\w+Error):", error_message, re.MULTILINE)
        if type_match:
            error_info["type"] = type_match.group(1)

        # Parse stack trace if provided
        if stack_trace:
            # Extract file and line from stack trace
            # Format: File "path/to/file.py", line X, in function_name
            file_match = re.search(r'File "([^"]+)", line (\d+)', stack_trace)
            if file_match:
                error_info["file"] = file_match.group(1)
                error_info["line"] = int(file_match.group(2))

        return error_info

    def _analyze_code_structure(self, code: str) -> dict[str, Any]:
        """Analyze code structure for tracing."""
        import ast

        functions: list[dict[str, Any]] = []
        classes: list[dict[str, Any]] = []
        imports: list[str] = []
        calls: list[dict[str, Any]] = []
        structure: dict[str, Any] = {
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "calls": calls,
        }

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "args": [arg.arg for arg in node.args.args],
                        }
                    )
                elif isinstance(node, ast.ClassDef):
                    classes.append({"name": node.name, "line": node.lineno})
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        calls.append({"function": node.func.id, "line": node.lineno})
        except SyntaxError:
            pass

        return structure

    def _build_analysis_prompt(
        self,
        error_message: str,
        stack_trace: str | None,
        code_context: str | None,
        file_path: Path | None,
    ) -> str:
        """Build prompt for error analysis."""
        prompt_parts = [
            "Analyze the following error and provide:",
            "1. Root cause of the error",
            "2. Specific issue explanation",
            "3. Step-by-step fix suggestions",
            "4. Code examples for the fix",
            "",
            f"Error: {error_message}",
            "",
        ]

        if stack_trace:
            prompt_parts.append("Stack trace:")
            prompt_parts.append(stack_trace)
            prompt_parts.append("")

        if file_path:
            prompt_parts.append(f"File: {file_path}")
            prompt_parts.append("")

        if code_context:
            prompt_parts.append("Code context:")
            prompt_parts.append("```python")
            prompt_parts.append(code_context[:2000])  # Limit context size
            prompt_parts.append("```")
            prompt_parts.append("")

        prompt_parts.extend(
            [
                "Provide analysis in the following format:",
                "ROOT_CAUSE: <explanation>",
                "ISSUE: <specific issue>",
                "SUGGESTIONS:",
                "1. <first suggestion>",
                "2. <second suggestion>",
                "FIX_EXAMPLES:",
                "```python",
                "<code example>",
                "```",
            ]
        )

        return "\n".join(prompt_parts)

    def _build_trace_prompt(
        self,
        code: str,
        function_name: str | None,
        line_number: int | None,
        structure: dict[str, Any],
    ) -> str:
        """Build prompt for code path tracing."""
        prompt_parts = ["Trace the execution path of this code:", ""]

        if function_name:
            prompt_parts.append(f"Starting from function: {function_name}")
        if line_number:
            prompt_parts.append(f"Starting from line: {line_number}")

        prompt_parts.append("")
        prompt_parts.append("Code structure:")
        prompt_parts.append(
            f"- Functions: {', '.join([f['name'] for f in structure['functions']])}"
        )
        prompt_parts.append(
            f"- Classes: {', '.join([c['name'] for c in structure['classes']])}"
        )
        prompt_parts.append("")
        prompt_parts.append("Code:")
        prompt_parts.append("```python")
        prompt_parts.append(code[:3000])  # Limit code size
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("Provide execution path analysis:")

        return "\n".join(prompt_parts)

    def _parse_llm_analysis(self, analysis_text: str) -> dict[str, Any]:
        """Parse LLM analysis response."""
        parsed = {"root_cause": "", "issue": "", "suggestions": [], "fix_examples": []}

        # Extract root cause
        root_cause_match = re.search(
            r"ROOT_CAUSE:\s*(.+?)(?=\n[A-Z_]+:|$)", analysis_text, re.DOTALL
        )
        if root_cause_match:
            parsed["root_cause"] = root_cause_match.group(1).strip()

        # Extract issue
        issue_match = re.search(
            r"ISSUE:\s*(.+?)(?=\n[A-Z_]+:|$)", analysis_text, re.DOTALL
        )
        if issue_match:
            parsed["issue"] = issue_match.group(1).strip()

        # Extract suggestions
        suggestions_match = re.search(
            r"SUGGESTIONS:\s*(.+?)(?=\n[A-Z_]+:|$)", analysis_text, re.DOTALL
        )
        if suggestions_match:
            suggestions_text = suggestions_match.group(1)
            # Extract numbered suggestions
            suggestion_lines = re.findall(
                r"\d+\.\s*(.+?)(?=\n\d+\.|$)", suggestions_text, re.DOTALL
            )
            parsed["suggestions"] = [s.strip() for s in suggestion_lines]

        # Extract fix examples
        fix_examples_match = re.search(
            r"FIX_EXAMPLES:\s*```python\s*(.+?)```", analysis_text, re.DOTALL
        )
        if fix_examples_match:
            parsed["fix_examples"] = [fix_examples_match.group(1).strip()]

        return parsed

    def _parse_execution_path(self, trace_analysis: str) -> list[str]:
        """Parse execution path from trace analysis."""
        # Simple extraction - look for function calls or line references
        path = []

        # Look for patterns like "calls function X" or "line Y"
        calls = re.findall(
            r"(?:calls|executes|runs)\s+(\w+)", trace_analysis, re.IGNORECASE
        )
        path.extend(calls)

        return path if path else ["Execution path extracted from analysis"]
