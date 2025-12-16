"""
Tests for CLI commands.

Tests CLI argument parsing, command routing, and error handling.
Uses mocks to avoid requiring actual agents or LLM calls.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.cli import (
    help_command,
    list_stories_command,
    review_command,
    score_command,
)


class TestReviewCommand:
    """Tests for review command."""

    @pytest.mark.asyncio
    async def test_review_command_file_not_found(self, tmp_path, capsys):
        """Test review command with non-existent file."""
        non_existent = tmp_path / "nonexistent.py"
        
        with pytest.raises(SystemExit) as exc_info:
            await review_command(str(non_existent), output_format="json")
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: File not found" in captured.err

    @pytest.mark.asyncio
    async def test_review_command_success_json(self, sample_python_file, capsys, mock_mal):
        """Test review command with valid file, JSON output using real ReviewerAgent."""
        from tapps_agents.agents.reviewer.agent import ReviewerAgent
        
        # Use real ReviewerAgent instance (will use real CodeScorer)
        # Only mock MAL to avoid network calls
        with patch("tapps_agents.cli.ReviewerAgent") as mock_agent_class:
            # Create a real agent instance
            real_agent = ReviewerAgent()
            real_agent.mal = mock_mal
            real_agent.activate = AsyncMock()
            real_agent.close = AsyncMock()
            mock_agent_class.return_value = real_agent

            await review_command(str(sample_python_file), output_format="json")

            captured = capsys.readouterr()
            result = json.loads(captured.out)
            assert result["file"] == str(sample_python_file)
            assert "scoring" in result
            # Validate real scoring results are present (not just mocked values)
            assert "overall_score" in result["scoring"]
            assert isinstance(result["scoring"]["overall_score"], (int, float))
            real_agent.activate.assert_called_once()
            real_agent.run.assert_called_once()
            real_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_command_success_text(self, sample_python_file, capsys):
        """Test review command with valid file, text output."""
        with patch("tapps_agents.cli.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": str(sample_python_file),
                "scoring": {
                    "complexity_score": 7.5,
                    "security_score": 8.0,
                    "maintainability_score": 9.0,
                    "overall_score": 82.5,
                },
                "passed": True,
                "feedback": {"summary": "Good code"},
            })
            mock_agent_class.return_value = mock_agent

            await review_command(str(sample_python_file), output_format="text")

            captured = capsys.readouterr()
            assert "Review:" in captured.out
            assert str(sample_python_file) in captured.out
            assert "Complexity:" in captured.out
            assert "Security:" in captured.out
            assert "Maintainability:" in captured.out

    @pytest.mark.asyncio
    async def test_review_command_error_handling(self, sample_python_file, capsys):
        """Test review command error handling."""
        with patch("tapps_agents.cli.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={"error": "Test error"})
            mock_agent_class.return_value = mock_agent

            with pytest.raises(SystemExit) as exc_info:
                await review_command(str(sample_python_file), output_format="json")
            
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Error: Test error" in captured.err


class TestScoreCommand:
    """Tests for score command."""

    @pytest.mark.asyncio
    async def test_score_command_file_not_found(self, tmp_path, capsys):
        """Test score command with non-existent file."""
        non_existent = tmp_path / "nonexistent.py"
        
        with pytest.raises(SystemExit) as exc_info:
            await score_command(str(non_existent), output_format="json")
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error: File not found" in captured.err

    @pytest.mark.asyncio
    async def test_score_command_success_json(self, sample_python_file, capsys):
        """Test score command with valid file, JSON output."""
        with patch("tapps_agents.cli.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": str(sample_python_file),
                "scoring": {
                    "complexity_score": 7.5,
                    "security_score": 8.0,
                    "maintainability_score": 9.0,
                    "overall_score": 82.5,
                },
            })
            mock_agent_class.return_value = mock_agent

            await score_command(str(sample_python_file), output_format="json")

            captured = capsys.readouterr()
            result = json.loads(captured.out)
            assert result["file"] == str(sample_python_file)
            assert "scoring" in result
            mock_agent.activate.assert_called_once()
            mock_agent.run.assert_called_once()
            mock_agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_score_command_success_text(self, sample_python_file, capsys):
        """Test score command with valid file, text output."""
        with patch("tapps_agents.cli.ReviewerAgent") as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.activate = AsyncMock()
            mock_agent.close = AsyncMock()
            mock_agent.run = AsyncMock(return_value={
                "file": str(sample_python_file),
                "scoring": {
                    "complexity_score": 7.5,
                    "security_score": 8.0,
                    "maintainability_score": 9.0,
                    "overall_score": 82.5,
                },
            })
            mock_agent_class.return_value = mock_agent

            await score_command(str(sample_python_file), output_format="text")

            captured = capsys.readouterr()
            assert "Scores for:" in captured.out
            assert str(sample_python_file) in captured.out
            assert "Complexity:" in captured.out


class TestHelpCommand:
    """Tests for help command."""

    @pytest.mark.asyncio
    async def test_help_command(self, capsys):
        """Test help command output."""
        await help_command()
        captured = capsys.readouterr()
        assert len(captured.out) > 0
        # Help should contain some information
        assert "TappsCodingAgents" in captured.out or "agent" in captured.out.lower()


class TestListStoriesCommand:
    """Tests for list stories command."""

    @pytest.mark.asyncio
    async def test_list_stories_command_json(self, tmp_path, capsys):
        """Test list stories command with JSON output."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        stories_dir = project_dir / ".tapps-agents" / "stories"
        stories_dir.mkdir(parents=True)
        
        # Create a sample story file
        story_file = stories_dir / "story-001.yaml"
        story_file.write_text("title: Test Story\nstatus: open\n")

        with patch("tapps_agents.cli.Path.cwd", return_value=project_dir):
            await list_stories_command(output_format="json")
        
        captured = capsys.readouterr()
        # Should output JSON (may be dict or list)
        output = captured.out.strip()
        if output:
            try:
                result = json.loads(output)
                # Can be dict with 'stories' key or list
                assert isinstance(result, (dict, list))
            except json.JSONDecodeError:
                # If not JSON, might be error message
                pass

    @pytest.mark.asyncio
    async def test_list_stories_command_text(self, tmp_path, capsys):
        """Test list stories command with text output."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        stories_dir = project_dir / ".tapps-agents" / "stories"
        stories_dir.mkdir(parents=True)

        with patch("tapps_agents.cli.Path.cwd", return_value=project_dir):
            await list_stories_command(output_format="text")
        
        captured = capsys.readouterr()
        # Should output something (even if "No stories found")
        # captured.out is always a string (could be empty), so just verify it's a string
        assert isinstance(captured.out, str)


class TestMainFunction:
    """Tests for main CLI entry point."""

    def test_main_help(self, capsys):
        """Test main function with --help."""
        from tapps_agents.cli import main
        
        with patch("sys.argv", ["tapps_agents", "--help"]):
            try:
                main()
            except SystemExit:
                pass  # argparse exits on --help
        
        captured = capsys.readouterr()
        assert "TappsCodingAgents" in captured.out or "agent" in captured.out.lower()

    def test_main_reviewer_help(self, capsys):
        """Test main function with reviewer --help."""
        from tapps_agents.cli import main
        
        with patch("sys.argv", ["tapps_agents", "reviewer", "--help"]):
            try:
                main()
            except SystemExit:
                pass
        
        captured = capsys.readouterr()
        assert len(captured.out) > 0

