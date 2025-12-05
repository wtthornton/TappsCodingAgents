"""
Integration tests for ReviewerAgent.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from tapps_agents.agents.reviewer.agent import ReviewerAgent
from tests.fixtures.sample_code import SIMPLE_CODE, COMPLEX_CODE, INSECURE_CODE


@pytest.mark.integration
class TestReviewerAgent:
    """Integration tests for ReviewerAgent."""
    
    @pytest.mark.asyncio
    async def test_reviewer_initialization(self, mock_mal):
        """Test that ReviewerAgent initializes correctly."""
        reviewer = ReviewerAgent(mal=mock_mal)
        assert reviewer.agent_id == "reviewer"
        assert reviewer.agent_name == "Reviewer Agent"
        assert reviewer.mal is not None
        assert reviewer.scorer is not None
    
    @pytest.mark.asyncio
    async def test_reviewer_get_commands(self, mock_mal):
        """Test that ReviewerAgent returns correct commands."""
        reviewer = ReviewerAgent(mal=mock_mal)
        commands = reviewer.get_commands()
        
        command_names = [cmd["command"] for cmd in commands]
        assert "*help" in command_names
        assert "*review" in command_names
        assert "*score" in command_names
    
    @pytest.mark.asyncio
    async def test_reviewer_help_command(self, mock_mal):
        """Test that help command works."""
        reviewer = ReviewerAgent(mal=mock_mal)
        result = await reviewer.run("help")
        
        assert result["type"] == "help"
        assert "content" in result
        assert "Reviewer Agent" in result["content"]
    
    @pytest.mark.asyncio
    async def test_reviewer_review_command(self, mock_mal, sample_python_file: Path):
        """Test that review command works."""
        reviewer = ReviewerAgent(mal=mock_mal)
        mock_mal.generate.return_value = "This code looks good. No major issues found."
        
        result = await reviewer.run("review", file=str(sample_python_file))
        
        assert "file" in result
        assert "scoring" in result
        assert "feedback" in result
        assert "passed" in result
        assert isinstance(result["scoring"]["overall_score"], (int, float))
    
    @pytest.mark.asyncio
    async def test_reviewer_review_command_no_file(self, mock_mal):
        """Test that review command handles missing file gracefully."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
        result = await reviewer.run("review", file=None)
        
        assert "error" in result
        assert "required" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_reviewer_score_command(self, mock_mal, sample_python_file: Path):
        """Test that score command works without LLM feedback."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
        result = await reviewer.run("score", file=str(sample_python_file))
        
        assert "file" in result
        assert "scoring" in result
        assert "feedback" not in result  # Score only, no feedback
        assert isinstance(result["scoring"]["overall_score"], (int, float))
    
    @pytest.mark.asyncio
    async def test_reviewer_review_file_simple_code(self, mock_mal, tmp_path: Path):
        """Test reviewing simple code."""
        reviewer = ReviewerAgent(mal=mock_mal)
        test_file = tmp_path / "simple.py"
        test_file.write_text(SIMPLE_CODE)
        mock_mal.generate.return_value = "Simple, clean code. Good structure."
        
        result = await reviewer.review_file(test_file, include_scoring=True, include_llm_feedback=True)
        
        assert result["file"] == str(test_file)
        assert "scoring" in result
        assert "feedback" in result
        assert result["passed"] is not None
    
    @pytest.mark.asyncio
    async def test_reviewer_review_file_complex_code(self, mock_mal, tmp_path: Path):
        """Test reviewing complex code."""
        reviewer = ReviewerAgent(mal=mock_mal)
        test_file = tmp_path / "complex.py"
        test_file.write_text(COMPLEX_CODE)
        mock_mal.generate.return_value = "Complex code with nested logic. Consider refactoring."
        
        result = await reviewer.review_file(test_file, include_scoring=True, include_llm_feedback=True)
        
        assert result["file"] == str(test_file)
        assert result["scoring"]["complexity_score"] >= 0
        # Complex code might have lower scores
        assert result["scoring"]["overall_score"] >= 0
    
    @pytest.mark.asyncio
    async def test_reviewer_review_file_insecure_code(self, mock_mal, tmp_path: Path):
        """Test reviewing code with security issues."""
        reviewer = ReviewerAgent(mal=mock_mal)
        test_file = tmp_path / "insecure.py"
        test_file.write_text(INSECURE_CODE)
        mock_mal.generate.return_value = "Security issues detected: eval(), exec(), pickle.loads()"
        
        result = await reviewer.review_file(test_file, include_scoring=True, include_llm_feedback=True)
        
        assert result["file"] == str(test_file)
        # Security score should be lower
        assert result["scoring"]["security_score"] >= 0
        assert result["scoring"]["security_score"] <= 10
    
    @pytest.mark.asyncio
    async def test_reviewer_score_only_no_llm(self, mock_mal, sample_python_file: Path):
        """Test that score-only mode doesn't call LLM."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
        result = await reviewer.review_file(
            sample_python_file,
            include_scoring=True,
            include_llm_feedback=False
        )
        
        assert "scoring" in result
        assert "feedback" not in result
        # LLM should not be called
        mock_mal.generate.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_reviewer_activation(self, mock_mal, temp_project_dir: Path):
        """Test that reviewer activation works."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
        # Should not raise exception
        await reviewer.activate(temp_project_dir)
        
        # Activation should complete
    
    @pytest.mark.asyncio
    async def test_reviewer_close(self, mock_mal):
        """Test that reviewer cleanup works."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
        await reviewer.close()
        
        # MAL close should be called
        mock_mal.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reviewer_unknown_command(self, mock_mal):
        """Test that unknown commands return error."""
        reviewer = ReviewerAgent(mal=mock_mal)
        
        result = await reviewer.run("unknown_command")
        
        assert "error" in result
        assert "unknown" in result["error"].lower() or "command" in result["error"].lower()

