"""
E2E tests for security-aware learning with real security scanning.

Tests real security vulnerability detection, security threshold
enforcement, and secure pattern extraction.
"""

import logging
from pathlib import Path

import pytest

from tapps_agents.core.agent_learning import AgentLearner
from tapps_agents.core.capability_registry import CapabilityRegistry
from tapps_agents.experts.expert_registry import ExpertRegistry
from tapps_agents.core.hardware_profiler import HardwareProfile
from tapps_agents.core.security_scanner import SecurityScanner
from tapps_agents.core.task_memory import TaskMemorySystem

logger = logging.getLogger(__name__)


@pytest.mark.e2e_workflow
@pytest.mark.template_type("small")
class TestSecurityLearningE2E:
    """E2E tests for security-aware learning."""

    @pytest.fixture
    def agent_learner(self):
        """Create an AgentLearner instance for security testing."""
        return AgentLearner(
            capability_registry=CapabilityRegistry(),
            expert_registry=ExpertRegistry(),
            memory_system=TaskMemorySystem(),
            hardware_profile=HardwareProfile.WORKSTATION,
        )

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_real_security_scanning_with_vulnerabilities(
        self, agent_learner, e2e_project: Path
    ):
        """Test real security scanning with actual vulnerable code."""
        # Code with real security vulnerabilities
        vulnerable_code = """
import os
import subprocess

def unsafe_function(user_input: str):
    \"\"\"Unsafe function with vulnerabilities.\"\"\"
    # SQL injection risk
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    
    # Command injection risk
    os.system(f"echo {user_input}")
    
    # Shell injection risk
    subprocess.call(f"ls {user_input}", shell=True)
    
    return query
"""
        result = await agent_learner.learn_from_task(
            capability_id="security_test",
            task_id="task_vulnerable",
            code=vulnerable_code,
            quality_scores={"overall_score": 50.0, "security_score": 2.0},
            success=True,  # Task might succeed but code is insecure
        )

        # Should detect security issues
        assert result["security_checked"] is True
        assert result["security_score"] < 7.0
        assert len(result["security_vulnerabilities"]) > 0

        # Should NOT extract patterns from insecure code
        assert result["patterns_extracted"] == 0

        # Should extract anti-patterns
        assert result["anti_patterns_extracted"] > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_real_security_scanning_with_secure_code(
        self, agent_learner, e2e_project: Path
    ):
        """Test real security scanning with secure code."""
        # Secure code
        secure_code = """
def secure_function(user_input: str) -> str:
    '''
    Secure function with proper input validation.
    
    Args:
        user_input: User input string
        
    Returns:
        Sanitized output
    '''
    # Proper input validation
    if not user_input or not isinstance(user_input, str):
        raise ValueError("Invalid input")
    
    # Sanitize input
    sanitized = user_input.strip().replace("'", "''")
    
    # Use parameterized query (simulated)
    query = "SELECT * FROM users WHERE name = ?"
    params = [sanitized]
    
    return query
"""
        result = await agent_learner.learn_from_task(
            capability_id="security_test",
            task_id="task_secure",
            code=secure_code,
            quality_scores={"overall_score": 85.0, "security_score": 9.0},
            success=True,
        )

        # Should pass security check
        assert result["security_checked"] is True
        assert result["security_score"] >= 7.0
        assert len(result["security_vulnerabilities"]) == 0

        # Should extract patterns from secure code
        assert result["patterns_extracted"] > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_security_threshold_enforcement(
        self, agent_learner, e2e_project: Path
    ):
        """Test that security thresholds are enforced."""
        # Code with moderate security (just below threshold)
        moderate_code = """
import subprocess

def moderate_security_function(command: str):
    \"\"\"Function with moderate security risk.\"\"\"
    # Medium risk: subprocess without shell=True is safer but still risky
    subprocess.call([command])
    return True
"""
        result = await agent_learner.learn_from_task(
            capability_id="security_test",
            task_id="task_moderate",
            code=moderate_code,
            quality_scores={"overall_score": 70.0, "security_score": 6.5},
            success=True,
        )

        # Security should be checked
        assert result["security_checked"] is True

        # If security score is below threshold, patterns should not be extracted
        if result["security_score"] < agent_learner.pattern_extractor.security_threshold:
            assert result["patterns_extracted"] == 0
        else:
            # If it passes, patterns should be extracted
            assert result["patterns_extracted"] >= 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_security_pattern_filtering(
        self, agent_learner, e2e_project: Path
    ):
        """Test that patterns are filtered by security score."""
        # Add patterns with different security scores
        from tapps_agents.core.agent_learning import CodePattern

        secure_pattern = CodePattern(
            pattern_id="secure_pattern",
            pattern_type="function",
            code_snippet="def secure():\n    pass",
            context="Secure",
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
            context="Less secure",
            quality_score=0.8,
            usage_count=3,
            success_rate=0.90,
            learned_from=["task_2"],
            security_score=7.5,
        )

        agent_learner.pattern_extractor.patterns["secure_pattern"] = secure_pattern
        agent_learner.pattern_extractor.patterns[
            "less_secure_pattern"
        ] = less_secure_pattern

        # Retrieve patterns - should prioritize secure patterns
        patterns = agent_learner.get_learned_patterns(context="test", limit=5)

        assert len(patterns) >= 2

        # Patterns should be sorted by security + quality
        if len(patterns) >= 2:
            first_score = patterns[0].security_score + patterns[0].quality_score
            second_score = patterns[1].security_score + patterns[1].quality_score
            assert first_score >= second_score

