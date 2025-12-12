"""
Test Generator - Generates tests from code analysis using LLM
"""

import ast
from pathlib import Path
from typing import Any

from ...core.mal import MAL


class TestGenerator:
    """Generates tests from code analysis using LLM."""

    def __init__(self, mal: MAL):
        self.mal = mal

    async def generate_unit_tests(
        self,
        code_path: Path,
        test_path: Path | None = None,
        context: str | None = None,
        expert_guidance: str | None = None,
    ) -> str:
        """
        Generate unit tests for a given code file.

        Args:
            code_path: Path to the source code file
            test_path: Optional path where test will be written
            context: Optional context (existing tests, patterns, etc.)

        Returns:
            Generated test code as string
        """
        # Read source code
        code = code_path.read_text(encoding="utf-8")

        # Analyze code structure
        analysis = self._analyze_code(code, code_path)

        # Build prompt for LLM
        prompt = self._build_unit_test_prompt(
            code, analysis, test_path, context, expert_guidance
        )

        # Generate test code
        test_code = await self.mal.generate(prompt)

        return test_code

    async def generate_integration_tests(
        self,
        file_paths: list[Path],
        test_path: Path | None = None,
        context: str | None = None,
        expert_guidance: str | None = None,
    ) -> str:
        """
        Generate integration tests for multiple files/modules.

        Args:
            file_paths: List of source code file paths
            test_path: Optional path where test will be written
            context: Optional context

        Returns:
            Generated test code as string
        """
        # Read all source files
        code_snippets = []
        for path in file_paths:
            code = path.read_text(encoding="utf-8")
            code_snippets.append(f"# {path.name}\n{code}\n")

        combined_code = "\n".join(code_snippets)

        # Build prompt for LLM
        prompt = self._build_integration_test_prompt(
            combined_code, test_path, context, expert_guidance
        )

        # Generate test code
        test_code = await self.mal.generate(prompt)

        return test_code

    def _analyze_code(self, code: str, file_path: Path) -> dict[str, Any]:
        """Analyze code structure to extract functions, classes, etc."""
        analysis = {
            "file_name": file_path.name,
            "functions": [],
            "classes": [],
            "imports": [],
            "test_framework": self._detect_test_framework(code),
        }

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis["functions"].append(
                        {
                            "name": node.name,
                            "args": [arg.arg for arg in node.args.args],
                            "decorators": [
                                ast.unparse(d) if hasattr(ast, "unparse") else str(d)
                                for d in node.decorator_list
                            ],
                        }
                    )
                elif isinstance(node, ast.ClassDef):
                    methods = [
                        n.name for n in node.body if isinstance(n, ast.FunctionDef)
                    ]
                    analysis["classes"].append({"name": node.name, "methods": methods})
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        analysis["imports"].extend([alias.name for alias in node.names])
                    else:
                        analysis["imports"].append(node.module or "")
        except SyntaxError:
            # If code has syntax errors, return basic analysis
            pass

        return analysis

    def _detect_test_framework(self, code: str) -> str:
        """Detect which test framework is being used."""
        if "import pytest" in code or "from pytest" in code:
            return "pytest"
        elif "import unittest" in code or "from unittest" in code:
            return "unittest"
        elif "import nose" in code or "from nose" in code:
            return "nose"
        else:
            return "pytest"  # Default

    def _build_unit_test_prompt(
        self,
        code: str,
        analysis: dict[str, Any],
        test_path: Path | None,
        context: str | None,
        expert_guidance: str | None = None,
    ) -> str:
        """Build prompt for unit test generation."""
        prompt_parts = [
            "Generate comprehensive unit tests for the following Python code.",
            "",
            f"Source file: {analysis['file_name']}",
            "",
            "Code structure:",
            f"- Functions: {', '.join([f['name'] for f in analysis['functions']]) if analysis['functions'] else 'None'}",
            f"- Classes: {', '.join([c['name'] for c in analysis['classes']]) if analysis['classes'] else 'None'}",
            f"- Imports: {', '.join(analysis['imports'][:10]) if analysis['imports'] else 'None'}",
            "",
            f"Use {analysis['test_framework']} framework.",
            "",
            "Source code:",
            "```python",
            code[:5000],  # Limit code size
            "```",
            "",
        ]

        if test_path:
            prompt_parts.append(f"Write tests to: {test_path}")
            prompt_parts.append("")

        if context:
            prompt_parts.append("Context:")
            prompt_parts.append(context)
            prompt_parts.append("")

        if expert_guidance:
            prompt_parts.append("Expert Guidance:")
            prompt_parts.append(expert_guidance)
            prompt_parts.append("")

        prompt_parts.extend(
            [
                "Requirements:",
                "- Test all public functions and methods",
                "- Include edge cases and error handling",
                "- Use descriptive test names",
                "- Include docstrings for test functions",
                "- Mock external dependencies",
                "- Ensure 80%+ coverage",
                "",
                "Generate only the test code (no explanations):",
            ]
        )

        return "\n".join(prompt_parts)

    def _build_integration_test_prompt(
        self,
        code: str,
        test_path: Path | None,
        context: str | None,
        expert_guidance: str | None = None,
    ) -> str:
        """Build prompt for integration test generation."""
        prompt_parts = [
            "Generate comprehensive integration tests for the following Python code.",
            "",
            "The code consists of multiple modules that work together.",
            "",
            "Source code:",
            "```python",
            code[:8000],  # Larger limit for integration tests
            "```",
            "",
        ]

        if test_path:
            prompt_parts.append(f"Write tests to: {test_path}")
            prompt_parts.append("")

        if context:
            prompt_parts.append("Context:")
            prompt_parts.append(context)
            prompt_parts.append("")

        if expert_guidance:
            prompt_parts.append("Expert Guidance:")
            prompt_parts.append(expert_guidance)
            prompt_parts.append("")

        prompt_parts.extend(
            [
                "Requirements:",
                "- Test interactions between modules",
                "- Test end-to-end workflows",
                "- Include setup and teardown",
                "- Use descriptive test names",
                "- Mock external services",
                "",
                "Generate only the test code (no explanations):",
            ]
        )

        return "\n".join(prompt_parts)
