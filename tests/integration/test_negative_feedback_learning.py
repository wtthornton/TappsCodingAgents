"""
Integration tests for negative feedback learning system.
"""

import pytest
from unittest.mock import Mock

from tapps_agents.core.agent_learning import AgentLearner
from tapps_agents.core.capability_registry import CapabilityRegistry


@pytest.mark.integration
class TestNegativeFeedbackLearning:
    """Integration tests for negative feedback learning."""

    @pytest.fixture
    def capability_registry(self):
        """Create a capability registry for testing."""
        return CapabilityRegistry()

    @pytest.fixture
    def expert_registry(self):
        """Create a mock expert registry."""
        return Mock()

    @pytest.fixture
    def agent_learner(self, capability_registry, expert_registry):
        """Create an AgentLearner instance."""
        return AgentLearner(
            capability_registry=capability_registry,
            expert_registry=expert_registry,
        )

    @pytest.mark.asyncio
    async def test_learn_from_failure(self, agent_learner):
        """Test learning from failed tasks."""
        failed_code = """
def failed_function():
    # This function has issues
    return None
"""

        quality_scores = {
            "overall_score": 40.0,  # Low quality
            "security_score": 5.0,
        }

        result = await agent_learner.learn_from_task(
            capability_id="test_capability",
            task_id="test_task_failure",
            code=failed_code,
            quality_scores=quality_scores,
            success=False,  # Task failed
        )

        assert result["failure_analyzed"] is True
        assert "failure_analysis" in result
        assert result["anti_patterns_extracted"] > 0

        # Check that anti-patterns were stored
        assert len(agent_learner.anti_pattern_extractor.anti_patterns) > 0

    @pytest.mark.asyncio
    async def test_learn_from_rejection(self, agent_learner):
        """Test learning from user rejection."""
        rejected_code = """
def rejected_function():
    eval('unsafe')
    return True
"""

        result = await agent_learner.learn_from_rejection(
            capability_id="test_capability",
            task_id="test_task_rejection",
            code=rejected_code,
            rejection_reason="Code contains security vulnerabilities",
            quality_score=0.4,
        )

        assert result["rejection_recorded"] is True
        assert result["anti_patterns_extracted"] > 0

        # Check that rejection was recorded
        assert len(agent_learner.negative_feedback_handler.rejections) == 1
        assert (
            agent_learner.negative_feedback_handler.rejections[0]["reason"]
            == "Code contains security vulnerabilities"
        )

    @pytest.mark.asyncio
    async def test_learn_from_low_quality(self, agent_learner):
        """Test learning anti-patterns from low-quality code."""
        low_quality_code = """
def low_quality_function():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    # Too many variables, poor structure
    return x + y + z + a + b
"""

        quality_scores = {
            "overall_score": 35.0,  # Very low quality
        }

        result = await agent_learner.learn_from_task(
            capability_id="test_capability",
            task_id="test_task_low_quality",
            code=low_quality_code,
            quality_scores=quality_scores,
            success=True,  # Task succeeded but quality is low
        )

        # Should extract anti-patterns from low-quality code
        assert result["anti_patterns_extracted"] > 0

    @pytest.mark.asyncio
    async def test_failure_mode_analysis(self, agent_learner):
        """Test failure mode analysis integration."""
        failed_code = """
def syntax_error_function(
    # Missing closing parenthesis
    return True
"""

        quality_scores = {
            "overall_score": 20.0,
        }

        result = await agent_learner.learn_from_task(
            capability_id="test_capability",
            task_id="test_task_syntax_error",
            code=failed_code,
            quality_scores=quality_scores,
            success=False,
        )

        assert result["failure_analyzed"] is True
        failure_analysis = result["failure_analysis"]
        assert "failure_mode" in failure_analysis
        assert "suggestions" in failure_analysis

        # Check that failure mode was tracked
        common_modes = agent_learner.failure_mode_analyzer.get_common_failure_modes()
        assert len(common_modes) > 0

    def test_anti_pattern_retrieval(self, agent_learner):
        """Test retrieving anti-patterns to avoid."""
        # Add some anti-patterns
        from tapps_agents.core.agent_learning import CodePattern

        anti_pattern = CodePattern(
            pattern_id="anti_pattern_1",
            pattern_type="function",
            code_snippet="def bad():\n    eval('unsafe')",
            context="Bad function",
            quality_score=0.3,
            usage_count=1,
            success_rate=0.0,
            learned_from=["task_1"],
            is_anti_pattern=True,
            failure_reasons=["Security issue"],
            rejection_count=2,
        )

        agent_learner.anti_pattern_extractor.anti_patterns["anti_pattern_1"] = (
            anti_pattern
        )

        # Get anti-patterns
        anti_patterns = agent_learner.negative_feedback_handler.get_anti_patterns_for_context(
            context="test",
            limit=5,
        )

        assert len(anti_patterns) > 0
        assert all(p.is_anti_pattern for p in anti_patterns)

    def test_pattern_exclusion(self, agent_learner):
        """Test that anti-patterns are excluded by default."""
        from tapps_agents.core.agent_learning import CodePattern

        # Add a regular pattern
        regular_pattern = CodePattern(
            pattern_id="regular_pattern",
            pattern_type="function",
            code_snippet="def good():\n    pass",
            context="Good function",
            quality_score=0.9,
            usage_count=5,
            success_rate=0.95,
            learned_from=["task_1"],
            is_anti_pattern=False,
        )

        # Add an anti-pattern
        anti_pattern = CodePattern(
            pattern_id="anti_pattern",
            pattern_type="function",
            code_snippet="def bad():\n    pass",
            context="Bad function",
            quality_score=0.3,
            usage_count=1,
            success_rate=0.0,
            learned_from=["task_2"],
            is_anti_pattern=True,
        )

        agent_learner.pattern_extractor.patterns["regular_pattern"] = regular_pattern
        agent_learner.pattern_extractor.patterns["anti_pattern"] = anti_pattern

        # Get patterns - should exclude anti-patterns by default
        patterns = agent_learner.get_learned_patterns(
            context="test",
            exclude_anti_patterns=True,
        )

        assert all(not p.is_anti_pattern for p in patterns)

        # Get patterns including anti-patterns
        all_patterns = agent_learner.get_learned_patterns(
            context="test",
            exclude_anti_patterns=False,
        )

        assert len(all_patterns) >= len(patterns)
        assert any(p.is_anti_pattern for p in all_patterns)

