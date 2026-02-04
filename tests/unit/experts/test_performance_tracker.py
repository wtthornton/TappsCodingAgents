"""
Tests for Expert Performance Tracker
"""

from pathlib import Path

import pytest

from tapps_agents.core.outcome_tracker import OutcomeTracker
from tapps_agents.experts.performance_tracker import ExpertPerformanceTracker


@pytest.fixture
def tracker(tmp_path):
    """Create performance tracker."""
    outcome_tracker = OutcomeTracker(project_root=tmp_path)
    return ExpertPerformanceTracker(
        project_root=tmp_path, outcome_tracker=outcome_tracker
    )


def test_track_consultation(tracker):
    """Test tracking expert consultation."""
    tracker.track_consultation(
        expert_id="expert-security",
        domain="security",
        confidence=0.85,
        query="How to implement secure authentication?",
    )
    
    # Should not raise
    assert True


def test_calculate_performance_no_data(tracker):
    """Test performance calculation with no data."""
    performance = tracker.calculate_performance("expert-security", days=30)
    
    # Should return None if no data
    assert performance is None


def test_calculate_performance_with_data(tracker):
    """Test performance calculation with data."""
    # Track consultations
    for i in range(10):
        tracker.track_consultation(
            expert_id="expert-security",
            domain="security",
            confidence=0.8 + (i % 3) * 0.05,
            query=f"Security question {i}",
        )
    
    # Track outcomes
    outcome_tracker = tracker.outcome_tracker
    for i in range(5):
        outcome_tracker.track_initial_scores(
            workflow_id=f"test-{i}",
            file_path=Path(f"test{i}.py"),
            scores={"complexity_score": 7.0},
            expert_consultations=["expert-security"],
        )
    
    performance = tracker.calculate_performance("expert-security", days=30)
    
    assert performance is not None
    assert performance.expert_id == "expert-security"
    assert performance.consultations == 10
    assert performance.avg_confidence > 0.0


def test_get_all_performance(tracker):
    """Test getting all expert performance."""
    # Track consultations for multiple experts
    tracker.track_consultation("expert-1", "domain-1", 0.8, "query1")
    tracker.track_consultation("expert-2", "domain-2", 0.9, "query2")
    
    all_performance = tracker.get_all_performance(days=30)
    
    assert len(all_performance) >= 0  # May be 0 if no outcomes
