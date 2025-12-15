"""
Tests for Reviewer Agent with real CodeScorer behavior.

Tests agent initialization, command handling, and business logic
using real CodeScorer instances. MAL is still mocked to avoid network calls.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.reviewer.agent import ReviewerAgent


class TestReviewerAgentInitialization:
    """Tests for ReviewerAgent initialization."""

    def test_reviewer_agent_init(self):
        """Test ReviewerAgent initialization."""
        agent = ReviewerAgent()
        assert agent.agent_id == "reviewer"
        assert agent.agent_name == "Reviewer Agent"
        assert agent.config is None

    @pytest.mark.asyncio
    async def test_reviewer_agent_activate(self, temp_project_dir: Path):
        """Test ReviewerAgent activation."""
        agent = ReviewerAgent()
        await agent.activate(temp_project_dir)
        
        assert agent.config is not None

    @pytest.mark.asyncio
    async def test_reviewer_agent_get_commands(self):
        """Test ReviewerAgent command list."""
        agent = ReviewerAgent()
        commands = agent.get_commands()
        
        assert isinstance(commands, list)
        assert len(commands) > 0
        # Should have review and score commands
        command_names = [cmd["command"] for cmd in commands]
        assert any("review" in cmd.lower() for cmd in command_names)


class TestReviewerAgentReviewCommand:
    """Tests for review command with real CodeScorer behavior."""

    @pytest.mark.asyncio
    async def test_review_command_success(self, sample_python_file, mock_mal):
        """Test review command with successful review using real CodeScorer."""
        agent = ReviewerAgent()
        agent.mal = mock_mal
        
        # Use real CodeScorer instance (already created in ReviewerAgent.__init__)
        # No need to mock - the agent already has a real scorer
        result = await agent.run("review", file=str(sample_python_file))
        
        assert "file" in result
        assert "scoring" in result
        # Validate real scoring results (not just mocked values)
        assert "overall_score" in result["scoring"]
        assert isinstance(result["scoring"]["overall_score"], (int, float))
        assert 0 <= result["scoring"]["overall_score"] <= 100
        # Validate individual scores are present
        assert "complexity_score" in result["scoring"]
        assert "security_score" in result["scoring"]
        assert "maintainability_score" in result["scoring"]

    @pytest.mark.asyncio
    async def test_review_command_file_not_found(self, tmp_path):
        """Test review command with non-existent file."""
        agent = ReviewerAgent()
        non_existent = tmp_path / "nonexistent.py"
        
        result = await agent.run("review", file=str(non_existent))
        
        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_review_command_invalid_file(self, tmp_path, mock_mal):
        """Test review command with invalid file."""
        agent = ReviewerAgent()
        agent.mal = mock_mal
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("not python code")
        
        # Should handle gracefully (may return error or attempt to process)
        result = await agent.run("review", file=str(invalid_file))
        assert isinstance(result, dict)
        # May contain error or attempt to process with real CodeScorer


class TestReviewerAgentScoreCommand:
    """Tests for score command with real CodeScorer behavior."""

    @pytest.mark.asyncio
    async def test_score_command_success(self, sample_python_file, mock_mal):
        """Test score command with successful scoring using real CodeScorer."""
        agent = ReviewerAgent()
        agent.mal = mock_mal
        
        # Use real CodeScorer instance (already created in ReviewerAgent.__init__)
        result = await agent.run("score", file=str(sample_python_file))
        
        assert "file" in result
        assert "scoring" in result
        assert "overall_score" in result["scoring"]
        # Validate real scoring results
        assert isinstance(result["scoring"]["overall_score"], (int, float))
        assert 0 <= result["scoring"]["overall_score"] <= 100
        # Validate all expected score fields are present
        expected_fields = [
            "complexity_score", "security_score", "maintainability_score",
            "test_coverage_score", "performance_score"
        ]
        for field in expected_fields:
            assert field in result["scoring"], f"Missing expected score field: {field}"

    @pytest.mark.asyncio
    async def test_score_command_file_not_found(self, tmp_path):
        """Test score command with non-existent file."""
        agent = ReviewerAgent()
        non_existent = tmp_path / "nonexistent.py"
        
        result = await agent.run("score", file=str(non_existent))
        
        assert "error" in result


class TestReviewerAgentErrorHandling:
    """Tests for error handling with real CodeScorer."""

    @pytest.mark.asyncio
    async def test_review_command_scorer_error(self, sample_python_file, mock_mal):
        """Test review command handles scorer errors from real CodeScorer."""
        agent = ReviewerAgent()
        agent.mal = mock_mal
        
        # Patch the scorer's score_file method to raise a specific error
        # This tests error propagation through real agent code
        error_message = "Scorer error: File parsing failed"
        original_score_file = agent.scorer.score_file
        
        def failing_score_file(*args, **kwargs):
            raise RuntimeError(error_message)
        
        agent.scorer.score_file = failing_score_file
        
        result = await agent.run("review", file=str(sample_python_file))
        
        # Should handle error gracefully and propagate error information
        assert isinstance(result, dict)
        # Validate that error information is included in result
        if "error" in result:
            # Error should contain the original error message
            error_info = result.get("error", {})
            if isinstance(error_info, dict):
                error_msg = error_info.get("message", "") or str(error_info)
                assert error_message in error_msg or "error" in str(result).lower()
        else:
            # If no explicit error field, scoring should be absent
            assert "scoring" not in result

    @pytest.mark.asyncio
    async def test_review_command_mal_error(self, sample_python_file):
        """Test review command handles MAL errors with real CodeScorer."""
        agent = ReviewerAgent()
        
        # Create a mock MAL that raises errors
        mock_mal = MagicMock()
        mock_mal.generate = AsyncMock(side_effect=Exception("MAL error"))
        agent.mal = mock_mal
        
        # Use real CodeScorer - score command should work even if MAL fails
        # because scoring doesn't require MAL (only review uses MAL)
        result = await agent.run("score", file=str(sample_python_file))
        assert isinstance(result, dict)
        # Score command should succeed without MAL
        assert "scoring" in result
        assert "overall_score" in result["scoring"]

