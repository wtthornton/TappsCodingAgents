"""
Unit tests for external feedback storage.

Tests cover:
- Saving and loading feedback
- Listing feedback with filters
- Aggregating feedback statistics
- Error handling
- File system operations
"""

from datetime import UTC, datetime, timedelta

import pytest

from tapps_agents.core.external_feedback_models import (
    ExternalFeedbackData,
    FeedbackContext,
    FeedbackMetrics,
)
from tapps_agents.core.external_feedback_storage import ExternalFeedbackStorage

pytestmark = pytest.mark.unit


class TestExternalFeedbackStorage:
    """Test ExternalFeedbackStorage class."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create storage instance with temporary directory."""
        return ExternalFeedbackStorage(project_root=tmp_path)

    @pytest.fixture
    def sample_feedback(self):
        """Create sample feedback data."""
        return ExternalFeedbackData(
            performance_ratings={"overall": 8.5, "usability": 7.0},
            suggestions=["Test suggestion"],
            context=FeedbackContext(workflow_id="workflow-123", agent_id="reviewer"),
            metrics=FeedbackMetrics(execution_time_seconds=45.2),
            project_id="test-project",
        )

    def test_storage_initialization(self, tmp_path):
        """Test storage initialization creates directory."""
        storage = ExternalFeedbackStorage(project_root=tmp_path)
        assert storage.project_root == tmp_path
        assert storage.feedback_dir.exists()
        assert storage.feedback_dir == tmp_path / ".tapps-agents" / "feedback"

    def test_storage_initialization_default_project_root(self, monkeypatch, tmp_path):
        """Test storage uses current directory when project_root is None."""
        monkeypatch.chdir(tmp_path)
        storage = ExternalFeedbackStorage(project_root=None)
        assert storage.project_root == tmp_path
        assert storage.feedback_dir.exists()

    def test_save_feedback(self, storage, sample_feedback):
        """Test saving feedback creates file."""
        file_path = storage.save_feedback(sample_feedback)

        assert file_path.exists()
        assert file_path.name == f"feedback-{sample_feedback.feedback_id}.json"
        assert file_path.parent == storage.feedback_dir

    def test_save_feedback_file_content(self, storage, sample_feedback):
        """Test saved file contains correct data."""
        file_path = storage.save_feedback(sample_feedback)

        import json

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["feedback_id"] == sample_feedback.feedback_id
        assert data["performance_ratings"] == {"overall": 8.5, "usability": 7.0}
        assert data["suggestions"] == ["Test suggestion"]

    def test_load_feedback(self, storage, sample_feedback):
        """Test loading feedback by ID."""
        storage.save_feedback(sample_feedback)

        loaded = storage.load_feedback(sample_feedback.feedback_id)

        assert loaded is not None
        assert loaded.feedback_id == sample_feedback.feedback_id
        assert loaded.performance_ratings == sample_feedback.performance_ratings
        assert loaded.suggestions == sample_feedback.suggestions

    def test_load_feedback_not_found(self, storage):
        """Test loading non-existent feedback returns None."""
        loaded = storage.load_feedback("nonexistent-id")
        assert loaded is None

    def test_list_feedback_empty(self, storage):
        """Test listing feedback when no feedback exists."""
        feedback_list = storage.list_feedback()
        assert feedback_list == []

    def test_list_feedback_all(self, storage):
        """Test listing all feedback."""
        feedback1 = ExternalFeedbackData(
            performance_ratings={"overall": 8.0}, suggestions=["Test 1"]
        )
        feedback2 = ExternalFeedbackData(
            performance_ratings={"overall": 9.0}, suggestions=["Test 2"]
        )

        storage.save_feedback(feedback1)
        storage.save_feedback(feedback2)

        feedback_list = storage.list_feedback()

        assert len(feedback_list) == 2
        feedback_ids = [f.feedback_id for f in feedback_list]
        assert feedback1.feedback_id in feedback_ids
        assert feedback2.feedback_id in feedback_ids

    def test_list_feedback_filter_by_workflow_id(self, storage):
        """Test filtering feedback by workflow_id."""
        feedback1 = ExternalFeedbackData(
            performance_ratings={"overall": 8.0},
            suggestions=["Test 1"],
            context=FeedbackContext(workflow_id="workflow-123"),
        )
        feedback2 = ExternalFeedbackData(
            performance_ratings={"overall": 9.0},
            suggestions=["Test 2"],
            context=FeedbackContext(workflow_id="workflow-456"),
        )

        storage.save_feedback(feedback1)
        storage.save_feedback(feedback2)

        feedback_list = storage.list_feedback(workflow_id="workflow-123")

        assert len(feedback_list) == 1
        assert feedback_list[0].feedback_id == feedback1.feedback_id

    def test_list_feedback_filter_by_agent_id(self, storage):
        """Test filtering feedback by agent_id."""
        feedback1 = ExternalFeedbackData(
            performance_ratings={"overall": 8.0},
            suggestions=["Test 1"],
            context=FeedbackContext(agent_id="reviewer"),
        )
        feedback2 = ExternalFeedbackData(
            performance_ratings={"overall": 9.0},
            suggestions=["Test 2"],
            context=FeedbackContext(agent_id="implementer"),
        )

        storage.save_feedback(feedback1)
        storage.save_feedback(feedback2)

        feedback_list = storage.list_feedback(agent_id="reviewer")

        assert len(feedback_list) == 1
        assert feedback_list[0].feedback_id == feedback1.feedback_id

    def test_list_feedback_filter_by_date_range(self, storage):
        """Test filtering feedback by date range."""
        now = datetime.now(UTC)
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        # Create feedback with different timestamps (we can't control timestamp in model)
        feedback1 = ExternalFeedbackData(
            performance_ratings={"overall": 8.0}, suggestions=["Test 1"]
        )
        # Manually set timestamp for testing
        feedback1.timestamp = yesterday

        feedback2 = ExternalFeedbackData(
            performance_ratings={"overall": 9.0}, suggestions=["Test 2"]
        )
        feedback2.timestamp = tomorrow

        storage.save_feedback(feedback1)
        storage.save_feedback(feedback2)

        # Filter by date range that includes yesterday but not tomorrow
        start_date = yesterday - timedelta(hours=1)
        end_date = now

        feedback_list = storage.list_feedback(start_date=start_date, end_date=end_date)

        # Should find feedback1 (yesterday) but not feedback2 (tomorrow)
        feedback_ids = [f.feedback_id for f in feedback_list]
        assert feedback1.feedback_id in feedback_ids
        assert feedback2.feedback_id not in feedback_ids

    def test_list_feedback_limit(self, storage):
        """Test limiting number of results."""
        for i in range(5):
            feedback = ExternalFeedbackData(
                performance_ratings={"overall": float(i)}, suggestions=[f"Test {i}"]
            )
            storage.save_feedback(feedback)

        feedback_list = storage.list_feedback(limit=3)

        assert len(feedback_list) == 3

    def test_aggregate_feedback_empty(self, storage):
        """Test aggregation with no feedback."""
        aggregated = storage.aggregate_feedback()

        assert aggregated["count"] == 0
        assert aggregated["average_ratings"] == {}
        assert aggregated["suggestion_count"] == 0

    def test_aggregate_feedback_basic(self, storage):
        """Test basic aggregation statistics."""
        feedback1 = ExternalFeedbackData(
            performance_ratings={"overall": 8.0, "usability": 7.0},
            suggestions=["Suggestion 1"],
        )
        feedback2 = ExternalFeedbackData(
            performance_ratings={"overall": 9.0, "usability": 8.0},
            suggestions=["Suggestion 2", "Suggestion 3"],
        )

        storage.save_feedback(feedback1)
        storage.save_feedback(feedback2)

        aggregated = storage.aggregate_feedback()

        assert aggregated["count"] == 2
        assert aggregated["average_ratings"]["overall"] == 8.5
        assert aggregated["average_ratings"]["usability"] == 7.5
        assert aggregated["suggestion_count"] == 3
        assert aggregated["average_suggestions_per_feedback"] == 1.5

    def test_aggregate_feedback_with_filters(self, storage):
        """Test aggregation with filters."""
        feedback1 = ExternalFeedbackData(
            performance_ratings={"overall": 8.0},
            suggestions=["Test 1"],
            context=FeedbackContext(workflow_id="workflow-123"),
        )
        feedback2 = ExternalFeedbackData(
            performance_ratings={"overall": 9.0},
            suggestions=["Test 2"],
            context=FeedbackContext(workflow_id="workflow-456"),
        )

        storage.save_feedback(feedback1)
        storage.save_feedback(feedback2)

        aggregated = storage.aggregate_feedback(workflow_id="workflow-123")

        assert aggregated["count"] == 1
        assert aggregated["average_ratings"]["overall"] == 8.0
