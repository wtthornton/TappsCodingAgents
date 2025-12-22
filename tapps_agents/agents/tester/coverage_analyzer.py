"""
Coverage Analyzer - Language-aware test coverage measurement

Phase 2.1: Test Generation Integration

Note: This module performs tool operations (running pytest, jest, coverage.py) and is
Cursor-first compatible. Tool operations work in both Cursor and headless modes.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess  # nosec B404
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...core.language_detector import Language
from ...core.subprocess_utils import wrap_windows_cmd_shim


@dataclass
class CoverageResult:
    """Test coverage measurement result."""

    coverage_percentage: float  # 0.0-100.0
    language: Language
    framework: str
    lines_covered: int | None = None
    lines_total: int | None = None
    branches_covered: int | None = None
    branches_total: int | None = None
    error: str | None = None


class CoverageAnalyzer:
    """
    Analyzes test coverage for different languages and test frameworks.
    
    Supports:
    - Python: pytest + coverage.py
    - TypeScript/React: jest/vitest with --coverage
    - JavaScript: jest/vitest with --coverage
    """

    async def measure_coverage(
        self,
        file_path: Path,
        language: Language,
        test_file_path: Path | None = None,
        project_root: Path | None = None,
    ) -> CoverageResult:
        """
        Measure test coverage for a file using language-specific tools.
        
        Args:
            file_path: Path to the source file
            language: Detected language
            test_file_path: Optional path to test file
            project_root: Optional project root directory
            
        Returns:
            CoverageResult with coverage percentage and metrics
        """
        if project_root is None:
            project_root = file_path.parent

        # Route to language-specific coverage measurement
        if language == Language.PYTHON:
            return await self._measure_python_coverage(
                file_path, test_file_path, project_root
            )
        elif language in [Language.TYPESCRIPT, Language.JAVASCRIPT, Language.REACT]:
            return await self._measure_typescript_coverage(
                file_path, test_file_path, project_root, language
            )
        else:
            # Unsupported language - return neutral result
            return CoverageResult(
                coverage_percentage=0.0,
                language=language,
                framework="unknown",
                error=f"Coverage measurement not supported for language: {language.value}",
            )

    async def _measure_python_coverage(
        self,
        file_path: Path,
        test_file_path: Path | None,
        project_root: Path,
    ) -> CoverageResult:
        """
        Measure Python test coverage using pytest + coverage.py.
        
        Args:
            file_path: Path to Python source file
            test_file_path: Optional path to test file
            project_root: Project root directory
            
        Returns:
            CoverageResult with coverage metrics
        """
        # Check if coverage.py is available
        coverage_available = shutil.which("coverage") is not None
        pytest_available = shutil.which("pytest") is not None

        if not pytest_available:
            return CoverageResult(
                coverage_percentage=0.0,
                language=Language.PYTHON,
                framework="pytest",
                error="pytest not found. Install with: pip install pytest",
            )

        # Determine test file to run
        if test_file_path and test_file_path.exists():
            test_target = str(test_file_path)
        else:
            # Try to find corresponding test file
            test_target = self._find_python_test_file(file_path, project_root)
            if not test_target:
                return CoverageResult(
                    coverage_percentage=0.0,
                    language=Language.PYTHON,
                    framework="pytest",
                    error=f"No test file found for {file_path.name}",
                )

        try:
            if coverage_available:
                # Use coverage.py for accurate measurement
                cmd = [
                    "coverage",
                    "run",
                    "--source",
                    str(file_path.parent),
                    "-m",
                    "pytest",
                    test_target,
                    "-v",
                ]
            else:
                # Fallback to pytest-cov if available
                cmd = [
                    "pytest",
                    test_target,
                    "--cov",
                    str(file_path.parent),
                    "--cov-report=json",
                    "-v",
                ]

            # Run coverage measurement asynchronously
            process = await asyncio.create_subprocess_exec(
                *wrap_windows_cmd_shim(cmd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(project_root),
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="ignore") if stderr else "Unknown error"
                return CoverageResult(
                    coverage_percentage=0.0,
                    language=Language.PYTHON,
                    framework="pytest",
                    error=f"Test execution failed: {error_msg[:200]}",
                )

            # Parse coverage results
            if coverage_available:
                # Read coverage.json generated by coverage.py
                coverage_json_path = project_root / "coverage.json"
                if not coverage_json_path.exists():
                    # Generate coverage report
                    report_process = await asyncio.create_subprocess_exec(
                        *wrap_windows_cmd_shim(["coverage", "json"]),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=str(project_root),
                    )
                    await asyncio.wait_for(report_process.communicate(), timeout=10)

                if coverage_json_path.exists():
                    with open(coverage_json_path, encoding="utf-8") as f:
                        coverage_data = json.load(f)

                    # Extract coverage for specific file
                    file_path_str = str(file_path.relative_to(project_root))
                    totals = coverage_data.get("totals", {})
                    coverage_percent = totals.get("percent_covered", 0.0)

                    return CoverageResult(
                        coverage_percentage=coverage_percent,
                        language=Language.PYTHON,
                        framework="pytest",
                        lines_covered=totals.get("covered_lines"),
                        lines_total=totals.get("num_statements"),
                        branches_covered=totals.get("covered_branches"),
                        branches_total=totals.get("num_branches"),
                    )
            else:
                # Try to parse pytest-cov JSON output
                coverage_json_path = project_root / "coverage.json"
                if coverage_json_path.exists():
                    with open(coverage_json_path, encoding="utf-8") as f:
                        coverage_data = json.load(f)

                    totals = coverage_data.get("totals", {})
                    coverage_percent = totals.get("percent_covered", 0.0)

                    return CoverageResult(
                        coverage_percentage=coverage_percent,
                        language=Language.PYTHON,
                        framework="pytest",
                        lines_covered=totals.get("covered_lines"),
                        lines_total=totals.get("num_statements"),
                    )

            # Fallback: parse stdout for coverage percentage
            stdout_text = stdout.decode("utf-8", errors="ignore") if stdout else ""
            coverage_match = self._parse_coverage_from_output(stdout_text)
            if coverage_match:
                return CoverageResult(
                    coverage_percentage=coverage_match,
                    language=Language.PYTHON,
                    framework="pytest",
                )

            return CoverageResult(
                coverage_percentage=0.0,
                language=Language.PYTHON,
                framework="pytest",
                error="Could not parse coverage results",
            )

        except asyncio.TimeoutError:
            return CoverageResult(
                coverage_percentage=0.0,
                language=Language.PYTHON,
                framework="pytest",
                error="Coverage measurement timed out",
            )
        except Exception as e:
            return CoverageResult(
                coverage_percentage=0.0,
                language=Language.PYTHON,
                framework="pytest",
                error=f"Coverage measurement failed: {str(e)}",
            )

    async def _measure_typescript_coverage(
        self,
        file_path: Path,
        test_file_path: Path | None,
        project_root: Path,
        language: Language,
    ) -> CoverageResult:
        """
        Measure TypeScript/React/JavaScript test coverage using jest or vitest.
        
        Args:
            file_path: Path to source file
            test_file_path: Optional path to test file
            project_root: Project root directory
            language: Language (TYPESCRIPT, JAVASCRIPT, or REACT)
            
        Returns:
            CoverageResult with coverage metrics
        """
        # Detect test framework (jest or vitest)
        framework = self._detect_typescript_test_framework(project_root)

        if framework == "jest":
            return await self._measure_jest_coverage(
                file_path, test_file_path, project_root, language
            )
        elif framework == "vitest":
            return await self._measure_vitest_coverage(
                file_path, test_file_path, project_root, language
            )
        else:
            return CoverageResult(
                coverage_percentage=0.0,
                language=language,
                framework="unknown",
                error=f"Test framework not detected. Install jest or vitest.",
            )

    async def _measure_jest_coverage(
        self,
        file_path: Path,
        test_file_path: Path | None,
        project_root: Path,
        language: Language,
    ) -> CoverageResult:
        """Measure coverage using Jest."""
        # Check if jest is available
        jest_available = shutil.which("jest") is not None
        npx_available = shutil.which("npx") is not None

        if not jest_available and not npx_available:
            return CoverageResult(
                coverage_percentage=0.0,
                language=language,
                framework="jest",
                error="jest not found. Install with: npm install --save-dev jest",
            )

        try:
            # Use npx jest if jest not directly available
            cmd = ["npx", "jest", "--coverage", "--coverageReporters=json"] if not jest_available else [
                "jest",
                "--coverage",
                "--coverageReporters=json",
            ]

            # Add specific file if test_file_path provided
            if test_file_path and test_file_path.exists():
                cmd.append(str(test_file_path.relative_to(project_root)))
            elif test_file_path:
                # Try to find corresponding test file
                test_target = self._find_typescript_test_file(file_path, project_root)
                if test_target:
                    cmd.append(test_target)

            # Run jest coverage
            process = await asyncio.create_subprocess_exec(
                *wrap_windows_cmd_shim(cmd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(project_root),
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="ignore") if stderr else "Unknown error"
                return CoverageResult(
                    coverage_percentage=0.0,
                    language=language,
                    framework="jest",
                    error=f"Jest execution failed: {error_msg[:200]}",
                )

            # Parse coverage.json
            coverage_json_path = project_root / "coverage" / "coverage-final.json"
            if not coverage_json_path.exists():
                # Try alternative location
                coverage_json_path = project_root / "coverage-final.json"

            if coverage_json_path.exists():
                with open(coverage_json_path, encoding="utf-8") as f:
                    coverage_data = json.load(f)

                # Calculate overall coverage from all files
                total_statements = 0
                covered_statements = 0

                for file_data in coverage_data.values():
                    s = file_data.get("s", {})  # Statements
                    statement_map = file_data.get("statementMap", {})
                    total_statements += len(statement_map)
                    covered_statements += sum(1 for v in s.values() if v > 0)

                coverage_percent = (
                    (covered_statements / total_statements * 100)
                    if total_statements > 0
                    else 0.0
                )

                return CoverageResult(
                    coverage_percentage=coverage_percent,
                    language=language,
                    framework="jest",
                    lines_covered=covered_statements,
                    lines_total=total_statements,
                )

            # Fallback: parse stdout
            stdout_text = stdout.decode("utf-8", errors="ignore") if stdout else ""
            coverage_match = self._parse_coverage_from_output(stdout_text)
            if coverage_match:
                return CoverageResult(
                    coverage_percentage=coverage_match,
                    language=language,
                    framework="jest",
                )

            return CoverageResult(
                coverage_percentage=0.0,
                language=language,
                framework="jest",
                error="Could not parse Jest coverage results",
            )

        except asyncio.TimeoutError:
            return CoverageResult(
                coverage_percentage=0.0,
                language=language,
                framework="jest",
                error="Jest coverage measurement timed out",
            )
        except Exception as e:
            return CoverageResult(
                coverage_percentage=0.0,
                language=language,
                framework="jest",
                error=f"Jest coverage measurement failed: {str(e)}",
            )

    async def _measure_vitest_coverage(
        self,
        file_path: Path,
        test_file_path: Path | None,
        project_root: Path,
        language: Language,
    ) -> CoverageResult:
        """Measure coverage using Vitest (similar to Jest)."""
        # Vitest uses similar coverage format to Jest
        # This is a simplified implementation
        return await self._measure_jest_coverage(
            file_path, test_file_path, project_root, language
        )

    def _detect_typescript_test_framework(self, project_root: Path) -> str:
        """Detect which test framework is being used (jest or vitest)."""
        package_json = project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json, encoding="utf-8") as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    if "vitest" in deps:
                        return "vitest"
                    if "jest" in deps:
                        return "jest"
            except Exception:
                pass

        # Check for config files
        if (project_root / "vitest.config.ts").exists() or (project_root / "vitest.config.js").exists():
            return "vitest"
        if (project_root / "jest.config.js").exists() or (project_root / "jest.config.ts").exists():
            return "jest"

        return "jest"  # Default

    def _find_python_test_file(self, file_path: Path, project_root: Path) -> str | None:
        """Find corresponding test file for Python source file."""
        file_stem = file_path.stem
        file_dir = file_path.parent

        # Common test file patterns
        test_patterns = [
            f"test_{file_stem}.py",
            f"{file_stem}_test.py",
            f"test_{file_stem}.py",
        ]

        # Look in same directory
        for pattern in test_patterns:
            test_file = file_dir / pattern
            if test_file.exists():
                return str(test_file.relative_to(project_root))

        # Look in tests/ directory
        tests_dir = project_root / "tests"
        if tests_dir.exists():
            for pattern in test_patterns:
                test_file = tests_dir / pattern
                if test_file.exists():
                    return str(test_file.relative_to(project_root))

        return None

    def _find_typescript_test_file(
        self, file_path: Path, project_root: Path
    ) -> str | None:
        """Find corresponding test file for TypeScript/JavaScript source file."""
        file_stem = file_path.stem
        file_dir = file_path.parent

        # Common test file patterns
        test_patterns = [
            f"{file_stem}.test.ts",
            f"{file_stem}.test.tsx",
            f"{file_stem}.test.js",
            f"{file_stem}.test.jsx",
            f"{file_stem}.spec.ts",
            f"{file_stem}.spec.tsx",
            f"{file_stem}.spec.js",
            f"{file_stem}.spec.jsx",
        ]

        # Look in same directory
        for pattern in test_patterns:
            test_file = file_dir / pattern
            if test_file.exists():
                return str(test_file.relative_to(project_root))

        # Look in __tests__ directory
        tests_dir = file_dir / "__tests__"
        if tests_dir.exists():
            for pattern in test_patterns:
                test_file = tests_dir / pattern
                if test_file.exists():
                    return str(test_file.relative_to(project_root))

        return None

    def _parse_coverage_from_output(self, output: str) -> float | None:
        """Parse coverage percentage from command output."""
        import re

        # Common patterns for coverage output
        patterns = [
            r"TOTAL\s+.*?\s+(\d+(?:\.\d+)?)%",  # Jest/Vitest style
            r"coverage:\s+.*?(\d+(?:\.\d+)?)%",  # Generic
            r"(\d+(?:\.\d+)?)%\s+coverage",  # Reverse order
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

