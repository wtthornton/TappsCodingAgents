"""
Unit tests for meta-learning system.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from tapps_agents.core.meta_learning import (
    LearningEffectivenessTracker,
    LearningSession,
    LearningSelfAssessor,
    AdaptiveLearningRate,
    LearningStrategySelector,
    LearningStrategy,
)


class TestLearningEffectivenessTracker:
    """Test LearningEffectivenessTracker functionality."""

    def test_init(self):
        """Test LearningEffectivenessTracker initialization."""
        tracker = LearningEffectivenessTracker()
        assert tracker is not None
        assert len(tracker.sessions) == 0
        assert tracker.max_sessions == 1000

    def test_track_effectiveness(self):
        """Test tracking learning effectiveness."""
        tracker = LearningEffectivenessTracker()

        before_metrics = {
            "quality_score": 0.7,
            "success_rate": 0.8,
        }
        after_metrics = {
            "quality_score": 0.85,
            "success_rate": 0.9,
        }

        session = tracker.track_effectiveness(
            capability_id="test_capability",
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            strategies_used=["balanced"],
        )

        assert session is not None
        assert session.capability_id == "test_capability"
        assert session.improvement_percent > 0
        assert session.effectiveness_score > 0
        assert len(tracker.sessions) == 1

    def test_calculate_improvement_rate(self):
        """Test calculating improvement rate."""
        tracker = LearningEffectivenessTracker()

        # Track some sessions
        for i in range(5):
            tracker.track_effectiveness(
                capability_id="test_capability",
                before_metrics={"quality_score": 0.7 + i * 0.01},
                after_metrics={"quality_score": 0.75 + i * 0.01},
            )

        rate = tracker.calculate_improvement_rate(
            capability_id="test_capability",
            days=30,
        )

        assert rate["sessions_count"] == 5
        assert "average_improvement" in rate
        assert "improvement_rate" in rate

    def test_get_effective_strategies(self):
        """Test getting effective strategies."""
        tracker = LearningEffectivenessTracker()

        # Track sessions with different strategies
        tracker.track_effectiveness(
            capability_id="test",
            before_metrics={"score": 0.7},
            after_metrics={"score": 0.8},
            strategies_used=["conservative"],
        )
        tracker.track_effectiveness(
            capability_id="test",
            before_metrics={"score": 0.7},
            after_metrics={"score": 0.9},
            strategies_used=["aggressive"],
        )

        strategies = tracker.get_effective_strategies(capability_id="test")

        assert isinstance(strategies, dict)
        assert "conservative" in strategies or "aggressive" in strategies

    def test_get_learning_roi(self):
        """Test getting learning ROI."""
        tracker = LearningEffectivenessTracker()

        # Track some sessions
        for i in range(3):
            tracker.track_effectiveness(
                capability_id="test",
                before_metrics={"score": 0.7},
                after_metrics={"score": 0.8 + i * 0.05},
            )

        roi = tracker.get_learning_roi(capability_id="test")

        assert roi["total_sessions"] == 3
        assert "roi_score" in roi
        assert roi["roi_score"] > 0


class TestLearningSelfAssessor:
    """Test LearningSelfAssessor functionality."""

    def test_init(self):
        """Test LearningSelfAssessor initialization."""
        assessor = LearningSelfAssessor()
        assert assessor is not None
        assert len(assessor.assessments) == 0

    def test_assess_learning_quality(self):
        """Test assessing learning quality."""
        assessor = LearningSelfAssessor()

        assessment = assessor.assess_learning_quality(
            pattern_count=50,
            anti_pattern_count=10,
            average_quality=0.85,
            average_security=8.5,
        )

        assert "quality_score" in assessment
        assert assessment["pattern_count"] == 50
        assert assessment["average_quality"] == 0.85
        assert 0.0 <= assessment["quality_score"] <= 1.0

    def test_evaluate_pattern_quality(self):
        """Test evaluating pattern quality."""
        assessor = LearningSelfAssessor()

        # Mock patterns
        patterns = [
            Mock(quality_score=0.9, security_score=8.0),
            Mock(quality_score=0.8, security_score=7.5),
        ]

        evaluation = assessor.evaluate_pattern_quality(patterns)

        assert evaluation["total_patterns"] == 2
        assert "average_quality" in evaluation
        assert "average_security" in evaluation
        assert "quality_score" in evaluation

    def test_identify_learning_gaps(self):
        """Test identifying learning gaps."""
        assessor = LearningSelfAssessor()

        capability_metrics = {
            "success_rate": 0.75,  # Below 0.8 threshold
        }
        pattern_statistics = {
            "total_patterns": 5,  # Below 10 threshold
            "average_quality": 0.6,  # Below 0.7 threshold
            "average_security": 6.0,  # Below 7.0 threshold
        }

        gaps = assessor.identify_learning_gaps(
            capability_metrics=capability_metrics,
            pattern_statistics=pattern_statistics,
        )

        assert isinstance(gaps, list)
        assert len(gaps) > 0

    def test_suggest_improvements(self):
        """Test suggesting improvements."""
        assessor = LearningSelfAssessor()

        assessment = {
            "quality_score": 0.6,  # Low
            "pattern_count": 5,  # Low
            "average_security": 6.0,  # Low
        }

        suggestions = assessor.suggest_improvements(assessment)

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0


class TestAdaptiveLearningRate:
    """Test AdaptiveLearningRate functionality."""

    def test_init(self):
        """Test AdaptiveLearningRate initialization."""
        rate = AdaptiveLearningRate(base_rate=0.7)
        assert rate is not None
        assert rate.base_rate == 0.7
        assert rate.current_rate == 0.7

    def test_calculate_optimal_rate_high_effectiveness(self):
        """Test calculating optimal rate with high effectiveness."""
        rate = AdaptiveLearningRate(base_rate=0.7)

        optimal = rate.calculate_optimal_rate([0.9, 0.85, 0.9])

        # High effectiveness should increase rate
        assert optimal >= rate.base_rate

    def test_calculate_optimal_rate_low_effectiveness(self):
        """Test calculating optimal rate with low effectiveness."""
        rate = AdaptiveLearningRate(base_rate=0.7)

        optimal = rate.calculate_optimal_rate([0.3, 0.35, 0.3])

        # Low effectiveness should decrease rate
        assert optimal <= rate.base_rate

    def test_adjust_learning_intensity(self):
        """Test adjusting learning intensity."""
        rate = AdaptiveLearningRate(base_rate=0.7)

        adjustment = rate.adjust_learning_intensity(0.85)

        assert "previous_rate" in adjustment
        assert "new_rate" in adjustment
        assert "effectiveness" in adjustment
        assert "adjustment" in adjustment

    def test_optimize_thresholds_high_success(self):
        """Test optimizing thresholds with high success rate."""
        rate = AdaptiveLearningRate()

        optimized = rate.optimize_thresholds(
            current_threshold=0.7,
            success_rate=0.95,
            quality_score=0.85,
        )

        # High success and quality should allow lower threshold
        assert optimized <= 0.7

    def test_optimize_thresholds_low_success(self):
        """Test optimizing thresholds with low success rate."""
        rate = AdaptiveLearningRate()

        optimized = rate.optimize_thresholds(
            current_threshold=0.7,
            success_rate=0.6,
            quality_score=0.65,
        )

        # Low success should raise threshold
        assert optimized >= 0.7

    def test_balance_exploration(self):
        """Test balancing exploration vs exploitation."""
        rate = AdaptiveLearningRate()

        balance = rate.balance_exploration(exploration_rate=0.1)

        assert "exploration_rate" in balance
        assert "exploitation_rate" in balance
        assert balance["exploration_rate"] + balance["exploitation_rate"] == 1.0


class TestLearningStrategySelector:
    """Test LearningStrategySelector functionality."""

    def test_init(self):
        """Test LearningStrategySelector initialization."""
        selector = LearningStrategySelector()
        assert selector is not None
        assert len(selector.strategy_performance) == 0

    def test_select_strategy_high_effectiveness(self):
        """Test selecting strategy with high effectiveness."""
        selector = LearningStrategySelector()

        strategy = selector.select_strategy(
            capability_id="test",
            current_effectiveness=0.9,
            hardware_profile=None,
        )

        # High effectiveness should select aggressive
        assert strategy == LearningStrategy.AGGRESSIVE

    def test_select_strategy_low_effectiveness(self):
        """Test selecting strategy with low effectiveness."""
        selector = LearningStrategySelector()

        strategy = selector.select_strategy(
            capability_id="test",
            current_effectiveness=0.3,
            hardware_profile=None,
        )

        # Low effectiveness should select conservative
        assert strategy == LearningStrategy.CONSERVATIVE

    def test_select_strategy_nuc_hardware(self):
        """Test selecting strategy for NUC hardware."""
        selector = LearningStrategySelector()

        strategy = selector.select_strategy(
            capability_id="test",
            current_effectiveness=0.6,
            hardware_profile="nuc",
        )

        # NUC hardware should select conservative
        assert strategy == LearningStrategy.CONSERVATIVE

    def test_test_strategy(self):
        """Test testing strategy effectiveness."""
        selector = LearningStrategySelector()

        result = selector.test_strategy(
            strategy=LearningStrategy.BALANCED,
            effectiveness=0.85,
        )

        assert result["strategy"] == "balanced"
        assert result["effectiveness"] == 0.85
        assert "average_effectiveness" in result
        assert "test_count" in result

    def test_switch_strategy(self):
        """Test switching strategies."""
        selector = LearningStrategySelector()

        # Test both strategies
        selector.test_strategy(LearningStrategy.CONSERVATIVE, 0.7)
        selector.test_strategy(LearningStrategy.AGGRESSIVE, 0.9)

        switch_result = selector.switch_strategy(
            current_strategy=LearningStrategy.CONSERVATIVE,
            new_strategy=LearningStrategy.AGGRESSIVE,
        )

        assert "switched" in switch_result
        assert switch_result["switched"] is True  # Aggressive is better

    def test_optimize_strategy(self):
        """Test optimizing strategy parameters."""
        selector = LearningStrategySelector()

        parameters = {
            "quality_threshold": 0.7,
            "security_threshold": 7.0,
        }

        optimized = selector.optimize_strategy(
            strategy=LearningStrategy.CONSERVATIVE,
            parameters=parameters,
        )

        assert "quality_threshold" in optimized
        assert "security_threshold" in optimized
        # Conservative should have higher thresholds
        assert optimized["quality_threshold"] >= 0.7
        assert optimized["security_threshold"] >= 7.0

