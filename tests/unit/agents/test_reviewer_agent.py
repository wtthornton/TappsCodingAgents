"""
Tests for Reviewer Agent with mocked LLM calls.

Tests agent initialization, command handling, and business logic
without requiring actual LLM calls.
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
    """Tests for review command."""

    @pytest.mark.asyncio
    async def test_review_command_success(self, sample_python_file, mock_mal):
        """Test review command with successful review."""
        agent = ReviewerAgent()
        agent.mal = mock_mal
        
        with patch("tapps_agents.agents.reviewer.agent.CodeScorer") as mock_scorer_class:
            mock_scorer = MagicMock()
            mock_scorer.score_file.return_value = {
                "complexity_score": 7.5,
                "security_score": 8.0,
                "maintainability_score": 9.0,
                "overall_score": 82.5,
            }
            mock_scorer_class.return_value = mock_scorer
            
            result = await agent.run("review", file=str(sample_python_file))
            
            assert "file" in result
            assert "scoring" in result
            assert result["scoring"]["overall_score"] == 82.5

    @pytest.mark.asyncio
    async def test_review_command_file_not_found(self, tmp_path):
        """Test review command with non-existent file."""
        agent = ReviewerAgent()
        non_existent = tmp_path / "nonexistent.py"
        
        result = await agent.run("review", file=str(non_existent))
        
        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_review_command_invalid_file(self, tmp_path):
        """Test review command with invalid file."""
        agent = ReviewerAgent()
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("not python code")
        
        # Should handle gracefully (may return error or attempt to process)
        result = await agent.run("review", file=str(invalid_file))
        assert isinstance(result, dict)


class TestReviewerAgentScoreCommand:
    """Tests for score command."""

    @pytest.mark.asyncio
    async def test_score_command_success(self, sample_python_file, mock_mal):
        """Test score command with successful scoring."""
        agent = ReviewerAgent()
        agent.mal = mock_mal
        
        with patch("tapps_agents.agents.reviewer.agent.CodeScorer") as mock_scorer_class:
            mock_scorer = MagicMock()
            mock_scorer.score_file.return_value = {
                "complexity_score": 7.5,
                "security_score": 8.0,
                "maintainability_score": 9.0,
                "overall_score": 82.5,
            }
            mock_scorer_class.return_value = mock_scorer
            
            result = await agent.run("score", file=str(sample_python_file))
            
            assert "file" in result
            assert "scoring" in result
            assert "overall_score" in result["scoring"]

    @pytest.mark.asyncio
    async def test_score_command_file_not_found(self, tmp_path):
        """Test score command with non-existent file."""
        agent = ReviewerAgent()
        non_existent = tmp_path / "nonexistent.py"
        
        result = await agent.run("score", file=str(non_existent))
        
        assert "error" in result


class TestReviewerAgentErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_review_command_scorer_error(self, sample_python_file, mock_mal):
        """Test review command handles scorer errors."""
        agent = ReviewerAgent()
        agent.mal = mock_mal
        
        with patch("tapps_agents.agents.reviewer.agent.CodeScorer") as mock_scorer_class:
            mock_scorer = MagicMock()
            mock_scorer.score_file.side_effect = Exception("Scorer error")
            mock_scorer_class.return_value = mock_scorer
            
            result = await agent.run("review", file=str(sample_python_file))
            
            # Should handle error gracefully
            assert isinstance(result, dict)
            # May contain error or attempt fallback

    @pytest.mark.asyncio
    async def test_review_command_mal_error(self, sample_python_file):
        """Test review command handles MAL errors."""
        agent = ReviewerAgent()
        
        # Create a mock MAL that raises errors
        mock_mal = MagicMock()
        mock_mal.generate = AsyncMock(side_effect=Exception("MAL error"))
        agent.mal = mock_mal
        
        with patch("tapps_agents.agents.reviewer.agent.CodeScorer") as mock_scorer_class:
            mock_scorer = MagicMock()
            mock_scorer.score_file.return_value = {
                "complexity_score": 7.5,
                "security_score": 8.0,
                "maintainability_score": 9.0,
                "overall_score": 82.5,
            }
            mock_scorer_class.return_value = mock_scorer
            
            # Should still work if scoring doesn't require MAL
            result = await agent.run("score", file=str(sample_python_file))
            assert isinstance(result, dict)

