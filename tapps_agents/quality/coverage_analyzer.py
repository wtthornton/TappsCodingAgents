"""
Coverage Analysis & Reporting Module.

Story 6.3: Coverage Analysis & Reporting
- Calculate line and branch coverage
- Identify missing coverage areas
- Generate coverage reports
- Coverage threshold enforcement
"""

import json
import subprocess  # nosec B404
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from coverage import Coverage

    HAS_COVERAGE = True
except ImportError:
    HAS_COVERAGE = False


@dataclass
class CoverageMetrics:
    """Coverage metrics for a file or module."""

    file_path: str
    total_lines: int
    covered_lines: int
    missing_lines: list[int]
    coverage_percentage: float
    branch_coverage: float | None = None
    statement_coverage: float | None = None


@dataclass
class CoverageReport:
    """Coverage report for a project."""

    total_files: int
    total_lines: int
    covered_lines: int
    missing_lines: int
    coverage_percentage: float
    branch_coverage: float | None = None
    statement_coverage: float | None = None
    files: dict[str, CoverageMetrics] = None
    missing_areas: list[dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.files is None:
            self.files = {}
        if self.missing_areas is None:
            self.missing_areas = []


class CoverageAnalyzer:
    """
    Analyze code coverage and generate reports.

    Story 6.3: Coverage Analysis & Reporting
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize coverage analyzer.

        Args:
            project_root: Root directory of project (default: current directory)
        """
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = Path(project_root).resolve()
        self.has_coverage = HAS_COVERAGE

    def analyze_coverage(
        self,
        coverage_file: Path | None = None,
        source_paths: list[Path] | None = None,
    ) -> CoverageReport:
        """
        Analyze coverage from coverage data file or by running coverage.

        Args:
            coverage_file: Path to coverage.json or .coverage file
            source_paths: Optional source paths to analyze

        Returns:
            CoverageReport with metrics
        """
        # Try to find coverage data
        if coverage_file is None:
            coverage_file = self._find_coverage_file()

        if coverage_file and coverage_file.exists():
            if coverage_file.suffix == ".json":
                return self._parse_coverage_json(coverage_file, source_paths)
            elif coverage_file.name == ".coverage":
                return self._parse_coverage_db(coverage_file, source_paths)

        # If no coverage file found, return empty report
        return CoverageReport(
            total_files=0,
            total_lines=0,
            covered_lines=0,
            missing_lines=0,
            coverage_percentage=0.0,
        )

    def _find_coverage_file(self) -> Path | None:
        """Find coverage file in project root."""
        coverage_files = [
            self.project_root / "coverage.json",
            self.project_root / ".coverage",
            self.project_root / "htmlcov" / "coverage.json",
        ]

        for cov_file in coverage_files:
            if cov_file.exists():
                return cov_file

        return None

    def _parse_coverage_json(
        self, coverage_file: Path, source_paths: list[Path] | None = None
    ) -> CoverageReport:
        """Parse coverage.json file."""
        try:
            with open(coverage_file, encoding="utf-8") as f:
                data = json.load(f)

            # Extract totals
            totals = data.get("totals", {})
            total_lines = totals.get("num_statements", 0)
            covered_lines = totals.get("covered_lines", 0)
            missing_lines = total_lines - covered_lines
            coverage_pct = totals.get("percent_covered", 0.0)

            # Extract branch coverage if available
            branch_coverage = None
            if "percent_covered_branches" in totals:
                branch_coverage = totals["percent_covered_branches"]

            # Extract statement coverage
            statement_coverage = None
            if "percent_covered_statements" in totals:
                statement_coverage = totals["percent_covered_statements"]

            # Parse file-level coverage
            files: dict[str, CoverageMetrics] = {}
            missing_areas: list[dict[str, Any]] = []

            file_data = data.get("files", {})
            for file_path, file_info in file_data.items():
                # Filter by source_paths if provided
                if source_paths:
                    file_path_obj = Path(file_path)
                    if not any(
                        file_path_obj.is_relative_to(src) or file_path_obj == src
                        for src in source_paths
                    ):
                        continue

                summary = file_info.get("summary", {})
                file_total = summary.get("num_statements", 0)
                file_covered = summary.get("covered_lines", 0)
                file_missing = summary.get("missing_lines", [])

                file_coverage_pct = summary.get("percent_covered", 0.0)

                files[file_path] = CoverageMetrics(
                    file_path=file_path,
                    total_lines=file_total,
                    covered_lines=file_covered,
                    missing_lines=file_missing,
                    coverage_percentage=file_coverage_pct,
                    branch_coverage=summary.get("percent_covered_branches"),
                    statement_coverage=summary.get("percent_covered_statements"),
                )

                # Identify missing areas (files with low coverage)
                if file_coverage_pct < 80.0 and file_total > 0:
                    missing_areas.append(
                        {
                            "file": file_path,
                            "coverage": file_coverage_pct,
                            "missing_lines": len(file_missing),
                            "total_lines": file_total,
                        }
                    )

            return CoverageReport(
                total_files=len(files),
                total_lines=total_lines,
                covered_lines=covered_lines,
                missing_lines=missing_lines,
                coverage_percentage=coverage_pct,
                branch_coverage=branch_coverage,
                statement_coverage=statement_coverage,
                files=files,
                missing_areas=missing_areas,
            )

        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            # Return empty report on error
            return CoverageReport(
                total_files=0,
                total_lines=0,
                covered_lines=0,
                missing_lines=0,
                coverage_percentage=0.0,
            )

    def _parse_coverage_db(
        self, coverage_file: Path, source_paths: list[Path] | None = None
    ) -> CoverageReport:
        """Parse .coverage database file."""
        if not self.has_coverage:
            return CoverageReport(
                total_files=0,
                total_lines=0,
                covered_lines=0,
                missing_lines=0,
                coverage_percentage=0.0,
            )

        try:
            cov = Coverage()
            cov.load()

            # Get coverage data
            data = cov.get_data()

            # Calculate totals
            measured_files = data.measured_files()
            if source_paths:
                # Filter files by source_paths
                measured_files = [
                    f
                    for f in measured_files
                    if any(Path(f).is_relative_to(src) or Path(f) == src for src in source_paths)
                ]

            total_lines = 0
            covered_lines = 0
            files: dict[str, CoverageMetrics] = {}
            missing_areas: list[dict[str, Any]] = []

            for file_path in measured_files:
                lines = data.lines(file_path)
                if not lines:
                    continue

                # Count executable lines (simplified)
                file_total = len(lines)
                file_covered = len([l for l in lines if data.line_data(file_path, l)])

                total_lines += file_total
                covered_lines += file_covered

                file_missing = [l for l in lines if not data.line_data(file_path, l)]
                file_coverage_pct = (file_covered / file_total * 100.0) if file_total > 0 else 0.0

                files[file_path] = CoverageMetrics(
                    file_path=file_path,
                    total_lines=file_total,
                    covered_lines=file_covered,
                    missing_lines=file_missing,
                    coverage_percentage=file_coverage_pct,
                )

                # Identify missing areas
                if file_coverage_pct < 80.0 and file_total > 0:
                    missing_areas.append(
                        {
                            "file": file_path,
                            "coverage": file_coverage_pct,
                            "missing_lines": len(file_missing),
                            "total_lines": file_total,
                        }
                    )

            coverage_pct = (covered_lines / total_lines * 100.0) if total_lines > 0 else 0.0

            return CoverageReport(
                total_files=len(files),
                total_lines=total_lines,
                covered_lines=covered_lines,
                missing_lines=total_lines - covered_lines,
                coverage_percentage=coverage_pct,
                files=files,
                missing_areas=missing_areas,
            )

        except Exception:
            # Return empty report on error
            return CoverageReport(
                total_files=0,
                total_lines=0,
                covered_lines=0,
                missing_lines=0,
                coverage_percentage=0.0,
            )

    def check_threshold(
        self, report: CoverageReport, threshold: float = 80.0
    ) -> dict[str, Any]:
        """
        Check if coverage meets threshold.

        Args:
            report: CoverageReport to check
            threshold: Minimum coverage percentage (default: 80.0)

        Returns:
            Dictionary with threshold check results
        """
        passed = report.coverage_percentage >= threshold

        return {
            "passed": passed,
            "coverage": report.coverage_percentage,
            "threshold": threshold,
            "message": (
                f"Coverage {report.coverage_percentage:.2f}% {'meets' if passed else 'below'} threshold of {threshold}%"
            ),
            "missing_areas_count": len(report.missing_areas),
        }

    def generate_report(
        self, report: CoverageReport, output_file: Path | None = None
    ) -> str:
        """
        Generate human-readable coverage report.

        Args:
            report: CoverageReport to format
            output_file: Optional file to write report to

        Returns:
            Formatted report as string
        """
        lines = [
            "Coverage Report",
            "=" * 50,
            "",
            f"Total Files: {report.total_files}",
            f"Total Lines: {report.total_lines}",
            f"Covered Lines: {report.covered_lines}",
            f"Missing Lines: {report.missing_lines}",
            f"Coverage: {report.coverage_percentage:.2f}%",
        ]

        if report.branch_coverage is not None:
            lines.append(f"Branch Coverage: {report.branch_coverage:.2f}%")
        if report.statement_coverage is not None:
            lines.append(f"Statement Coverage: {report.statement_coverage:.2f}%")

        lines.append("")

        # List missing areas
        if report.missing_areas:
            lines.append("Missing Coverage Areas:")
            lines.append("-" * 50)
            for area in sorted(report.missing_areas, key=lambda x: x["coverage"])[:10]:
                lines.append(
                    f"  {area['file']}: {area['coverage']:.2f}% "
                    f"({area['missing_lines']}/{area['total_lines']} lines missing)"
                )

        report_text = "\n".join(lines)

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(report_text, encoding="utf-8")

        return report_text
