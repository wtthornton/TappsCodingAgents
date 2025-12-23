"""
Coverage-Driven Test Generator

Generates tests targeting specific uncovered code paths identified by coverage analysis.
"""

import logging
from pathlib import Path
from typing import Any

from .coverage_analyzer import CoverageAnalyzer, CoverageGap, CoverageReport
from .test_generator import TestGenerator

logger = logging.getLogger(__name__)


class CoverageTestGenerator:
    """
    Generates tests targeting specific uncovered code paths.

    Uses coverage analysis to identify gaps and generate targeted tests.
    """

    def __init__(
        self,
        project_root: Path | None = None,
        test_generator: TestGenerator | None = None,
    ):
        """
        Initialize coverage test generator.

        Args:
            project_root: Root directory of the project
            test_generator: Optional TestGenerator instance (created if None)
        """
        self.project_root = project_root or Path.cwd()
        self.coverage_analyzer = CoverageAnalyzer(project_root=self.project_root)
        self.test_generator = test_generator or TestGenerator(
            project_root=self.project_root
        )

    async def generate_coverage_tests(
        self,
        coverage_file: Path | str,
        target_coverage: float = 80.0,
        focus_uncovered: bool = True,
        module: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate tests targeting uncovered code paths.

        Args:
            coverage_file: Path to coverage.json file
            target_coverage: Target coverage percentage
            focus_uncovered: Whether to focus only on uncovered code
            module: Optional module path to focus on

        Returns:
            Dictionary with generation results
        """
        # Analyze coverage
        report = self.coverage_analyzer.analyze_coverage(
            coverage_file, target_coverage=target_coverage
        )

        # Identify gaps
        if focus_uncovered:
            gaps = self.coverage_analyzer.identify_gaps(report, target=target_coverage)
        else:
            gaps = report.gaps

        # Filter by module if specified
        if module:
            module_path = Path(module)
            if not module_path.is_absolute():
                module_path = self.project_root / module_path
            gaps = [
                gap
                for gap in gaps
                if Path(gap.file_path).is_relative_to(module_path)
                or str(module_path) in gap.file_path
            ]

        # Group gaps by file
        gaps_by_file: dict[str, list[CoverageGap]] = {}
        for gap in gaps:
            if gap.file_path not in gaps_by_file:
                gaps_by_file[gap.file_path] = []
            gaps_by_file[gap.file_path].append(gap)

        # Generate tests for each file
        results: dict[str, Any] = {
            "coverage_before": report.coverage_percentage,
            "target_coverage": target_coverage,
            "gaps_identified": len(gaps),
            "files_with_gaps": len(gaps_by_file),
            "tests_generated": [],
            "errors": [],
        }

        for file_path, file_gaps in gaps_by_file.items():
            try:
                # Generate tests for this file's gaps
                test_result = await self._generate_tests_for_file(
                    file_path, file_gaps, report
                )
                results["tests_generated"].append(test_result)
            except Exception as e:
                logger.error(f"Error generating tests for {file_path}: {e}", exc_info=True)
                results["errors"].append({"file": file_path, "error": str(e)})

        results["total_tests_generated"] = len(results["tests_generated"])

        return results

    async def _generate_tests_for_file(
        self, file_path: str, gaps: list[CoverageGap], report: CoverageReport
    ) -> dict[str, Any]:
        """
        Generate tests for a specific file's coverage gaps.

        Args:
            file_path: Path to source file
            gaps: List of coverage gaps for this file
            report: Full coverage report

        Returns:
            Test generation result
        """
        source_path = Path(file_path)
        if not source_path.is_absolute():
            source_path = self.project_root / source_path

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Read source file to understand context
        source_code = source_path.read_text(encoding="utf-8")

        # Build test specification from gaps
        test_spec = self._build_test_specification(gaps, source_code)

        # Generate test file path
        test_file = self._get_test_file_path(source_path)

        # Use test generator to create tests
        # For now, create a simple test structure
        # In the future, this would use the TestGenerator more intelligently
        test_content = self._generate_test_content(
            source_path, gaps, test_spec, source_code
        )

        # Write test file
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(test_content, encoding="utf-8")

        return {
            "source_file": str(source_path),
            "test_file": str(test_file),
            "gaps_addressed": len(gaps),
            "test_content_length": len(test_content),
        }

    def _build_test_specification(
        self, gaps: list[CoverageGap], source_code: str
    ) -> dict[str, Any]:
        """
        Build test specification from coverage gaps.

        Args:
            gaps: List of coverage gaps
            source_code: Source code content

        Returns:
            Test specification dictionary
        """
        spec: dict[str, Any] = {
            "functions_to_test": [],
            "lines_to_test": [],
            "branches_to_test": [],
            "edge_cases": [],
        }

        for gap in gaps:
            if gap.gap_type == "function" and gap.function_name:
                spec["functions_to_test"].append(gap.function_name)
            elif gap.gap_type == "line" and gap.line_number:
                spec["lines_to_test"].append(gap.line_number)
            elif gap.gap_type == "branch":
                spec["branches_to_test"].append(gap)

            # Identify edge cases from context
            if gap.context:
                if any(
                    keyword in gap.context.lower()
                    for keyword in ["error", "exception", "raise"]
                ):
                    spec["edge_cases"].append("error_handling")

        return spec

    def _get_test_file_path(self, source_path: Path) -> Path:
        """Get test file path for a source file."""
        # Convert src/path/to/file.py -> tests/test_path_to_file.py
        relative_path = source_path.relative_to(self.project_root)

        # Remove 'src' prefix if present
        parts = list(relative_path.parts)
        if parts[0] == "src":
            parts = parts[1:]

        # Create test path
        test_parts = ["tests"] + parts[:-1] + [f"test_{parts[-1]}"]
        return self.project_root / Path(*test_parts)

    def _generate_test_content(
        self,
        source_path: Path,
        gaps: list[CoverageGap],
        test_spec: dict[str, Any],
        source_code: str,
    ) -> str:
        """
        Generate test file content.

        Args:
            source_path: Path to source file
            gaps: Coverage gaps to address
            test_spec: Test specification
            source_code: Source code content

        Returns:
            Test file content
        """
        module_name = source_path.stem
        import_path = str(source_path.relative_to(self.project_root)).replace(
            "/", "."
        ).replace("\\", ".").replace(".py", "")

        lines = [
            '"""',
            f"Tests for {module_name} - Generated to address coverage gaps",
            '"""',
            "",
            "import pytest",
            f"from {import_path} import *",
            "",
        ]

        # Generate tests for uncovered functions
        for func_name in test_spec["functions_to_test"]:
            lines.extend(
                [
                    "",
                    f"def test_{func_name}():",
                    f'    """Test {func_name} function."""',
                    "    # TODO: Implement test based on coverage gap",
                    "    pass",
                ]
            )

        # Generate tests for uncovered lines
        if test_spec["lines_to_test"]:
            lines.extend(
                [
                    "",
                    "def test_uncovered_lines():",
                    '    """Test uncovered lines."""',
                    f"    # Lines to cover: {', '.join(map(str, test_spec['lines_to_test']))}",
                    "    # TODO: Implement tests for these lines",
                    "    pass",
                ]
            )

        # Generate edge case tests
        if test_spec["edge_cases"]:
            for edge_case in test_spec["edge_cases"]:
                if edge_case == "error_handling":
                    lines.extend(
                        [
                            "",
                            "def test_error_handling():",
                            '    """Test error handling paths."""',
                            "    # TODO: Test error conditions",
                            "    pass",
                        ]
                    )

        return "\n".join(lines)

