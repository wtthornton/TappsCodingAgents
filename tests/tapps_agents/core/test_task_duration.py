"""
Tests for task_duration.py
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.core.task_duration import (
    DurationEstimate,
    TaskDurationEstimator,
    create_duration_estimator,
)


class TestDurationEstimate:
    """Test DurationEstimate dataclass."""

    def test_init(self):
        """Test initialization."""
        estimate = DurationEstimate(
            estimated_seconds=15.0,
            confidence=0.8,
            method="historical",
            factors={"agent": "reviewer", "command": "review"},
        )
        assert estimate.estimated_seconds == 15.0
        assert estimate.confidence == 0.8
        assert estimate.method == "historical"
        assert estimate.factors == {"agent": "reviewer", "command": "review"}


class TestTaskDurationEstimator:
    """Test TaskDurationEstimator class."""

    def test_init_default(self):
        """Test initialization with defaults."""
        estimator = TaskDurationEstimator()
        assert estimator.project_root == Path.cwd()
        assert estimator.default_threshold == 30.0
        assert isinstance(estimator.history, dict)

    def test_init_custom(self):
        """Test initialization with custom parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            history_file = project_root / "custom-history.json"
            estimator = TaskDurationEstimator(
                project_root=project_root,
                history_file=history_file,
                default_threshold=60.0,
            )
            assert estimator.project_root == project_root
            assert estimator.history_file == history_file
            assert estimator.default_threshold == 60.0

    def test_load_history_no_file(self):
        """Test loading history when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            estimator = TaskDurationEstimator(project_root=Path(tmpdir))
            history = estimator._load_history()
            assert history == {}

    def test_load_history_with_file(self):
        """Test loading history from existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            # Create .tapps-agents directory
            tapps_dir = project_root / ".tapps-agents"
            tapps_dir.mkdir(parents=True, exist_ok=True)
            history_file = tapps_dir / "task-duration-history.json"
            
            # Create history with recent entry
            recent_timestamp = datetime.now().isoformat()
            history_data = {
                "reviewer:review": [
                    {
                        "timestamp": recent_timestamp,
                        "duration_seconds": 12.5,
                        "file_count": 1,
                    }
                ]
            }
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history_data, f)
            
            estimator = TaskDurationEstimator(project_root=project_root)
            history = estimator._load_history()
            assert "reviewer:review" in history
            assert len(history["reviewer:review"]) == 1

    def test_load_history_filters_old_entries(self):
        """Test that old entries are filtered out."""
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "task-duration-history.json"
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create history with old entry
            old_timestamp = (datetime.now() - timedelta(days=31)).isoformat()
            history_data = {
                "reviewer:review": [
                    {
                        "timestamp": old_timestamp,
                        "duration_seconds": 12.5,
                        "file_count": 1,
                    }
                ]
            }
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history_data, f)
            
            estimator = TaskDurationEstimator(project_root=Path(tmpdir))
            history = estimator._load_history()
            # Old entry should be filtered out
            assert "reviewer:review" not in history or len(history.get("reviewer:review", [])) == 0

    def test_save_history(self):
        """Test saving history to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            estimator = TaskDurationEstimator(project_root=Path(tmpdir))
            estimator.history["test:command"] = [
                {
                    "timestamp": datetime.now().isoformat(),
                    "duration_seconds": 10.0,
                    "file_count": 1,
                }
            ]
            estimator._save_history()
            
            assert estimator.history_file.exists()
            with open(estimator.history_file, encoding="utf-8") as f:
                saved_data = json.load(f)
            assert "test:command" in saved_data

    def test_get_file_count_multiplier(self):
        """Test file count multiplier calculation."""
        estimator = TaskDurationEstimator()
        
        assert estimator._get_file_count_multiplier(1) == 1.0
        assert estimator._get_file_count_multiplier(2) == 1.2
        assert estimator._get_file_count_multiplier(5) == 2.0
        assert estimator._get_file_count_multiplier(10) == 3.0
        assert estimator._get_file_count_multiplier(50) == 10.0
        assert estimator._get_file_count_multiplier(100) == 10.0  # Max multiplier

    def test_estimate_duration_heuristic(self):
        """Test duration estimation using heuristic."""
        estimator = TaskDurationEstimator()
        
        estimate = estimator.estimate_duration("reviewer", "score", file_count=1)
        
        assert estimate.estimated_seconds > 0
        assert estimate.method == "heuristic"
        assert estimate.confidence == 0.6
        assert "base_duration" in estimate.factors
        assert "file_multiplier" in estimate.factors

    def test_estimate_duration_with_file_count(self):
        """Test duration estimation with multiple files."""
        estimator = TaskDurationEstimator()
        
        estimate_single = estimator.estimate_duration("reviewer", "review", file_count=1)
        estimate_multiple = estimator.estimate_duration("reviewer", "review", file_count=10)
        
        assert estimate_multiple.estimated_seconds > estimate_single.estimated_seconds

    def test_estimate_duration_with_file_size(self):
        """Test duration estimation with file size."""
        estimator = TaskDurationEstimator()
        
        estimate_small = estimator.estimate_duration("reviewer", "review", file_size_kb=100.0)
        estimate_large = estimator.estimate_duration("reviewer", "review", file_size_kb=5000.0)
        
        assert estimate_large.estimated_seconds > estimate_small.estimated_seconds

    def test_estimate_duration_historical(self):
        """Test duration estimation using historical data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            estimator = TaskDurationEstimator(project_root=Path(tmpdir))
            
            # Record some historical data
            estimator.record_execution("reviewer", "review", 15.0, file_count=1)
            estimator.record_execution("reviewer", "review", 18.0, file_count=1)
            
            estimate = estimator.estimate_duration("reviewer", "review", file_count=1)
            
            assert estimate.method == "historical"
            assert estimate.confidence > 0.6
            assert "historical_avg" in estimate.factors
            assert estimate.factors["sample_count"] == 2

    def test_should_use_background_agent_below_threshold(self):
        """Test that short tasks don't use background agent."""
        estimator = TaskDurationEstimator(default_threshold=30.0)
        
        should_use, estimate = estimator.should_use_background_agent(
            "reviewer", "score", file_count=1
        )
        
        assert should_use is False
        assert estimate.estimated_seconds < 30.0

    def test_should_use_background_agent_above_threshold(self):
        """Test that long tasks use background agent."""
        estimator = TaskDurationEstimator(default_threshold=30.0)
        
        should_use, estimate = estimator.should_use_background_agent(
            "reviewer", "analyze-project", file_count=1
        )
        
        assert should_use is True
        assert estimate.estimated_seconds >= 30.0

    def test_should_use_background_agent_custom_threshold(self):
        """Test with custom threshold."""
        estimator = TaskDurationEstimator(default_threshold=30.0)
        
        should_use, estimate = estimator.should_use_background_agent(
            "reviewer", "review", file_count=1, threshold=10.0
        )
        
        # Should use background if estimate >= 10.0
        assert isinstance(should_use, bool)

    def test_record_execution(self):
        """Test recording execution time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            estimator = TaskDurationEstimator(project_root=Path(tmpdir))
            
            estimator.record_execution("reviewer", "review", 15.5, file_count=1)
            
            assert "reviewer:review" in estimator.history
            assert len(estimator.history["reviewer:review"]) == 1
            assert estimator.history["reviewer:review"][0]["duration_seconds"] == 15.5

    def test_record_execution_limits_entries(self):
        """Test that recording limits entries to 100."""
        with tempfile.TemporaryDirectory() as tmpdir:
            estimator = TaskDurationEstimator(project_root=Path(tmpdir))
            
            # Record 101 executions
            for i in range(101):
                estimator.record_execution("reviewer", "review", 15.0 + i, file_count=1)
            
            assert len(estimator.history["reviewer:review"]) == 100
            # Should keep the last 100
            assert estimator.history["reviewer:review"][0]["duration_seconds"] == 15.0 + 1

    def test_get_base_duration_known_command(self):
        """Test getting base duration for known command."""
        estimator = TaskDurationEstimator()
        
        duration = estimator._get_base_duration("reviewer", "score")
        assert duration == 2.0

    def test_get_base_duration_unknown_command(self):
        """Test getting base duration for unknown command."""
        estimator = TaskDurationEstimator()
        
        duration = estimator._get_base_duration("unknown_agent", "unknown_command")
        assert duration == 10.0  # Default


def test_create_duration_estimator():
    """Test convenience function to create estimator."""
    with tempfile.TemporaryDirectory() as tmpdir:
        estimator = create_duration_estimator(
            project_root=Path(tmpdir), threshold=60.0
        )
        
        assert isinstance(estimator, TaskDurationEstimator)
        assert estimator.project_root == Path(tmpdir)
        assert estimator.default_threshold == 60.0
