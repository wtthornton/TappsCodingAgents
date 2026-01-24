"""
Tests for Adaptive Scoring Engine
"""

import pytest

from tapps_agents.core.adaptive_scoring import AdaptiveScoringEngine
from tapps_agents.core.outcome_tracker import CodeOutcome, OutcomeTracker


@pytest.fixture
def engine(tmp_path):
    """Create adaptive scoring engine."""
    tracker = OutcomeTracker(project_root=tmp_path)
    return AdaptiveScoringEngine(outcome_tracker=tracker)


@pytest.mark.asyncio
async def test_adjust_weights_insufficient_data(engine):
    """Test weight adjustment with insufficient data."""
    # Should return default weights if not enough outcomes
    weights = await engine.adjust_weights(outcomes=[], current_weights=None)
    
    assert weights is not None
    assert "complexity" in weights
    assert "security" in weights
    assert abs(sum(weights.values()) - 1.0) < 0.01


@pytest.mark.asyncio
async def test_adjust_weights_with_outcomes(engine):
    """Test weight adjustment with sufficient outcomes."""
    # Create mock outcomes
    outcomes = []
    for i in range(15):  # More than MIN_OUTCOMES_FOR_ADJUSTMENT
        outcome = CodeOutcome(
            workflow_id=f"test-{i}",
            file_path=f"test{i}.py",
            initial_scores={
                "complexity_score": 7.0 if i % 2 == 0 else 5.0,
                "security_score": 8.0 if i % 2 == 0 else 6.0,
                "maintainability_score": 7.5,
                "test_coverage_score": 6.0,
                "performance_score": 7.0,
                "structure_score": 8.0,
                "devex_score": 7.0,
            },
            final_scores={},
            iterations=1 if i % 2 == 0 else 3,
            first_pass_success=(i % 2 == 0),
        )
        outcomes.append(outcome)
    
    weights = await engine.adjust_weights(outcomes=outcomes, current_weights=None)
    
    assert weights is not None
    assert abs(sum(weights.values()) - 1.0) < 0.01


def test_pearson_correlation(engine):
    """Test Pearson correlation calculation."""
    x = [0.7, 0.8, 0.9, 0.6, 0.5]
    y = [True, True, True, False, False]
    
    correlation = engine._pearson_correlation(x, y)
    
    # Should be positive correlation (higher scores = more success)
    assert correlation > 0
    assert -1.0 <= correlation <= 1.0


def test_get_weight_adjustment_recommendation(engine):
    """Test weight adjustment recommendation."""
    outcomes = []
    for i in range(15):
        outcome = CodeOutcome(
            workflow_id=f"test-{i}",
            file_path=f"test{i}.py",
            initial_scores={
                "complexity_score": 7.0,
                "security_score": 8.0,
                "maintainability_score": 7.5,
                "test_coverage_score": 6.0,
                "performance_score": 7.0,
                "structure_score": 8.0,
                "devex_score": 7.0,
            },
            final_scores={},
            iterations=1,
            first_pass_success=(i % 2 == 0),
        )
        outcomes.append(outcome)
    
    recommendation = engine.get_weight_adjustment_recommendation(outcomes=outcomes)
    
    assert recommendation["recommended"] is True
    assert "correlations" in recommendation
    assert "adjustments" in recommendation
