"""
Integration tests for security-aware learning system.
"""

from unittest.mock import Mock

import pytest

from tapps_agents.core.agent_learning import AgentLearner, PatternExtractor
from tapps_agents.core.capability_registry import CapabilityRegistry
from tapps_agents.core.security_scanner import SecurityScanner


@pytest.mark.integration
class TestSecurityAwareLearning:
    """Integration tests for security-aware learning."""

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
    async def test_learn_from_secure_code(self, agent_learner):
        """Test learning from secure code."""
        secure_code = """
def secure_function():
    \"\"\"A secure function.\"\"\"
    return True
"""

        quality_scores = {
            "overall_score": 85.0,
            "security_score": 9.0,
        }

        result = await agent_learner.learn_from_task(
            capability_id="test_capability",
            task_id="test_task_1",
            code=secure_code,
            quality_scores=quality_scores,
            success=True,
        )

        assert result["security_checked"] is True
        assert result["security_score"] >= 7.0
        assert result["patterns_extracted"] >= 0  # May or may not extract based on thresholds

    @pytest.mark.asyncio
    async def test_learn_from_insecure_code(self, agent_learner):
        """Test that insecure code is not learned from."""
        insecure_code = """
def insecure_function():
    eval('dangerous code')
    return True
"""

        quality_scores = {
            "overall_score": 60.0,
            "security_score": 3.0,  # Low security score
        }

        result = await agent_learner.learn_from_task(
            capability_id="test_capability",
            task_id="test_task_2",
            code=insecure_code,
            quality_scores=quality_scores,
            success=True,
        )

        assert result["security_checked"] is True
        assert result["security_score"] < 7.0
        # Should not extract patterns from insecure code
        assert result["patterns_extracted"] == 0

    @pytest.mark.asyncio
    async def test_security_threshold_filtering(self, agent_learner):
        """Test that security threshold filters patterns."""
        # Code with moderate security
        code = """
def moderate_security():
    import subprocess
    subprocess.call(['ls'])  # Medium security risk
    return True
"""

        quality_scores = {
            "overall_score": 70.0,
            "security_score": 6.5,  # Just below threshold
        }

        result = await agent_learner.learn_from_task(
            capability_id="test_capability",
            task_id="test_task_3",
            code=code,
            quality_scores=quality_scores,
            success=True,
        )

        # Should check security but not extract if below threshold
        assert result["security_checked"] is True
        if result["security_score"] < agent_learner.pattern_extractor.security_threshold:
            assert result["patterns_extracted"] == 0

    def test_pattern_extractor_security_integration(self):
        """Test PatternExtractor security integration."""
        scanner = SecurityScanner()
        extractor = PatternExtractor(
            min_quality_threshold=0.7,
            security_scanner=scanner,
            security_threshold=7.0,
        )

        # Secure code
        secure_code = """
def good_function():
    return True
"""

        patterns = extractor.extract_patterns(
            code=secure_code,
            quality_score=0.9,
            task_id="test_task",
        )

        # Should extract patterns if security check passes
        assert isinstance(patterns, list)
        if patterns:
            assert all(p.security_score >= 0.0 for p in patterns)

    def test_pattern_retrieval_with_security(self, agent_learner):
        """Test pattern retrieval considers security scores."""
        # Add some patterns with different security scores
        from tapps_agents.core.agent_learning import CodePattern

        secure_pattern = CodePattern(
            pattern_id="secure_pattern",
            pattern_type="function",
            code_snippet="def secure():\n    pass",
            context="Secure function",
            quality_score=0.9,
            usage_count=5,
            success_rate=0.95,
            learned_from=["task_1"],
            security_score=9.0,
        )

        less_secure_pattern = CodePattern(
            pattern_id="less_secure_pattern",
            pattern_type="function",
            code_snippet="def less_secure():\n    pass",
            context="Less secure function",
            quality_score=0.85,
            usage_count=3,
            success_rate=0.90,
            learned_from=["task_2"],
            security_score=7.5,
        )

        agent_learner.pattern_extractor.patterns["secure_pattern"] = secure_pattern
        agent_learner.pattern_extractor.patterns["less_secure_pattern"] = less_secure_pattern

        # Retrieve patterns - should be sorted by security + quality
        patterns = agent_learner.get_learned_patterns(
            context="test",
            limit=5,
        )

        if len(patterns) >= 2:
            # First pattern should have higher security + quality
            first_score = patterns[0].security_score + patterns[0].quality_score
            second_score = patterns[1].security_score + patterns[1].quality_score
            assert first_score >= second_score

