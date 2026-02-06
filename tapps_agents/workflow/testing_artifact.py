"""
Testing Analysis Artifact Schema.

Defines versioned JSON schema for testing results from Background Agents.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common_enums import ArtifactStatus
from .metadata_models import ArtifactMetadata


class TestResult(BaseModel):
    """Result from test execution."""

    test_name: str
    status: str  # "passed", "failed", "skipped", "error"
    duration_seconds: float | None = None
    error_message: str | None = None
    stdout: str | None = None
    stderr: str | None = None

    model_config = {"extra": "forbid"}


class CoverageSummary(BaseModel):
    """Test coverage summary."""

    total_lines: int = 0
    covered_lines: int = 0
    coverage_percentage: float = 0.0
    missing_lines: list[int] = Field(default_factory=list)
    branch_coverage: float | None = None
    statement_coverage: float | None = None

    model_config = {"extra": "forbid"}


class TestingArtifact(BaseModel):
    """
    Versioned testing analysis artifact.

    Schema version: 1.0
    Migrated to Pydantic BaseModel for runtime validation and type safety.
    """

    schema_version: str = "1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: ArtifactStatus = ArtifactStatus.PENDING
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
    test_results: list[TestResult] = Field(default_factory=list)

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
    metadata: ArtifactMetadata = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    def mark_completed(self) -> None:
        """Mark test execution as completed."""
        self.status = ArtifactStatus.COMPLETED
        self.tests_run = True
        # Calculate success rate
        if self.total_tests > 0:
            self.success_rate = (self.passed_tests / self.total_tests) * 100.0

    def mark_failed(self, error: str) -> None:
        """Mark test execution as failed."""
        self.status = ArtifactStatus.FAILED
        self.error = error
        self.tests_run = True

    def mark_cancelled(self) -> None:
        """Mark test execution as cancelled."""
        self.status = ArtifactStatus.CANCELLED
        self.cancelled = True

    def mark_timeout(self) -> None:
        """Mark test execution as timed out."""
        self.status = ArtifactStatus.TIMEOUT
        self.timeout = True

    def mark_not_run(self, reason: str) -> None:
        """Mark tests as not run with explanation."""
        self.status = ArtifactStatus.NOT_RUN
        self.not_run_reason = reason
        self.tests_run = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TestingArtifact:
        """
        Create from dictionary (backward compatibility with old dataclass format).

        This method supports both old dataclass format and new Pydantic format.
        """
        # Try Pydantic validation first (new format)
        try:
            return cls.model_validate(data)
        except Exception:
            # Fall back to manual conversion (old dataclass format)
            return cls._from_dict_legacy(data)

    @classmethod
    def _from_dict_legacy(cls, data: dict[str, Any]) -> TestingArtifact:
        """Convert from legacy dataclass format."""
        # Convert test_results from dict to TestResult objects
        test_results = []
        if "test_results" in data:
            for tr_data in data["test_results"]:
                if isinstance(tr_data, dict):
                    test_results.append(TestResult(**tr_data))
                else:
                    test_results.append(tr_data)

        # Convert coverage from dict to CoverageSummary object
        coverage = None
        if data.get("coverage"):
            coverage_data = data["coverage"]
            if isinstance(coverage_data, dict):
                coverage = CoverageSummary(**coverage_data)
            elif isinstance(coverage_data, CoverageSummary):
                coverage = coverage_data

        # Convert status string to enum
        status = ArtifactStatus.PENDING
        if data.get("status"):
            try:
                status = ArtifactStatus(data["status"].lower())
            except ValueError:
                pass

        # Build new artifact
        artifact_data = data.copy()
        artifact_data["test_results"] = test_results
        artifact_data["coverage"] = coverage
        artifact_data["status"] = status

        # Remove methods that might cause issues
        artifact_data.pop("to_dict", None)
        artifact_data.pop("from_dict", None)
        artifact_data.pop("mark_completed", None)
        artifact_data.pop("mark_failed", None)
        artifact_data.pop("mark_cancelled", None)

        return cls(**artifact_data)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary (backward compatibility method).

        For new code, use model_dump(mode="json") instead.
        """
        return self.model_dump(mode="json", exclude_none=False)
