"""
Integration tests for Reviewer Agent.

These tests verify that the Reviewer Agent creates instruction objects
for Cursor Skills execution instead of calling LLMs directly.
"""

import pytest

from tapps_agents.agents.reviewer.agent import ReviewerAgent
from tapps_agents.core.config import ProjectConfig


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
class TestReviewerAgentReal:
    """Integration tests for Reviewer Agent with instruction objects."""

    @pytest.fixture
    def reviewer_agent(self):
        """Create reviewer agent instance."""
        return ReviewerAgent()

    @pytest.fixture
    def sample_python_file(self, tmp_path):
        """Create a minimal Python file for testing."""
        file_path = tmp_path / "test_code.py"
        file_path.write_text("""def add(a, b):
    return a + b
""")
        return file_path

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_reviewer_agent_real_score(self, reviewer_agent, sample_python_file):
        """Test reviewer agent scoring."""
        reviewer = reviewer_agent
        
        try:
            await reviewer.activate()
            result = await reviewer.run("score", file=str(sample_python_file))
            
            assert "file" in result
            assert "scoring" in result
            assert "overall_score" in result["scoring"]
            assert 0 <= result["scoring"]["overall_score"] <= 100
        finally:
            await reviewer.close()

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_reviewer_agent_error_handling_real(self, reviewer_agent, tmp_path):
        """Test reviewer error handling."""
        non_existent = tmp_path / "nonexistent.py"
        reviewer = reviewer_agent
        
        try:
            await reviewer.activate()
            try:
                result = await reviewer.run("score", file=str(non_existent))
                assert "error" in result or "file" not in result
            except FileNotFoundError:
                pass
        finally:
            await reviewer.close()

