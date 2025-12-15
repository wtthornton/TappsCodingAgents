"""
Testing Analysis Artifact Schema.

Defines versioned JSON schema for testing results from Background Agents.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TestResult:
    """Result from test execution."""

    test_name: str
    status: str  # "passed", "failed", "skipped", "error"
    duration_seconds: float | None = None
    error_message: str | None = None
    stdout: str | None = None
    stderr: str | None = None


@dataclass
class CoverageSummary:
    """Test coverage summary."""

    total_lines: int = 0
    covered_lines: int = 0
    coverage_percentage: float = 0.0
    missing_lines: list[int] = field(default_factory=list)
    branch_coverage: float | None = None
    statement_coverage: float | None = None


@dataclass
class TestingArtifact:
    """
    Versioned testing analysis artifact.

    Schema version: 1.0
    """

    schema_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # "pending", "running", "completed", "failed", "cancelled", "timeout", "not_run"
    worktree_path: str | None = None
    correlation_id: str | None = None

    # Test execution results
    tests_run: bool = False
    test_framework: str = "pytest"
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    success_rate: float = 0.0

    # Individual test results (optional, for detailed reporting)
    test_results: list[TestResult] = field(default_factory=list)

    # Coverage information
    coverage_enabled: bool = False
    coverage: CoverageSummary | None = None

    # Execution details
    execution_time_seconds: float | None = None
    return_code: int | None = None
    stdout: str | None = None
    stderr: str | None = None

    # Error information
    error: str | None = None
    cancelled: bool = False
    timeout: bool = False
    not_run_reason: str | None = None  # Explanation if tests were not run

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert TestResult and CoverageSummary objects to dicts
        data["test_results"] = [asdict(tr) for tr in self.test_results]
        if self.coverage:
            data["coverage"] = asdict(self.coverage)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TestingArtifact:
        """Create from dictionary."""
        # Convert test result dicts back to TestResult objects
        test_results = []
        if "test_results" in data:
            test_results = [TestResult(**tr) for tr in data["test_results"]]
        data["test_results"] = test_results

        # Convert coverage dict back to CoverageSummary
        if "coverage" in data and data["coverage"]:
            data["coverage"] = CoverageSummary(**data["coverage"])
        else:
            data["coverage"] = None

        return cls(**data)

    def mark_completed(self) -> None:
        """Mark test execution as completed."""
        self.status = "completed"
        self.tests_run = True
        # Calculate success rate
        if self.total_tests > 0:
            self.success_rate = (self.passed_tests / self.total_tests) * 100.0

    def mark_failed(self, error: str) -> None:
        """Mark test execution as failed."""
        self.status = "failed"
        self.error = error
        self.tests_run = True

    def mark_cancelled(self) -> None:
        """Mark test execution as cancelled."""
        self.status = "cancelled"
        self.cancelled = True

    def mark_timeout(self) -> None:
        """Mark test execution as timed out."""
        self.status = "timeout"
        self.timeout = True

    def mark_not_run(self, reason: str) -> None:
        """Mark tests as not run with explanation."""
        self.status = "not_run"
        self.not_run_reason = reason
        self.tests_run = False
