"""
Coverage Analysis Integration

Analyzes coverage.json files to identify gaps and generate targeted tests.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CoverageGap:
    """Represents a coverage gap in the codebase."""

    file_path: str
    line_number: int | None = None
    function_name: str | None = None
    class_name: str | None = None
    branch: bool = False
    priority: int = 5  # 1-10, 10 is highest priority
    gap_type: str = "line"  # line, branch, function, class
    context: str | None = None  # Surrounding code context


@dataclass
class CoverageReport:
    """Coverage report with gap analysis."""

    total_lines: int = 0
    covered_lines: int = 0
    total_branches: int = 0
    covered_branches: int = 0
    total_functions: int = 0
    covered_functions: int = 0
    coverage_percentage: float = 0.0
    branch_coverage_percentage: float = 0.0
    function_coverage_percentage: float = 0.0
    gaps: list[CoverageGap] = field(default_factory=list)
    files: dict[str, dict[str, Any]] = field(default_factory=dict)


class CoverageAnalyzer:
    """
    Analyzes coverage.json files to identify gaps and prioritize test generation.

    Supports coverage.py JSON format.
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize coverage analyzer.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path.cwd()

    def analyze_coverage(
        self, coverage_file: Path | str, target_coverage: float = 80.0
    ) -> CoverageReport:
        """
        Analyze coverage.json file and identify gaps.

        Args:
            coverage_file: Path to coverage.json file
            target_coverage: Target coverage percentage (default: 80%)

        Returns:
            CoverageReport with gaps identified and prioritized
        """
        coverage_path = Path(coverage_file)
        if not coverage_path.is_absolute():
            coverage_path = self.project_root / coverage_path

        if not coverage_path.exists():
            raise FileNotFoundError(f"Coverage file not found: {coverage_path}")

        # Parse coverage.json (coverage.py format)
        with coverage_path.open(encoding="utf-8") as f:
            coverage_data = json.load(f)

        report = CoverageReport()

        # Extract coverage data
        files = coverage_data.get("files", {})
        report.files = files

        # Calculate totals
        total_lines = 0
        covered_lines = 0
        total_branches = 0
        covered_branches = 0
        total_functions = 0
        covered_functions = 0

        gaps: list[CoverageGap] = []

        for file_path, file_data in files.items():
            # Normalize file path
            if not Path(file_path).is_absolute():
                file_path = str(self.project_root / file_path)

            # Extract line coverage
            executed_lines = file_data.get("executed_lines", [])
            missing_lines = file_data.get("missing_lines", [])
            excluded_lines = file_data.get("excluded_lines", [])

            total_file_lines = len(executed_lines) + len(missing_lines)
            covered_file_lines = len(executed_lines)

            total_lines += total_file_lines
            covered_lines += covered_file_lines

            # Extract branch coverage
            summary = file_data.get("summary", {})
            branch_data = file_data.get("branches", {})
            if branch_data:
                total_file_branches = summary.get("num_branches", 0)
                covered_file_branches = summary.get("covered_branches", 0)
                total_branches += total_file_branches
                covered_branches += covered_file_branches

                # Identify uncovered branches
                for branch_id, branch_info in branch_data.items():
                    if not branch_info.get("covered", False):
                        gaps.append(
                            CoverageGap(
                                file_path=file_path,
                                branch=True,
                                priority=self._calculate_priority(
                                    file_path, branch=True
                                ),
                                gap_type="branch",
                                context=branch_info.get("context"),
                            )
                        )

            # Extract function coverage
            functions = file_data.get("functions", {})
            if functions:
                for func_name, func_info in functions.items():
                    total_functions += 1
                    if func_info.get("executed", False):
                        covered_functions += 1
                    else:
                        # Uncovered function
                        gaps.append(
                            CoverageGap(
                                file_path=file_path,
                                function_name=func_name,
                                priority=self._calculate_priority(
                                    file_path, function_name=func_name
                                ),
                                gap_type="function",
                                context=func_info.get("context"),
                            )
                        )

            # Identify uncovered lines
            for line_num in missing_lines:
                # Get context if available
                context = None
                if "line_contexts" in file_data:
                    context = file_data["line_contexts"].get(str(line_num))

                gaps.append(
                    CoverageGap(
                        file_path=file_path,
                        line_number=line_num,
                        priority=self._calculate_priority(file_path, line_num=line_num),
                        gap_type="line",
                        context=context,
                    )
                )

        # Calculate percentages
        report.total_lines = total_lines
        report.covered_lines = covered_lines
        report.total_branches = total_branches
        report.covered_branches = covered_branches
        report.total_functions = total_functions
        report.covered_functions = covered_functions

        if total_lines > 0:
            report.coverage_percentage = (covered_lines / total_lines) * 100.0
        if total_branches > 0:
            report.branch_coverage_percentage = (
                covered_branches / total_branches
            ) * 100.0
        if total_functions > 0:
            report.function_coverage_percentage = (
                covered_functions / total_functions
            ) * 100.0

        # Prioritize gaps
        report.gaps = self.prioritize_gaps(gaps, target_coverage)

        logger.info(
            f"Coverage analysis complete: {report.coverage_percentage:.1f}% "
            f"({covered_lines}/{total_lines} lines, {len(gaps)} gaps identified)"
        )

        return report

    def identify_gaps(
        self, report: CoverageReport, target: float = 80.0
    ) -> list[CoverageGap]:
        """
        Identify gaps that need to be addressed to reach target coverage.

        Args:
            report: Coverage report
            target: Target coverage percentage

        Returns:
            List of gaps prioritized by importance
        """
        if report.coverage_percentage >= target:
            return []

        # Filter gaps that would help reach target
        target_lines = int((target / 100.0) * report.total_lines)
        needed_lines = target_lines - report.covered_lines

        # Prioritize gaps
        prioritized = self.prioritize_gaps(report.gaps, target)

        # Return gaps that would help reach target
        result: list[CoverageGap] = []
        lines_to_cover = needed_lines

        for gap in prioritized:
            if gap.gap_type == "line" and gap.line_number:
                result.append(gap)
                lines_to_cover -= 1
                if lines_to_cover <= 0:
                    break
            elif gap.gap_type == "function":
                # Functions typically cover multiple lines
                result.append(gap)
                lines_to_cover -= 5  # Estimate
                if lines_to_cover <= 0:
                    break

        return result

    def prioritize_gaps(
        self, gaps: list[CoverageGap], target_coverage: float = 80.0
    ) -> list[CoverageGap]:
        """
        Prioritize coverage gaps for test generation.

        Priority factors:
        - Critical paths (error handling, edge cases)
        - High-traffic code (frequently called functions)
        - Public APIs (functions/classes used by other modules)
        - Test files (should have high coverage)

        Args:
            gaps: List of coverage gaps
            target_coverage: Target coverage percentage

        Returns:
            Prioritized list of gaps (highest priority first)
        """
        # Score each gap
        scored_gaps = []
        for gap in gaps:
            score = gap.priority

            # Boost priority for error handling
            if gap.context:
                context_lower = gap.context.lower()
                if any(
                    keyword in context_lower
                    for keyword in ["error", "exception", "raise", "except"]
                ):
                    score += 3

            # Boost priority for public APIs
            if gap.function_name and not gap.function_name.startswith("_"):
                score += 2

            # Boost priority for test files
            if "test" in gap.file_path.lower():
                score += 5

            # Boost priority for critical modules
            critical_modules = ["auth", "security", "payment", "database", "api"]
            if any(module in gap.file_path.lower() for module in critical_modules):
                score += 2

            scored_gaps.append((score, gap))

        # Sort by score (highest first)
        scored_gaps.sort(key=lambda x: x[0], reverse=True)

        # Update priorities and return
        result = []
        for score, gap in scored_gaps:
            gap.priority = min(score, 10)  # Cap at 10
            result.append(gap)

        return result

    def _calculate_priority(
        self,
        file_path: str,
        line_num: int | None = None,
        function_name: str | None = None,
        branch: bool = False,
    ) -> int:
        """
        Calculate priority for a coverage gap.

        Args:
            file_path: Path to file
            line_num: Line number (if applicable)
            function_name: Function name (if applicable)
            branch: Whether this is a branch gap

        Returns:
            Priority score (1-10)
        """
        priority = 5  # Default

        # Higher priority for source files (not tests)
        if "test" not in file_path.lower():
            priority += 1

        # Higher priority for main modules
        if "main" in file_path.lower() or "__init__" in file_path:
            priority += 1

        # Higher priority for public functions
        if function_name and not function_name.startswith("_"):
            priority += 1

        # Higher priority for branches (edge cases)
        if branch:
            priority += 1

        return min(priority, 10)
