"""
E2E tests for negative feedback learning with real scenarios.

Tests learning from failures, user rejections, and low-quality code
in realistic end-to-end scenarios.
"""

import logging
from pathlib import Path

import pytest

from tapps_agents.core.agent_learning import AgentLearner
from tapps_agents.core.capability_registry import CapabilityRegistry
from tapps_agents.core.hardware_profiler import HardwareProfile
from tapps_agents.core.task_memory import TaskMemorySystem
from tapps_agents.experts.expert_registry import ExpertRegistry

logger = logging.getLogger(__name__)


@pytest.mark.e2e_workflow
@pytest.mark.template_type("small")
class TestNegativeFeedbackE2E:
    """E2E tests for negative feedback learning."""

    @pytest.fixture
    def agent_learner(self):
        """Create an AgentLearner instance for negative feedback testing."""
        return AgentLearner(
            capability_registry=CapabilityRegistry(),
            expert_registry=ExpertRegistry(),
            memory_system=TaskMemorySystem(),
            hardware_profile=HardwareProfile.WORKSTATION,
        )

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_learn_from_real_failure(
        self, agent_learner, e2e_project: Path
    ):
        """Test learning from a real task failure."""
        # Code that would cause a real failure
        failing_code = """
def broken_function():
    \"\"\"Function with intentional bugs.\"\"\"
    # Syntax error (commented out for test, but represents real failure)
    # x = 
    
    # Logic error
    result = 10 / 0  # Division by zero
    
    # Type error
    value = "string" + 5  # Type mismatch
    
    return result
"""
        result = await agent_learner.learn_from_task(
            capability_id="failure_test",
            task_id="task_failure",
            code=failing_code,
            quality_scores={"overall_score": 20.0, "security_score": 5.0},
            success=False,
        )

        # Should analyze failure
        assert result["failure_analyzed"] is True
        assert "failure_analysis" in result
        assert result["failure_analysis"]["failure_mode"] is not None

        # Should extract anti-patterns
        assert result["anti_patterns_extracted"] > 0

        # Verify failure mode was tracked
        common_modes = agent_learner.failure_mode_analyzer.get_common_failure_modes(
            limit=10
        )
        assert len(common_modes) > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_learn_from_user_rejection(
        self, agent_learner, e2e_project: Path
    ):
        """Test learning from user rejection."""
        rejected_code = """
def rejected_function():
    \"\"\"Function rejected by user.\"\"\"
    # User didn't like this approach
    x = 1
    y = 2
    z = 3
    # Too many variables, poor style
    return x + y + z
"""
        result = await agent_learner.learn_from_rejection(
            capability_id="rejection_test",
            task_id="task_rejection",
            code=rejected_code,
            rejection_reason="Code style is not acceptable. Too many variables, poor structure.",
            quality_score=0.4,
        )

        # Should record rejection
        assert result["rejection_recorded"] is True
        assert result["anti_patterns_extracted"] > 0

        # Verify rejection was stored
        assert len(agent_learner.negative_feedback_handler.rejections) == 1
        assert (
            agent_learner.negative_feedback_handler.rejections[0]["reason"]
            == "Code style is not acceptable. Too many variables, poor structure."
        )

        # Verify anti-patterns have rejection count
        anti_patterns = agent_learner.anti_pattern_extractor.get_anti_patterns_for_context(
            context="rejection_test", limit=5
        )
        assert len(anti_patterns) > 0
        assert any(p.rejection_count > 0 for p in anti_patterns)

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_learn_from_low_quality_success(
        self, agent_learner, e2e_project: Path
    ):
        """Test learning anti-patterns from low-quality but successful code."""
        low_quality_code = """
def low_quality_function():
    # Bad naming
    x = 1
    y = 2
    # No docstring
    # Poor structure
    z = x + y
    return z
"""
        result = await agent_learner.learn_from_task(
            capability_id="quality_test",
            task_id="task_low_quality",
            code=low_quality_code,
            quality_scores={
                "overall_score": 35.0,  # Low quality
                "maintainability_score": 3.0,
                "security_score": 8.0,  # Secure but low quality
            },
            success=True,  # Task succeeded but quality is low
        )

        # Should extract anti-patterns from low-quality code
        assert result["anti_patterns_extracted"] > 0

        # Verify anti-patterns were stored
        anti_patterns = agent_learner.anti_pattern_extractor.get_anti_patterns_for_context(
            context="quality_test", limit=5
        )
        assert len(anti_patterns) > 0
        assert all(p.is_anti_pattern for p in anti_patterns)

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_anti_pattern_exclusion_in_retrieval(
        self, agent_learner, e2e_project: Path
    ):
        """Test that anti-patterns are excluded from pattern retrieval."""
        # Add a good pattern
        from tapps_agents.core.agent_learning import CodePattern

        good_pattern = CodePattern(
            pattern_id="good_pattern",
            pattern_type="function",
            code_snippet="def good():\n    return True",
            context="Good",
            quality_score=0.9,
            usage_count=5,
            success_rate=0.95,
            learned_from=["task_1"],
            is_anti_pattern=False,
        )

        # Add an anti-pattern
        bad_pattern = CodePattern(
            pattern_id="bad_pattern",
            pattern_type="function",
            code_snippet="def bad():\n    eval('unsafe')",
            context="Bad",
            quality_score=0.3,
            usage_count=1,
            success_rate=0.0,
            learned_from=["task_2"],
            is_anti_pattern=True,
            failure_reasons=["Security issue"],
        )

        agent_learner.pattern_extractor.patterns["good_pattern"] = good_pattern
        agent_learner.pattern_extractor.patterns["bad_pattern"] = bad_pattern

        # Retrieve patterns - should exclude anti-patterns by default
        patterns = agent_learner.get_learned_patterns(
            context="test", exclude_anti_patterns=True
        )

        assert len(patterns) == 1
        assert patterns[0].pattern_id == "good_pattern"
        assert not patterns[0].is_anti_pattern

        # Retrieve all patterns including anti-patterns
        all_patterns = agent_learner.get_learned_patterns(
            context="test", exclude_anti_patterns=False
        )

        assert len(all_patterns) == 2
        assert any(p.pattern_id == "bad_pattern" for p in all_patterns)

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_failure_mode_analysis_e2e(
        self, agent_learner, e2e_project: Path
    ):
        """Test failure mode analysis in E2E scenario."""
        # Multiple failures of different types
        failures = [
            {
                "code": "def syntax_error(\n    pass",  # Syntax error
                "reasons": ["SyntaxError: invalid syntax"],
            },
            {
                "code": "eval('unsafe')",  # Security issue
                "reasons": ["Security vulnerability detected"],
                "scores": {"security_score": 2.0},
            },
            {
                "code": "for i in range(1000000):\n    for j in range(1000000):\n        pass",  # Performance
                "reasons": ["Timeout: code too slow"],
            },
        ]

        for i, failure in enumerate(failures):
            await agent_learner.learn_from_task(
                capability_id="failure_analysis_test",
                task_id=f"task_fail_{i}",
                code=failure["code"],
                quality_scores=failure.get("scores", {}),
                success=False,
            )

        # Get common failure modes
        common_modes = agent_learner.failure_mode_analyzer.get_common_failure_modes(
            limit=10
        )

        assert len(common_modes) >= 2  # Should have multiple failure modes
        assert all("mode" in mode for mode in common_modes)
        assert all("count" in mode for mode in common_modes)

        # Verify failure modes are categorized correctly
        mode_types = [mode["mode"] for mode in common_modes]
        assert "syntax_error" in mode_types or "security_issue" in mode_types

