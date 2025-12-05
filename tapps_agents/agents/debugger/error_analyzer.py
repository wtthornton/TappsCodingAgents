"""
Error Analyzer - Analyzes errors, stack traces, and suggests fixes
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import re

from ...core.mal import MAL


class ErrorAnalyzer:
    """Analyzes errors, stack traces, and code paths to suggest fixes."""
    
    def __init__(self, mal: MAL):
        self.mal = mal
    
    async def analyze_error(
        self,
        error_message: str,
        stack_trace: Optional[str] = None,
        code_context: Optional[str] = None,
        file_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Analyze an error and provide insights.
        
        Args:
            error_message: The error message
            stack_trace: Optional stack trace
            code_context: Optional code context around the error
            file_path: Optional file path where error occurred
        
        Returns:
            Analysis result with error type, cause, and suggestions
        """
        # Extract error type and message
        error_info = self._parse_error(error_message, stack_trace)
        
        # Build prompt for LLM analysis
        prompt = self._build_analysis_prompt(error_message, stack_trace, code_context, file_path)
        
        # Get LLM analysis
        analysis_text = await self.mal.generate(prompt)
        
        # Parse LLM response
        parsed_analysis = self._parse_llm_analysis(analysis_text)
        
        return {
            "error_type": error_info["type"],
            "error_message": error_message,
            "file_location": error_info.get("file"),
            "line_number": error_info.get("line"),
            "analysis": parsed_analysis,
            "suggestions": parsed_analysis.get("suggestions", []),
            "root_cause": parsed_analysis.get("root_cause"),
            "fix_examples": parsed_analysis.get("fix_examples", [])
        }
    
    async def trace_code_path(
        self,
        file_path: Path,
        function_name: Optional[str] = None,
        line_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Trace code execution path.
        
        Args:
            file_path: Path to the file
            function_name: Optional function name to trace
            line_number: Optional line number to trace from
        
        Returns:
            Code path analysis
        """
        code = file_path.read_text(encoding='utf-8')
        
        # Analyze code structure
        structure = self._analyze_code_structure(code)
        
        # Build trace prompt
        prompt = self._build_trace_prompt(code, function_name, line_number, structure)
        
        # Get LLM trace analysis
        trace_analysis = await self.mal.generate(prompt)
        
        return {
            "file": str(file_path),
            "function": function_name,
            "line": line_number,
            "code_structure": structure,
            "trace_analysis": trace_analysis,
            "execution_path": self._parse_execution_path(trace_analysis)
        }
    
    def _parse_error(self, error_message: str, stack_trace: Optional[str] = None) -> Dict[str, Any]:
        """Parse error message and stack trace to extract information."""
        error_info = {
            "type": "Unknown",
            "message": error_message,
            "file": None,
            "line": None
        }
        
        # Extract error type (e.g., "ValueError", "AttributeError")
        type_match = re.search(r'^(\w+Error):', error_message, re.MULTILINE)
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
    
    def _analyze_code_structure(self, code: str) -> Dict[str, Any]:
        """Analyze code structure for tracing."""
        import ast
        
        structure = {
            "functions": [],
            "classes": [],
            "imports": [],
            "calls": []
        }
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    structure["functions"].append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args]
                    })
                elif isinstance(node, ast.ClassDef):
                    structure["classes"].append({
                        "name": node.name,
                        "line": node.lineno
                    })
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        structure["calls"].append({
                            "function": node.func.id,
                            "line": node.lineno
                        })
        except SyntaxError:
            pass
        
        return structure
    
    def _build_analysis_prompt(
        self,
        error_message: str,
        stack_trace: Optional[str],
        code_context: Optional[str],
        file_path: Optional[Path]
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
            ""
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
        
        prompt_parts.extend([
            "Provide analysis in the following format:",
            "ROOT_CAUSE: <explanation>",
            "ISSUE: <specific issue>",
            "SUGGESTIONS:",
            "1. <first suggestion>",
            "2. <second suggestion>",
            "FIX_EXAMPLES:",
            "```python",
            "<code example>",
            "```"
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_trace_prompt(
        self,
        code: str,
        function_name: Optional[str],
        line_number: Optional[int],
        structure: Dict[str, Any]
    ) -> str:
        """Build prompt for code path tracing."""
        prompt_parts = [
            "Trace the execution path of this code:",
            ""
        ]
        
        if function_name:
            prompt_parts.append(f"Starting from function: {function_name}")
        if line_number:
            prompt_parts.append(f"Starting from line: {line_number}")
        
        prompt_parts.append("")
        prompt_parts.append("Code structure:")
        prompt_parts.append(f"- Functions: {', '.join([f['name'] for f in structure['functions']])}")
        prompt_parts.append(f"- Classes: {', '.join([c['name'] for c in structure['classes']])}")
        prompt_parts.append("")
        prompt_parts.append("Code:")
        prompt_parts.append("```python")
        prompt_parts.append(code[:3000])  # Limit code size
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("Provide execution path analysis:")
        
        return "\n".join(prompt_parts)
    
    def _parse_llm_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse LLM analysis response."""
        parsed = {
            "root_cause": "",
            "issue": "",
            "suggestions": [],
            "fix_examples": []
        }
        
        # Extract root cause
        root_cause_match = re.search(r'ROOT_CAUSE:\s*(.+?)(?=\n[A-Z_]+:|$)', analysis_text, re.DOTALL)
        if root_cause_match:
            parsed["root_cause"] = root_cause_match.group(1).strip()
        
        # Extract issue
        issue_match = re.search(r'ISSUE:\s*(.+?)(?=\n[A-Z_]+:|$)', analysis_text, re.DOTALL)
        if issue_match:
            parsed["issue"] = issue_match.group(1).strip()
        
        # Extract suggestions
        suggestions_match = re.search(r'SUGGESTIONS:\s*(.+?)(?=\n[A-Z_]+:|$)', analysis_text, re.DOTALL)
        if suggestions_match:
            suggestions_text = suggestions_match.group(1)
            # Extract numbered suggestions
            suggestion_lines = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|$)', suggestions_text, re.DOTALL)
            parsed["suggestions"] = [s.strip() for s in suggestion_lines]
        
        # Extract fix examples
        fix_examples_match = re.search(r'FIX_EXAMPLES:\s*```python\s*(.+?)```', analysis_text, re.DOTALL)
        if fix_examples_match:
            parsed["fix_examples"] = [fix_examples_match.group(1).strip()]
        
        return parsed
    
    def _parse_execution_path(self, trace_analysis: str) -> List[str]:
        """Parse execution path from trace analysis."""
        # Simple extraction - look for function calls or line references
        path = []
        
        # Look for patterns like "calls function X" or "line Y"
        calls = re.findall(r'(?:calls|executes|runs)\s+(\w+)', trace_analysis, re.IGNORECASE)
        path.extend(calls)
        
        return path if path else ["Execution path extracted from analysis"]

