"""
Test Generator - Prepares test generation instructions for Cursor Skills

Phase 2.1: Enhanced with coverage analysis and language-aware test generation
"""

import ast
from pathlib import Path
from typing import Any

from ...core.instructions import TestGenerationInstruction
from ...core.language_detector import Language, LanguageDetector
from .coverage_analyzer import CoverageAnalyzer, CoverageReport


class TestGenerator:
    """
    Prepares test generation instructions for Cursor Skills execution.
    
    Enhanced with:
    - Language-aware test framework detection
    - Async coverage analysis
    - Coverage measurement for Python (pytest) and TypeScript/React (jest/vitest)
    """

    def __init__(self):
        """Initialize test generator."""
        self.language_detector = LanguageDetector()
        self.coverage_analyzer = CoverageAnalyzer()

    def prepare_unit_tests(
        self,
        code_path: Path,
        test_path: Path | None = None,
        context: str | None = None,
        expert_guidance: str | None = None,
        focus: str | None = None,
    ) -> TestGenerationInstruction:
        """
        Prepare unit test generation instruction for Cursor Skills.

        Args:
            code_path: Path to the source code file
            test_path: Optional path where test will be written
            context: Optional context (existing tests, patterns, etc.)
            expert_guidance: Optional expert guidance for test generation

        Returns:
            TestGenerationInstruction object for Cursor Skills execution
        """
        # Read source code
        code = code_path.read_text(encoding="utf-8")

        # Detect language
        detection_result = self.language_detector.detect_language(code_path, code)
        language = detection_result.language

        # Analyze code structure
        analysis = self._analyze_code(code, code_path)

        # Detect test framework based on language
        test_framework = self._detect_test_framework_for_language(language, code)

        # Build coverage requirements with focus areas if provided
        coverage_requirements = {
            "target_coverage": 80.0,
            "test_types": ["unit"],
            "context": context,
            "expert_guidance": expert_guidance,
            "language": language.value,
        }
        if focus:
            focus_areas = [area.strip() for area in focus.split(",")]
            coverage_requirements["focus_areas"] = focus_areas

        return TestGenerationInstruction(
            target_file=str(test_path) if test_path else str(code_path),
            test_framework=test_framework,
            coverage_requirements=coverage_requirements,
        )

    async def measure_coverage(
        self,
        file_path: Path,
        test_file_path: Path | None = None,
        project_root: Path | None = None,
    ) -> CoverageReport:
        """
        Measure test coverage for a file using language-specific tools.
        
        Phase 2.1: Coverage Analysis Integration
        
        Args:
            file_path: Path to the source file
            test_file_path: Optional path to test file
            project_root: Optional project root directory
            
        Returns:
            CoverageReport with coverage percentage and metrics
        """
        # Detect language
        code = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
        detection_result = self.language_detector.detect_language(file_path, code)
        language = detection_result.language

        # Measure coverage using language-specific analyzer
        return await self.coverage_analyzer.measure_coverage(
            file_path, language, test_file_path, project_root
        )

    def _detect_test_framework_for_language(
        self, language: Language, code: str
    ) -> str:
        """
        Detect test framework based on language.
        
        Args:
            language: Detected language
            code: Source code content
            
        Returns:
            Test framework name (pytest, jest, vitest, etc.)
        """
        if language == Language.PYTHON:
            # Check code for framework hints
            if "import pytest" in code or "from pytest" in code:
                return "pytest"
            elif "import unittest" in code or "from unittest" in code:
                return "unittest"
            return "pytest"  # Default for Python

        elif language in [Language.TYPESCRIPT, Language.JAVASCRIPT, Language.REACT]:
            # Check package.json or code for framework
            # This is a basic check - full detection is in CoverageAnalyzer
            if "vitest" in code.lower():
                return "vitest"
            return "jest"  # Default for TypeScript/JavaScript

        return "pytest"  # Fallback default

    def prepare_integration_tests(
        self,
        file_paths: list[Path],
        test_path: Path | None = None,
        context: str | None = None,
        expert_guidance: str | None = None,
        focus: str | None = None,
    ) -> TestGenerationInstruction:
        """
        Prepare integration test generation instruction for Cursor Skills.

        Args:
            file_paths: List of source code file paths
            test_path: Optional path where test will be written
            context: Optional context
            expert_guidance: Optional expert guidance
            focus: Optional comma-separated focus areas

        Returns:
            TestGenerationInstruction object for Cursor Skills execution
        """
        # Use first file path or test_path as target
        target_file = str(test_path) if test_path else str(file_paths[0]) if file_paths else ""

        coverage_requirements = {
            "target_coverage": 80.0,
            "test_types": ["integration"],
            "file_paths": [str(p) for p in file_paths],
            "context": context,
            "expert_guidance": expert_guidance,
        }
        if focus:
            focus_areas = [area.strip() for area in focus.split(",")]
            coverage_requirements["focus_areas"] = focus_areas

        return TestGenerationInstruction(
            target_file=target_file,
            test_framework="pytest",
            coverage_requirements=coverage_requirements,
        )

    def prepare_e2e_tests(
        self,
        project_root: Path,
        test_path: Path | None = None,
        context: str | None = None,
        expert_guidance: str | None = None,
    ) -> TestGenerationInstruction | None:
        """
        Prepare end-to-end (E2E) test generation instruction for Cursor Skills.

        Args:
            project_root: Root directory of the project
            test_path: Optional path where test will be written
            context: Optional context
            expert_guidance: Optional expert guidance

        Returns:
            TestGenerationInstruction object for Cursor Skills execution, or None if E2E framework not detected
        """
        # Detect E2E framework
        e2e_framework = self._detect_e2e_framework(project_root)
        if not e2e_framework:
            return None

        # Analyze project structure
        project_analysis = self._analyze_project_structure(project_root)

        target_file = str(test_path) if test_path else str(project_root)

        coverage_requirements = {
            "target_coverage": 80.0,
            "test_types": ["e2e"],
            "e2e_framework": e2e_framework,
            "project_analysis": project_analysis,
            "context": context,
            "expert_guidance": expert_guidance,
        }

        return TestGenerationInstruction(
            target_file=target_file,
            test_framework=e2e_framework,
            coverage_requirements=coverage_requirements,
        )

    def _detect_e2e_framework(self, project_root: Path) -> str | None:
        """
        Detect E2E testing framework in the project.

        Returns:
            Framework name ("playwright", "selenium", "cypress", "pytest-playwright") or None
        """
        project_root = Path(project_root)

        # Check for Playwright
        playwright_config = project_root / "playwright.config.js"
        playwright_config_ts = project_root / "playwright.config.ts"
        playwright_pyproject = project_root / "pyproject.toml"
        if (
            playwright_config.exists()
            or playwright_config_ts.exists()
            or (playwright_pyproject.exists() and "playwright" in playwright_pyproject.read_text())
        ):
            return "playwright"

        # Check for pytest-playwright
        if (project_root / "pytest.ini").exists():
            pytest_ini_content = (project_root / "pytest.ini").read_text()
            if "playwright" in pytest_ini_content.lower():
                return "pytest-playwright"

        # Check requirements.txt or pyproject.toml for pytest-playwright
        for req_file in [project_root / "requirements.txt", project_root / "pyproject.toml"]:
            if req_file.exists():
                content = req_file.read_text().lower()
                if "pytest-playwright" in content or "playwright" in content:
                    return "pytest-playwright"

        # Check for Selenium
        selenium_config = project_root / "selenium.config.js"
        for req_file in [project_root / "requirements.txt", project_root / "pyproject.toml"]:
            if req_file.exists():
                content = req_file.read_text().lower()
                if "selenium" in content:
                    return "selenium"
        if selenium_config.exists():
            return "selenium"

        # Check for Cypress (JavaScript/TypeScript projects)
        cypress_config = project_root / "cypress.config.js"
        cypress_config_ts = project_root / "cypress.config.ts"
        if cypress_config.exists() or cypress_config_ts.exists():
            return "cypress"

        return None

    def _analyze_project_structure(self, project_root: Path) -> dict[str, Any]:
        """Analyze project structure for E2E test generation."""
        project_root = Path(project_root)
        analysis: dict[str, Any] = {
            "entry_points": [],
            "main_modules": [],
            "api_endpoints": [],
            "test_directories": [],
        }

        # Find entry points (main.py, app.py, __main__.py, etc.)
        entry_patterns = ["main.py", "app.py", "__main__.py", "server.py", "run.py"]
        for pattern in entry_patterns:
            for entry_file in project_root.rglob(pattern):
                if "test" not in str(entry_file):
                    analysis["entry_points"].append(str(entry_file.relative_to(project_root)))

        # Find main modules (directories with __init__.py)
        for init_file in project_root.rglob("__init__.py"):
            module_dir = init_file.parent
            if "test" not in str(module_dir):
                rel_path = module_dir.relative_to(project_root)
                if str(rel_path) != ".":
                    analysis["main_modules"].append(str(rel_path))

        # Find API endpoints (common patterns)
        api_patterns = ["api", "routes", "endpoints", "controllers"]
        for pattern in api_patterns:
            api_dir = project_root / pattern
            if api_dir.exists() and api_dir.is_dir():
                analysis["api_endpoints"].append(pattern)

        # Find existing test directories
        test_dirs = ["tests", "test", "tests/e2e", "tests/integration"]
        for test_dir in test_dirs:
            test_path = project_root / test_dir
            if test_path.exists() and test_path.is_dir():
                analysis["test_directories"].append(test_dir)

        return analysis

    def _analyze_code(self, code: str, file_path: Path) -> dict[str, Any]:
        """Analyze code structure to extract functions, classes, etc."""
        functions: list[dict[str, Any]] = []
        classes: list[dict[str, Any]] = []
        imports: list[str] = []

        analysis: dict[str, Any] = {
            "file_name": file_path.name,
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "test_framework": self._detect_test_framework(code),
        }

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(
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
                    classes.append({"name": node.name, "methods": methods})
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        imports.extend([alias.name for alias in node.names])
                    else:
                        imports.append(node.module or "")
        except SyntaxError:
            # If code has syntax errors, return basic analysis
            pass

        return analysis

    def _detect_test_framework(self, code: str) -> str:
        """
        Detect which test framework is being used (legacy method).
        
        Note: Use _detect_test_framework_for_language() for language-aware detection.
        """
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

    def _build_e2e_test_prompt(
        self,
        project_root: Path,
        e2e_framework: str,
        project_analysis: dict[str, Any],
        test_path: Path | None,
        context: str | None,
        expert_guidance: str | None = None,
    ) -> str:
        """Build prompt for E2E test generation."""
        prompt_parts = [
            f"Generate comprehensive end-to-end (E2E) tests for this project using {e2e_framework}.",
            "",
            "Project structure:",
        ]

        if project_analysis["entry_points"]:
            prompt_parts.append(
                f"- Entry points: {', '.join(project_analysis['entry_points'][:5])}"
            )
        if project_analysis["main_modules"]:
            prompt_parts.append(
                f"- Main modules: {', '.join(project_analysis['main_modules'][:10])}"
            )
        if project_analysis["api_endpoints"]:
            prompt_parts.append(
                f"- API endpoints: {', '.join(project_analysis['api_endpoints'])}"
            )

        prompt_parts.append("")

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

        # Framework-specific requirements
        framework_requirements = {
            "playwright": [
                "- Use Playwright's page object model pattern",
                "- Test user workflows and interactions",
                "- Include browser automation (navigation, clicks, form fills)",
                "- Test across different browsers if configured",
            ],
            "pytest-playwright": [
                "- Use pytest fixtures for setup/teardown",
                "- Use Playwright's async API",
                "- Test user workflows end-to-end",
                "- Include proper async/await patterns",
            ],
            "selenium": [
                "- Use Selenium WebDriver patterns",
                "- Test user interactions and workflows",
                "- Include proper wait strategies",
                "- Test across different browsers",
            ],
            "cypress": [
                "- Use Cypress commands and patterns",
                "- Test user journeys end-to-end",
                "- Include proper assertions",
                "- Use Cypress best practices",
            ],
        }

        requirements = framework_requirements.get(
            e2e_framework,
            [
                "- Test complete user workflows",
                "- Include setup and teardown",
                "- Test critical paths",
            ],
        )

        prompt_parts.extend(
            [
                "Requirements:",
                *requirements,
                "- Test critical user journeys",
                "- Include error scenarios",
                "- Use descriptive test names",
                "- Ensure tests are deterministic and repeatable",
                "",
                "Generate only the test code (no explanations):",
            ]
        )

        return "\n".join(prompt_parts)
