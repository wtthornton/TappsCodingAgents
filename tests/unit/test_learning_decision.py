"""
Unit tests for Learning Decision Engine.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from tapps_agents.core.best_practice_consultant import (
    BestPracticeAdvice,
    BestPracticeConsultant,
)
from tapps_agents.core.learning_confidence import LearningConfidenceCalculator
from tapps_agents.core.learning_decision import (
    DecisionSource,
    LearningDecisionEngine,
)

pytestmark = pytest.mark.unit


class TestLearningDecisionEngine:
    """Test LearningDecisionEngine."""

    @pytest.fixture
    def mock_capability_registry(self):
        """Create mock capability registry."""
        return MagicMock()

    @pytest.fixture
    def mock_best_practice_consultant(self):
        """Create mock best practice consultant."""
        from unittest.mock import AsyncMock
        mock = MagicMock(spec=BestPracticeConsultant)
        mock.consult_best_practices = AsyncMock(return_value=None)
        return mock

    @pytest.fixture
    def decision_engine(self, mock_capability_registry, mock_best_practice_consultant):
        """Create LearningDecisionEngine instance."""
        return LearningDecisionEngine(
            capability_registry=mock_capability_registry,
            best_practice_consultant=mock_best_practice_consultant,
            confidence_calculator=LearningConfidenceCalculator(),
        )

    @pytest.mark.asyncio
    async def test_make_decision_high_learned_confidence(self, decision_engine):
        """Test decision with high learned confidence."""
        # High learned confidence should be prioritized
        decision = await decision_engine.make_decision(
            decision_type="quality_threshold",
            learned_data={
                "usage_count": 100,
                "success_rate": 0.9,
                "quality_score": 0.85,
                "value": 0.8,
            },
            context={},
            default_value=0.7,
        )

        assert decision.result.source == DecisionSource.LEARNED_EXPERIENCE
        assert decision.result.value == 0.8
        assert decision.result.confidence >= 0.8
        assert decision.result.should_proceed is True
        assert "High confidence from learned experience" in decision.result.reasoning

    @pytest.mark.asyncio
    async def test_make_decision_high_best_practice_confidence(
        self, decision_engine, mock_best_practice_consultant
    ):
        """Test decision with high best practice confidence."""
        # Mock best practice advice
        mock_advice = BestPracticeAdvice(
            advice="Use threshold 0.75", confidence=0.85, source="expert", cached=False
        )
        mock_best_practice_consultant.consult_best_practices = AsyncMock(
            return_value=mock_advice
        )

        # Low learned confidence, high best practice
        decision = await decision_engine.make_decision(
            decision_type="quality_threshold",
            learned_data={
                "usage_count": 5,
                "success_rate": 0.5,
                "quality_score": 0.5,
                "value": 0.6,
            },
            context={},
            default_value=0.7,
        )

        assert decision.result.source == DecisionSource.BEST_PRACTICE
        assert decision.result.confidence >= 0.7
        assert decision.result.should_proceed is True
        assert "High confidence from best practices" in decision.result.reasoning

    @pytest.mark.asyncio
    async def test_make_decision_moderate_learned_confidence(self, decision_engine):
        """Test decision with moderate learned confidence."""
        decision = await decision_engine.make_decision(
            decision_type="quality_threshold",
            learned_data={
                "usage_count": 20,
                "success_rate": 0.7,
                "quality_score": 0.7,
                "value": 0.7,
            },
            context={},
            default_value=0.6,
        )

        assert decision.result.source == DecisionSource.LEARNED_EXPERIENCE
        assert decision.result.confidence >= 0.6
        assert decision.result.should_proceed is True
        assert (
            "Moderate confidence from learned experience" in decision.result.reasoning
        )

    @pytest.mark.asyncio
    async def test_make_decision_best_practice_fallback(
        self, decision_engine, mock_best_practice_consultant
    ):
        """Test decision with best practice fallback."""
        # Mock best practice advice
        mock_advice = BestPracticeAdvice(
            advice="Use threshold 0.65", confidence=0.65, source="expert", cached=False
        )
        mock_best_practice_consultant.consult_best_practices = AsyncMock(
            return_value=mock_advice
        )

        # Low learned confidence
        decision = await decision_engine.make_decision(
            decision_type="quality_threshold",
            learned_data={
                "usage_count": 3,
                "success_rate": 0.4,
                "quality_score": 0.4,
                "value": 0.5,
            },
            context={},
            default_value=0.6,
        )

        assert decision.result.source == DecisionSource.BEST_PRACTICE
        assert decision.result.should_proceed is True
        assert "fallback" in decision.result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_make_decision_default_fallback(
        self, decision_engine, mock_best_practice_consultant
    ):
        """Test decision with default fallback."""
        # Mock best practice to return None (consultation failed)
        mock_best_practice_consultant.consult_best_practices = AsyncMock(
            return_value=None
        )

        # Low learned confidence, no best practice
        decision = await decision_engine.make_decision(
            decision_type="quality_threshold",
            learned_data={
                "usage_count": 2,
                "success_rate": 0.3,
                "quality_score": 0.3,
                "value": 0.4,
            },
            context={},
            default_value=0.7,
        )

        assert decision.result.source == DecisionSource.DEFAULT
        assert decision.result.value == 0.7
        assert decision.result.should_proceed is False
        assert "No sufficient confidence" in decision.result.reasoning

    @pytest.mark.asyncio
    async def test_make_decision_no_best_practice_consultant(self):
        """Test decision without best practice consultant."""
        engine = LearningDecisionEngine(
            capability_registry=MagicMock(),
            best_practice_consultant=None,
            confidence_calculator=LearningConfidenceCalculator(),
        )

        decision = await engine.make_decision(
            decision_type="quality_threshold",
            learned_data={
                "usage_count": 50,
                "success_rate": 0.8,
                "quality_score": 0.8,
                "value": 0.75,
            },
            context={},
            default_value=0.7,
        )

        # Should use learned experience
        assert decision.result.source == DecisionSource.LEARNED_EXPERIENCE
        assert decision.best_practice_advice is None

    def test_calculate_learned_confidence(self, decision_engine):
        """Test learned confidence calculation."""
        confidence = decision_engine._calculate_learned_confidence(
            {
                "usage_count": 50,
                "success_rate": 0.85,
                "quality_score": 0.8,
                "context_relevance": 1.0,
            }
        )

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.7  # Should be good with these metrics

    def test_extract_value_from_advice(self, decision_engine):
        """Test value extraction from advice."""
        advice = "Use threshold 0.75 for pattern extraction"
        value = decision_engine._extract_value_from_advice(advice, "quality_threshold")

        # Should return the advice text (simple implementation)
        assert value == advice

    def test_apply_decision_logic_priority_order(self, decision_engine):
        """Test decision logic priority order."""
        # Priority 1: High learned
        result1 = decision_engine._apply_decision_logic(
            learned_confidence=0.85,
            best_practice_confidence=0.8,
            learned_value=0.8,
            best_practice_value=0.75,
            default_value=0.7,
            decision_type="test",
        )
        assert result1.source == DecisionSource.LEARNED_EXPERIENCE
        assert result1.value == 0.8

        # Priority 2: High best practice (low learned)
        result2 = decision_engine._apply_decision_logic(
            learned_confidence=0.5,
            best_practice_confidence=0.75,
            learned_value=0.6,
            best_practice_value=0.75,
            default_value=0.7,
            decision_type="test",
        )
        assert result2.source == DecisionSource.BEST_PRACTICE
        assert result2.value == 0.75

    def test_get_decision_statistics(self, decision_engine):
        """Test decision statistics."""
        # Make some decisions
        import asyncio

        asyncio.run(
            decision_engine.make_decision(
                decision_type="quality_threshold",
                learned_data={
                    "usage_count": 10,
                    "success_rate": 0.7,
                    "quality_score": 0.7,
                    "value": 0.7,
                },
                context={},
                default_value=0.6,
            )
        )

        stats = decision_engine.get_decision_statistics()

        assert stats["total_decisions"] > 0
        assert "by_type" in stats
        assert "by_source" in stats

    def test_get_cache_statistics(self, decision_engine, mock_best_practice_consultant):
        """Test cache statistics retrieval."""
        mock_best_practice_consultant.get_cache_statistics.return_value = {
            "cache_size": 10,
            "hit_rate": 0.8,
        }

        stats = decision_engine.get_cache_statistics()

        assert stats is not None
        assert stats["cache_size"] == 10
        assert stats["hit_rate"] == 0.8

    def test_get_cache_statistics_no_consultant(self):
        """Test cache statistics without consultant."""
        engine = LearningDecisionEngine(
            capability_registry=MagicMock(), best_practice_consultant=None
        )

        stats = engine.get_cache_statistics()
        assert stats is None
