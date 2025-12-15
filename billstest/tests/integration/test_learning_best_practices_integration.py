"""
Integration tests for Learning System + Best Practices integration.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from tapps_agents.core.agent_learning import AgentLearner
from tapps_agents.core.capability_registry import CapabilityRegistry
from tapps_agents.core.hardware_profiler import HardwareProfile
from tapps_agents.core.learning_decision import DecisionSource
from tapps_agents.experts.expert_registry import ConsultationResult, ExpertRegistry


class TestLearningBestPracticesIntegration:
    """Integration tests for learning system with best practices."""

    @pytest.fixture
    def capability_registry(self):
        """Create capability registry."""
        return CapabilityRegistry()

    @pytest.fixture
    def hardware_profile(self):
        """Create hardware profile."""
        return HardwareProfile.WORKSTATION

    @pytest.fixture
    def mock_expert_registry(self):
        """Create mock expert registry."""
        registry = MagicMock(spec=ExpertRegistry)

        # Mock consultation result
        mock_result = ConsultationResult(
            domain="agent-learning",
            query="test query",
            responses=[],
            weighted_answer="Use threshold 0.75 for pattern extraction",
            agreement_level=0.9,
            confidence=0.85,
            confidence_threshold=0.7,
            primary_expert="expert-agent-learning",
            all_experts_agreed=True,
        )

        registry.consult = AsyncMock(return_value=mock_result)
        return registry

    @pytest.mark.asyncio
    async def test_agent_learner_with_expert_registry(
        self, capability_registry, hardware_profile, mock_expert_registry
    ):
        """Test AgentLearner initialization with expert registry."""
        learner = AgentLearner(
            capability_registry=capability_registry,
            hardware_profile=hardware_profile,
            expert_registry=mock_expert_registry,
        )

        assert learner.decision_engine is not None
        assert learner.decision_engine.best_practice_consultant is not None

    @pytest.mark.asyncio
    async def test_learn_from_task_with_decision_engine(
        self, capability_registry, hardware_profile, mock_expert_registry
    ):
        """Test learning from task with decision engine."""
        learner = AgentLearner(
            capability_registry=capability_registry,
            hardware_profile=hardware_profile,
            expert_registry=mock_expert_registry,
        )

        # Register a capability first
        capability_registry.register_capability(
            capability_id="test-capability", agent_id="test-agent"
        )

        # Update metrics to have good learned experience
        capability_registry.update_capability_metrics(
            capability_id="test-capability",
            success=True,
            duration=1.0,
            quality_score=0.85,
        )

        # Learn from task with high quality code
        results = await learner.learn_from_task(
            capability_id="test-capability",
            task_id="test-task-1",
            code="def test_function():\n    return True",
            quality_scores={"overall_score": 85.0},
            success=True,
            duration=1.0,
        )

        # Should extract patterns (decision engine should allow it)
        assert "patterns_extracted" in results
        assert results["feedback_analyzed"] is True

    @pytest.mark.asyncio
    async def test_decision_engine_uses_learned_experience(
        self, capability_registry, hardware_profile, mock_expert_registry
    ):
        """Test that decision engine prioritizes high-confidence learned experience."""
        learner = AgentLearner(
            capability_registry=capability_registry,
            hardware_profile=hardware_profile,
            expert_registry=mock_expert_registry,
        )

        # Register and build up good learned experience
        capability_registry.register_capability(
            capability_id="test-capability", agent_id="test-agent"
        )

        # Update metrics multiple times to build confidence
        for _i in range(20):
            capability_registry.update_capability_metrics(
                capability_id="test-capability",
                success=True,
                duration=1.0,
                quality_score=0.9,
            )

        # Get capability metric
        metric = capability_registry.get_capability("test-capability")
        assert metric.usage_count >= 20
        assert metric.success_rate >= 0.9

        # Make decision - should use learned experience
        decision = await learner.decision_engine.make_decision(
            decision_type="pattern_extraction_threshold",
            learned_data={
                "usage_count": metric.usage_count,
                "success_rate": metric.success_rate,
                "quality_score": metric.quality_score,
                "value": 0.8,
                "context_relevance": 1.0,
            },
            context={"hardware_profile": "workstation", "learning_intensity": "medium"},
            default_value=0.7,
        )

        # Should prioritize learned experience with high confidence
        assert decision.result.source == DecisionSource.LEARNED_EXPERIENCE
        assert decision.result.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_decision_engine_falls_back_to_best_practice(
        self, capability_registry, hardware_profile, mock_expert_registry
    ):
        """Test that decision engine falls back to best practices when learned confidence is low."""
        learner = AgentLearner(
            capability_registry=capability_registry,
            hardware_profile=hardware_profile,
            expert_registry=mock_expert_registry,
        )

        # Register capability with poor learned experience
        capability_registry.register_capability(
            capability_id="test-capability", agent_id="test-agent"
        )

        # Update metrics with poor performance
        capability_registry.update_capability_metrics(
            capability_id="test-capability",
            success=False,
            duration=1.0,
            quality_score=0.4,
        )

        metric = capability_registry.get_capability("test-capability")

        # Make decision - should use best practice
        decision = await learner.decision_engine.make_decision(
            decision_type="pattern_extraction_threshold",
            learned_data={
                "usage_count": metric.usage_count,
                "success_rate": metric.success_rate,
                "quality_score": metric.quality_score,
                "value": 0.5,
                "context_relevance": 1.0,
            },
            context={"hardware_profile": "workstation", "learning_intensity": "medium"},
            default_value=0.7,
        )

        # Should use best practice when learned confidence is low
        assert decision.result.source == DecisionSource.BEST_PRACTICE
        assert decision.best_practice_advice is not None

    @pytest.mark.asyncio
    async def test_decision_engine_cache_performance(
        self, capability_registry, hardware_profile, mock_expert_registry
    ):
        """Test that decision engine caching improves performance."""
        learner = AgentLearner(
            capability_registry=capability_registry,
            hardware_profile=hardware_profile,
            expert_registry=mock_expert_registry,
        )

        # First decision - should consult expert
        await learner.decision_engine.make_decision(
            decision_type="quality_threshold",
            learned_data={
                "usage_count": 5,
                "success_rate": 0.5,
                "quality_score": 0.5,
                "value": 0.6,
            },
            context={"hardware_profile": "workstation"},
            default_value=0.7,
        )

        # Verify expert was consulted
        assert mock_expert_registry.consult.call_count == 1

        # Second decision with same context - should use cache
        await learner.decision_engine.make_decision(
            decision_type="quality_threshold",
            learned_data={
                "usage_count": 5,
                "success_rate": 0.5,
                "quality_score": 0.5,
                "value": 0.6,
            },
            context={"hardware_profile": "workstation"},
            default_value=0.7,
        )

        # Should still be 1 call (cached)
        assert mock_expert_registry.consult.call_count == 1

        # Get cache statistics
        cache_stats = learner.decision_engine.get_cache_statistics()
        assert cache_stats is not None
        assert cache_stats["cache_hits"] >= 1

    @pytest.mark.asyncio
    async def test_backward_compatibility_no_expert_registry(
        self, capability_registry, hardware_profile
    ):
        """Test that system works without expert registry (backward compatibility)."""
        learner = AgentLearner(
            capability_registry=capability_registry,
            hardware_profile=hardware_profile,
            expert_registry=None,
        )

        # Should still work with hard-coded thresholds
        capability_registry.register_capability(
            capability_id="test-capability", agent_id="test-agent"
        )

        results = await learner.learn_from_task(
            capability_id="test-capability",
            task_id="test-task",
            code="def test():\n    return True",
            quality_scores={"overall_score": 85.0},
            success=True,
            duration=1.0,
        )

        # Should still extract patterns (using hard-coded threshold)
        assert "patterns_extracted" in results
