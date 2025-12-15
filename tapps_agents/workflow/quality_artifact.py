"""
Quality Analysis Artifact Schema.

Defines versioned JSON schema for quality analysis results from Background Agents.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ToolResult:
    """Result from a single quality tool (Ruff, mypy, etc.)."""

    tool_name: str
    available: bool
    status: str  # "success", "error", "unavailable", "timeout"
    issues: list[dict[str, Any]] = field(default_factory=list)
    issue_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    error_message: str | None = None
    execution_time_seconds: float | None = None


@dataclass
class QualityArtifact:
    """
    Versioned quality analysis artifact.

    Schema version: 1.0
    """

    schema_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # "pending", "running", "completed", "failed", "cancelled", "timeout"
    worktree_path: str | None = None
    correlation_id: str | None = None

    # Tool results
    tools: dict[str, ToolResult] = field(default_factory=dict)

    # Aggregated scores
    scores: dict[str, float] = field(default_factory=dict)  # e.g., {"linting": 8.5, "type_checking": 9.0}

    # Summary
    total_issues: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    overall_score: float | None = None

    # Error information
    error: str | None = None
    cancelled: bool = False
    timeout: bool = False

    # Metadata
    execution_time_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert ToolResult objects to dicts
        data["tools"] = {
            name: asdict(tool) for name, tool in self.tools.items()
        }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QualityArtifact:
        """Create from dictionary."""
        # Convert tool dicts back to ToolResult objects
        tools = {}
        if "tools" in data:
            for name, tool_data in data["tools"].items():
                tools[name] = ToolResult(**tool_data)
        data["tools"] = tools
        return cls(**data)

    def add_tool_result(self, tool_name: str, result: ToolResult) -> None:
        """Add a tool result."""
        self.tools[tool_name] = result
        # Update aggregated counts
        self.total_issues += result.issue_count
        self.total_errors += result.error_count
        self.total_warnings += result.warning_count

    def mark_completed(self) -> None:
        """Mark analysis as completed."""
        self.status = "completed"
        # Calculate overall score if not set
        if self.overall_score is None and self.scores:
            # Simple average of all scores
            self.overall_score = sum(self.scores.values()) / len(self.scores)

    def mark_failed(self, error: str) -> None:
        """Mark analysis as failed."""
        self.status = "failed"
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark analysis as cancelled."""
        self.status = "cancelled"
        self.cancelled = True

    def mark_timeout(self) -> None:
        """Mark analysis as timed out."""
        self.status = "timeout"
        self.timeout = True
