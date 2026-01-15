"""
Issue tracking dataclasses for reviewer agent feedback.

Phase 2 (P0): Added issue tracking for maintainability, performance, and other metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CodeIssue:
    """Base class for code issues."""

    issue_type: str
    message: str
    line_number: int | None = None
    severity: str = "medium"  # low, medium, high
    suggestion: str | None = None


@dataclass
class MaintainabilityIssue(CodeIssue):
    """Maintainability-specific issue."""

    function_name: str | None = None
    class_name: str | None = None
    metric_value: float | None = None  # e.g., function length, nesting depth
    threshold: float | None = None  # e.g., max function length


@dataclass
class PerformanceIssue(CodeIssue):
    """Performance-specific issue."""

    operation_type: str | None = None  # e.g., "loop", "function_call"
    context: str | None = None  # e.g., "nested in for loop"


@dataclass
class TypeCheckingIssue(CodeIssue):
    """Type checking-specific issue."""

    error_code: str | None = None  # e.g., "missing-return-type"
    type_expected: str | None = None
    type_actual: str | None = None


@dataclass
class TestCoverageIssue(CodeIssue):
    """Test coverage-specific issue."""

    coverage_percentage: float | None = None
    uncovered_lines: list[int] | None = None
    test_file_path: str | None = None


@dataclass
class CodeIssues:
    """Container for all code issues found during review."""

    maintainability_issues: list[MaintainabilityIssue] = field(default_factory=list)
    performance_issues: list[PerformanceIssue] = field(default_factory=list)
    type_checking_issues: list[TypeCheckingIssue] = field(default_factory=list)
    test_coverage_issues: list[TestCoverageIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert issues to dictionary format."""
        return {
            "maintainability": [
                {
                    "issue_type": issue.issue_type,
                    "message": issue.message,
                    "line_number": issue.line_number,
                    "severity": issue.severity,
                    "suggestion": issue.suggestion,
                    "function_name": issue.function_name,
                    "class_name": issue.class_name,
                    "metric_value": issue.metric_value,
                    "threshold": issue.threshold,
                }
                for issue in self.maintainability_issues
            ],
            "performance": [
                {
                    "issue_type": issue.issue_type,
                    "message": issue.message,
                    "line_number": issue.line_number,
                    "severity": issue.severity,
                    "suggestion": issue.suggestion,
                    "operation_type": issue.operation_type,
                    "context": issue.context,
                }
                for issue in self.performance_issues
            ],
            "type_checking": [
                {
                    "issue_type": issue.issue_type,
                    "message": issue.message,
                    "line_number": issue.line_number,
                    "severity": issue.severity,
                    "suggestion": issue.suggestion,
                    "error_code": issue.error_code,
                    "type_expected": issue.type_expected,
                    "type_actual": issue.type_actual,
                }
                for issue in self.type_checking_issues
            ],
            "test_coverage": [
                {
                    "issue_type": issue.issue_type,
                    "message": issue.message,
                    "line_number": issue.line_number,
                    "severity": issue.severity,
                    "suggestion": issue.suggestion,
                    "coverage_percentage": issue.coverage_percentage,
                    "uncovered_lines": issue.uncovered_lines,
                    "test_file_path": issue.test_file_path,
                }
                for issue in self.test_coverage_issues
            ],
        }

    def get_summary(self) -> dict[str, Any]:
        """Get summary of issues by category."""
        return {
            "total_issues": (
                len(self.maintainability_issues)
                + len(self.performance_issues)
                + len(self.type_checking_issues)
                + len(self.test_coverage_issues)
            ),
            "maintainability_count": len(self.maintainability_issues),
            "performance_count": len(self.performance_issues),
            "type_checking_count": len(self.type_checking_issues),
            "test_coverage_count": len(self.test_coverage_issues),
            "high_severity": sum(
                1
                for issue in (
                    self.maintainability_issues
                    + self.performance_issues
                    + self.type_checking_issues
                    + self.test_coverage_issues
                )
                if issue.severity == "high"
            ),
            "medium_severity": sum(
                1
                for issue in (
                    self.maintainability_issues
                    + self.performance_issues
                    + self.type_checking_issues
                    + self.test_coverage_issues
                )
                if issue.severity == "medium"
            ),
            "low_severity": sum(
                1
                for issue in (
                    self.maintainability_issues
                    + self.performance_issues
                    + self.type_checking_issues
                    + self.test_coverage_issues
                )
                if issue.severity == "low"
            ),
        }
