"""
Quality Analysis Artifact Schema.

Defines versioned JSON schema for quality analysis results from Background Agents.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common_enums import ArtifactStatus
from .metadata_models import ArtifactMetadata


class ToolResult(BaseModel):
    """Result from a single quality tool (Ruff, mypy, etc.)."""

    tool_name: str
    available: bool
    status: str  # "success", "error", "unavailable", "timeout"
    issues: list[dict[str, Any]] = Field(default_factory=list)
    issue_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    error_message: str | None = None
    execution_time_seconds: float | None = None

    model_config = {"extra": "forbid"}


class QualityArtifact(BaseModel):
    """
    Versioned quality analysis artifact.

    Schema version: 1.0
    Migrated to Pydantic BaseModel for runtime validation and type safety.
    """

    schema_version: str = "1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: ArtifactStatus = ArtifactStatus.PENDING
    worktree_path: str | None = None
    correlation_id: str | None = None

    # Tool results
    tools: dict[str, ToolResult] = Field(default_factory=dict)

    # Aggregated scores
    scores: dict[str, float] = Field(default_factory=dict)  # e.g., {"linting": 8.5, "type_checking": 9.0}

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
    metadata: ArtifactMetadata = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    def add_tool_result(self, tool_name: str, result: ToolResult) -> None:
        """Add a tool result."""
        self.tools[tool_name] = result
        # Update aggregated counts
        self.total_issues += result.issue_count
        self.total_errors += result.error_count
        self.total_warnings += result.warning_count

    def mark_completed(self) -> None:
        """Mark analysis as completed."""
        self.status = ArtifactStatus.COMPLETED
        # Calculate overall score if not set
        if self.overall_score is None and self.scores:
            # Simple average of all scores
            self.overall_score = sum(self.scores.values()) / len(self.scores)

    def mark_failed(self, error: str) -> None:
        """Mark analysis as failed."""
        self.status = ArtifactStatus.FAILED
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark analysis as cancelled."""
        self.status = ArtifactStatus.CANCELLED
        self.cancelled = True

    def mark_timeout(self) -> None:
        """Mark analysis as timed out."""
        self.status = ArtifactStatus.TIMEOUT
        self.timeout = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QualityArtifact:
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
    def _from_dict_legacy(cls, data: dict[str, Any]) -> QualityArtifact:
        """Convert from legacy dataclass format."""
        # Convert tools from dict of dicts to dict of ToolResult objects
        tools = {}
        if "tools" in data:
            for name, tool_data in data["tools"].items():
                if isinstance(tool_data, dict):
                    tools[name] = ToolResult(**tool_data)
                else:
                    tools[name] = tool_data

        # Convert status string to enum
        status = ArtifactStatus.PENDING
        if data.get("status"):
            try:
                status = ArtifactStatus(data["status"].lower())
            except ValueError:
                pass

        # Build new artifact
        artifact_data = data.copy()
        artifact_data["tools"] = tools
        artifact_data["status"] = status

        # Remove methods that might cause issues
        artifact_data.pop("to_dict", None)
        artifact_data.pop("from_dict", None)
        artifact_data.pop("add_tool_result", None)
        artifact_data.pop("mark_completed", None)
        artifact_data.pop("mark_failed", None)
        artifact_data.pop("mark_cancelled", None)
        artifact_data.pop("mark_timeout", None)

        return cls(**artifact_data)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary (backward compatibility method).

        For new code, use model_dump(mode="json") instead.
        """
        return self.model_dump(mode="json", exclude_none=False)
