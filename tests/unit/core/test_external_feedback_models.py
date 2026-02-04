"""
Unit tests for external feedback data models.

Tests cover:
- Data model validation
- Rating validation (0.0-10.0 range)
- Suggestion validation (non-empty strings)
- Serialization/deserialization
- Edge cases and error handling
"""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from tapps_agents.core.external_feedback_models import (
    ExternalFeedbackData,
    FeedbackContext,
    FeedbackMetrics,
)

pytestmark = pytest.mark.unit


class TestFeedbackContext:
    """Test FeedbackContext model."""

    def test_feedback_context_all_fields(self):
        """Test FeedbackContext with all fields."""
        context = FeedbackContext(
            workflow_id="workflow-123",
            agent_id="reviewer",
            task_type="code-review",
            timestamp=datetime.now(UTC),
        )
        assert context.workflow_id == "workflow-123"
        assert context.agent_id == "reviewer"
        assert context.task_type == "code-review"
        assert isinstance(context.timestamp, datetime)

    def test_feedback_context_optional_fields(self):
        """Test FeedbackContext with optional fields."""
        context = FeedbackContext()
        assert context.workflow_id is None
        assert context.agent_id is None
        assert context.task_type is None
        assert context.timestamp is None


class TestFeedbackMetrics:
    """Test FeedbackMetrics model."""

    def test_feedback_metrics_all_fields(self):
        """Test FeedbackMetrics with all fields."""
        metrics = FeedbackMetrics(
            execution_time_seconds=45.2,
            quality_score=85.0,
            code_lines_processed=1000,
            additional={"custom_metric": 123},
        )
        assert metrics.execution_time_seconds == 45.2
        assert metrics.quality_score == 85.0
        assert metrics.code_lines_processed == 1000
        assert metrics.additional == {"custom_metric": 123}

    def test_feedback_metrics_optional_fields(self):
        """Test FeedbackMetrics with optional fields."""
        metrics = FeedbackMetrics()
        assert metrics.execution_time_seconds is None
        assert metrics.quality_score is None
        assert metrics.code_lines_processed is None
        assert metrics.additional is None


