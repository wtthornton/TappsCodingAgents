"""
Tests for Outcome Tracker
"""

import pytest
from pathlib import Path

from tapps_agents.core.outcome_tracker import CodeOutcome, OutcomeTracker


@pytest.fixture
def tracker(tmp_path):
    """Create tracker instance."""
    return OutcomeTracker(project_root=tmp_path)


def test_track_initial_scores(tracker):
    """Test tracking initial scores."""
    outcome = tracker.track_initial_scores(
        workflow_id="test-workflow-1",
        file_path=Path("test.py"),
        scores={
            "complexity_score": 7.0,
            "security_score": 8.0,
            "maintainability_score": 7.5,
            "test_coverage_score": 6.0,
            "performance_score": 7.0,
            "structure_score": 8.0,
            "devex_score": 7.0,
        },
        expert_consultations=["expert-security"],
        agent_id="implementer",
    )
    
    assert outcome.workflow_id == "test-workflow-1"
    assert outcome.iterations == 1
    assert "expert-security" in outcome.expert_consultations
    assert outcome.first_pass_success is not None


def test_finalize_outcome(tracker):
    """Test finalizing outcome."""
    outcome = tracker.track_initial_scores(
        workflow_id="test-workflow-2",
        file_path=Path("test.py"),
        scores={"complexity_score": 6.0},
    )
    
    finalized = tracker.finalize_outcome(
        workflow_id="test-workflow-2",
        final_scores={"complexity_score": 8.0},
        time_to_correctness=120.0,
    )
    
    assert finalized is not None
    assert finalized.final_scores["complexity_score"] == 8.0
    assert finalized.time_to_correctness == 120.0


def test_load_outcomes(tracker):
    """Test loading outcomes."""
    # Track some outcomes
    tracker.track_initial_scores(
        workflow_id="test-1",
        file_path=Path("test1.py"),
        scores={"complexity_score": 7.0},
    )
    tracker.track_initial_scores(
        workflow_id="test-2",
        file_path=Path("test2.py"),
        scores={"complexity_score": 8.0},
    )
    
    outcomes = tracker.load_outcomes()
    assert len(outcomes) >= 2


def test_get_outcome_statistics(tracker):
    """Test outcome statistics."""
    # Track outcomes
    for i in range(5):
        tracker.track_initial_scores(
            workflow_id=f"test-{i}",
            file_path=Path(f"test{i}.py"),
            scores={"complexity_score": 7.0 + i * 0.5},
        )
    
    stats = tracker.get_outcome_statistics()
    assert stats["total_outcomes"] >= 5
    assert "first_pass_success_rate" in stats
    assert "avg_iterations" in stats
