"""
External feedback data models for TappsCodingAgents evaluation.

These models define the structure for feedback submitted by external projects
about TappsCodingAgents performance.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FeedbackContext(BaseModel):
    """Optional context information for feedback."""

    workflow_id: str | None = Field(None, description="Workflow identifier")
    agent_id: str | None = Field(None, description="Agent identifier")
    task_type: str | None = Field(None, description="Task type (e.g., 'code-review')")
    timestamp: datetime | None = Field(None, description="Context timestamp")


class FeedbackMetrics(BaseModel):
    """Optional performance metrics."""

    execution_time_seconds: float | None = Field(None, description="Execution time in seconds")
    quality_score: float | None = Field(None, description="Quality score")
    code_lines_processed: int | None = Field(None, description="Lines of code processed")
    additional: dict[str, Any] | None = Field(None, description="Additional metrics")


class ExternalFeedbackData(BaseModel):
    """External feedback data model for TappsCodingAgents evaluation."""

    feedback_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique feedback identifier (UUID)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Feedback submission timestamp",
    )
    performance_ratings: dict[str, float] = Field(
        ...,
        min_length=1,
        description="Performance ratings (metric name -> rating, typically 1.0-10.0)",
    )
    suggestions: list[str] = Field(
        ...,
        min_length=1,
        description="List of improvement suggestions",
    )
    context: FeedbackContext | None = Field(None, description="Optional context information")
    metrics: FeedbackMetrics | None = Field(None, description="Optional performance metrics")
    project_id: str | None = Field(None, description="Optional project identifier")

    @field_validator("performance_ratings")
    @classmethod
    def validate_ratings(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate rating values are in reasonable range."""
        for key, value in v.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"Rating '{key}' must be numeric, got {type(value).__name__}")
            if value < 0.0 or value > 10.0:
                raise ValueError(f"Rating '{key}' must be between 0.0 and 10.0, got {value}")
        return v

    @field_validator("suggestions")
    @classmethod
    def validate_suggestions(cls, v: list[str]) -> list[str]:
        """Validate suggestions are non-empty strings."""
        if not v:
            raise ValueError("At least one suggestion is required")
        for suggestion in v:
            if not isinstance(suggestion, str) or not suggestion.strip():
                raise ValueError("Suggestions must be non-empty strings")
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = self.model_dump(mode="json")
        # Ensure timestamp is ISO format string
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExternalFeedbackData":
        """Create from dictionary (handles timestamp conversion)."""
        # Convert timestamp string to datetime if needed
        if "timestamp" in data and isinstance(data["timestamp"], str):
            try:
                data["timestamp"] = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
            except ValueError:
                # Fallback: use current time
                data["timestamp"] = datetime.now(UTC)
        return cls(**data)

    model_config = ConfigDict(
        # JSON serialization handled by to_dict() method
    )