class TestExternalFeedbackData:
    """Test ExternalFeedbackData model."""

    def test_feedback_data_creation(self):
        """Test creating ExternalFeedbackData with required fields."""
        feedback = ExternalFeedbackData(
            performance_ratings={"overall": 8.5, "usability": 7.0},
            suggestions=["Improve error messages", "Add more examples"],
        )
        assert isinstance(feedback.feedback_id, str)
        assert UUID(feedback.feedback_id)  # Valid UUID
        assert isinstance(feedback.timestamp, datetime)
        assert feedback.performance_ratings == {"overall": 8.5, "usability": 7.0}
        assert feedback.suggestions == ["Improve error messages", "Add more examples"]

    def test_feedback_data_with_all_fields(self):
        """Test ExternalFeedbackData with all fields."""
        context = FeedbackContext(workflow_id="workflow-123", agent_id="reviewer")
        metrics = FeedbackMetrics(execution_time_seconds=45.2, quality_score=85.0)

        feedback = ExternalFeedbackData(
            performance_ratings={"overall": 8.5},
            suggestions=["Great framework!"],
            context=context,
            metrics=metrics,
            project_id="my-project-v1.0",
        )
        assert feedback.context == context
        assert feedback.metrics == metrics
        assert feedback.project_id == "my-project-v1.0"

    def test_feedback_data_rating_validation_valid_range(self):
        """Test rating validation accepts valid range (0.0-10.0)."""
        # Minimum value
        feedback = ExternalFeedbackData(
            performance_ratings={"overall": 0.0}, suggestions=["Test"]
        )
        assert feedback.performance_ratings["overall"] == 0.0

        # Maximum value
        feedback = ExternalFeedbackData(
            performance_ratings={"overall": 10.0}, suggestions=["Test"]
        )
        assert feedback.performance_ratings["overall"] == 10.0

        # Middle value
        feedback = ExternalFeedbackData(
            performance_ratings={"overall": 5.5}, suggestions=["Test"]
        )
        assert feedback.performance_ratings["overall"] == 5.5

    def test_feedback_data_rating_validation_below_range(self):
        """Test rating validation rejects values below 0.0."""
        with pytest.raises(ValueError, match="must be between 0.0 and 10.0"):
            ExternalFeedbackData(
                performance_ratings={"overall": -1.0}, suggestions=["Test"]
            )

    def test_feedback_data_rating_validation_above_range(self):
        """Test rating validation rejects values above 10.0."""
        with pytest.raises(ValueError, match="must be between 0.0 and 10.0"):
            ExternalFeedbackData(
                performance_ratings={"overall": 11.0}, suggestions=["Test"]
            )

    def test_feedback_data_rating_validation_non_numeric(self):
        """Test rating validation rejects non-numeric values."""
        with pytest.raises(ValidationError):
            ExternalFeedbackData(
                performance_ratings={"overall": "not a number"}, suggestions=["Test"]
            )

    def test_feedback_data_suggestions_validation_empty_list(self):
        """Test suggestions validation rejects empty list."""
        with pytest.raises(ValidationError):
            ExternalFeedbackData(performance_ratings={"overall": 8.5}, suggestions=[])

    def test_feedback_data_suggestions_validation_empty_string(self):
        """Test suggestions validation rejects empty strings."""
        with pytest.raises(ValueError, match="must be non-empty strings"):
            ExternalFeedbackData(
                performance_ratings={"overall": 8.5}, suggestions=[""]
            )

    def test_feedback_data_suggestions_validation_whitespace_only(self):
        """Test suggestions validation rejects whitespace-only strings."""
        with pytest.raises(ValueError, match="must be non-empty strings"):
            ExternalFeedbackData(
                performance_ratings={"overall": 8.5}, suggestions=["   "]
            )

    def test_feedback_data_to_dict(self):
        """Test serialization to dictionary."""
        feedback = ExternalFeedbackData(
            performance_ratings={"overall": 8.5}, suggestions=["Test"]
        )
        data = feedback.to_dict()

        assert isinstance(data, dict)
        assert data["feedback_id"] == feedback.feedback_id
        assert isinstance(data["timestamp"], str)  # ISO format string
        assert data["performance_ratings"] == {"overall": 8.5}
        assert data["suggestions"] == ["Test"]

    def test_feedback_data_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "feedback_id": "550e8400-e29b-41d4-a716-446655440000",
            "timestamp": "2026-01-09T08:29:34Z",
            "performance_ratings": {"overall": 8.5},
            "suggestions": ["Test"],
        }

        feedback = ExternalFeedbackData.from_dict(data)

        assert feedback.feedback_id == "550e8400-e29b-41d4-a716-446655440000"
        assert isinstance(feedback.timestamp, datetime)
        assert feedback.performance_ratings == {"overall": 8.5}
        assert feedback.suggestions == ["Test"]

    def test_feedback_data_from_dict_with_context(self):
        """Test deserialization with context."""
        data = {
            "feedback_id": "550e8400-e29b-41d4-a716-446655440000",
            "timestamp": "2026-01-09T08:29:34Z",
            "performance_ratings": {"overall": 8.5},
            "suggestions": ["Test"],
            "context": {
                "workflow_id": "workflow-123",
                "agent_id": "reviewer",
            },
        }

        feedback = ExternalFeedbackData.from_dict(data)

        assert feedback.context is not None
        assert feedback.context.workflow_id == "workflow-123"
        assert feedback.context.agent_id == "reviewer"

    def test_feedback_data_round_trip(self):
        """Test round-trip serialization (to_dict -> from_dict)."""
        original = ExternalFeedbackData(
            performance_ratings={"overall": 8.5, "usability": 7.0},
            suggestions=["Test suggestion 1", "Test suggestion 2"],
            context=FeedbackContext(workflow_id="workflow-123"),
            metrics=FeedbackMetrics(execution_time_seconds=45.2),
            project_id="my-project",
        )

        data = original.to_dict()
        restored = ExternalFeedbackData.from_dict(data)

        assert restored.feedback_id == original.feedback_id
        assert restored.performance_ratings == original.performance_ratings
        assert restored.suggestions == original.suggestions
        assert restored.project_id == original.project_id
        if original.context:
            assert restored.context is not None
            assert restored.context.workflow_id == original.context.workflow_id
