"""
Unit tests for Improver Agent.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.improver.agent import ImproverAgent


@pytest.mark.unit
class TestImproverAgent:
    """Test cases for ImproverAgent."""

    @pytest.fixture
    def improver(self, tmp_path):
        """Create an ImproverAgent instance with mocked MAL."""
        with patch("tapps_agents.agents.improver.agent.load_config"):
            with patch("tapps_agents.agents.improver.agent.MAL") as mock_mal_class:
                mock_mal = MagicMock()
                mock_mal.generate = AsyncMock(return_value="Improved code")
                mock_mal_class.return_value = mock_mal
                
                agent = ImproverAgent(mal=mock_mal)
                agent.project_root = tmp_path
                return agent

    @pytest.mark.asyncio
    async def test_refactor_success(self, improver, tmp_path):
        """Test refactor command."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def old(): pass")
        
        result = await improver.run(
            "refactor",
            file_path=str(test_file),
            instruction="Improve code"
        )

        assert "success" in result or "refactored" in result

    @pytest.mark.asyncio
    async def test_refactor_no_file(self, improver):
        """Test refactor command without file."""
        result = await improver.run("refactor", file_path="")

        assert "error" in result
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_refactor_file_not_found(self, improver):
        """Test refactor command with non-existent file."""
        result = await improver.run(
            "refactor",
            file_path="/nonexistent/file.py"
        )

        assert "error" in result
        # File may be reported as "not found" or "outside allowed roots"
        assert "not found" in result["error"].lower() or "outside allowed roots" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_optimize_performance(self, improver, tmp_path):
        """Test optimize performance command."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def slow(): pass")
        
        result = await improver.run(
            "optimize",
            file_path=str(test_file),
            optimization_type="performance"
        )

        assert "success" in result or "optimized" in result

    @pytest.mark.asyncio
    async def test_improve_quality(self, improver, tmp_path):
        """Test improve quality command."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def bad(): pass")
        
        result = await improver.run(
            "improve-quality",
            file_path=str(test_file)
        )

        assert "success" in result or "improved" in result

    @pytest.mark.asyncio
    async def test_help(self, improver):
        """Test help command."""
        result = await improver.run("help")

        assert "type" in result or "content" in result

    @pytest.mark.asyncio
    async def test_unknown_command(self, improver):
        """Test unknown command."""
        result = await improver.run("unknown-command")

        assert "error" in result
        assert "Unknown command" in result["error"]

