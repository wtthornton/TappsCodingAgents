"""
Unit tests for Implementer Agent.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.implementer.agent import ImplementerAgent


@pytest.mark.unit
class TestImplementerAgent:
    """Test cases for ImplementerAgent."""

    @pytest.fixture
    def implementer(self):
        """Create an ImplementerAgent instance with mocked dependencies."""
        with patch("tapps_agents.agents.implementer.agent.load_config"):
            with patch("tapps_agents.agents.implementer.agent.MAL") as mock_mal_class:
                mock_mal = MagicMock()
                mock_mal.generate = AsyncMock(return_value="def test(): pass")
                mock_mal_class.return_value = mock_mal
                
                with patch("tapps_agents.agents.implementer.agent.CodeGenerator"):
                    agent = ImplementerAgent()
                    agent.mal = mock_mal
                    agent.code_generator = MagicMock()
                    agent.code_generator.generate = AsyncMock(return_value="def test(): pass")
                    agent.reviewer = None
                    agent.expert_registry = None
                    agent.context7 = None
                    return agent

    @pytest.mark.asyncio
    async def test_implement_success(self, implementer, tmp_path):
        """Test implement command."""
        output_file = tmp_path / "output.py"
        
        result = await implementer.run(
            "implement",
            description="Create a test function",
            output_file=str(output_file)
        )

        assert "success" in result or "file" in result

    @pytest.mark.asyncio
    async def test_implement_no_description(self, implementer):
        """Test implement command without description."""
        result = await implementer.run("implement", description="")

        assert "error" in result

    @pytest.mark.asyncio
    async def test_generate_code(self, implementer):
        """Test generate code command."""
        result = await implementer.run(
            "generate-code",
            description="Create a function"
        )

        assert "success" in result or "code" in result

    @pytest.mark.asyncio
    async def test_refactor(self, implementer, tmp_path):
        """Test refactor command."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def old(): pass")
        
        result = await implementer.run(
            "refactor",
            file=str(test_file),
            instruction="Improve function name"
        )

        assert "success" in result or "refactored" in result

    @pytest.mark.asyncio
    async def test_help(self, implementer):
        """Test help command."""
        result = await implementer.run("help")

        assert "type" in result or "content" in result

    @pytest.mark.asyncio
    async def test_unknown_command(self, implementer):
        """Test unknown command."""
        result = await implementer.run("unknown-command")

        assert "error" in result
        assert "Unknown command" in result["error"]

