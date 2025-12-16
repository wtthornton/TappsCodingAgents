"""
Unit tests for Enhancer Agent.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.enhancer.agent import EnhancerAgent


@pytest.mark.unit
class TestEnhancerAgent:
    """Test cases for EnhancerAgent."""

    @pytest.fixture
    def enhancer(self):
        """Create an EnhancerAgent instance with mocked dependencies."""
        with patch("tapps_agents.agents.enhancer.agent.load_config"):
            with patch("tapps_agents.agents.enhancer.agent.MAL") as mock_mal_class:
                mock_mal = MagicMock()
                mock_mal.generate = AsyncMock(return_value="Mocked enhancement response")
                mock_mal_class.return_value = mock_mal
                
                with patch("tapps_agents.agents.enhancer.agent.AnalystAgent"):
                    agent = EnhancerAgent()
                    agent.mal = mock_mal
                    agent.analyst = MagicMock()
                    agent.analyst.run = AsyncMock(return_value={"success": True, "requirements": "test"})
                    return agent

    @pytest.mark.asyncio
    async def test_enhance_prompt_success(self, enhancer):
        """Test enhancing a prompt successfully."""
        result = await enhancer.run("enhance", prompt="Create a login page")

        assert "success" in result or "enhanced_prompt" in result
        assert enhancer.mal.generate.called or enhancer.analyst.run.called

    @pytest.mark.asyncio
    async def test_enhance_prompt_no_prompt(self, enhancer):
        """Test enhancing without prompt."""
        result = await enhancer.run("enhance", prompt="")

        assert "error" in result or "required" in result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_help(self, enhancer):
        """Test help command."""
        result = await enhancer.run("help")

        assert "type" in result
        assert result["type"] == "help"
        assert "content" in result

    @pytest.mark.asyncio
    async def test_unknown_command(self, enhancer):
        """Test unknown command."""
        result = await enhancer.run("unknown-command")

        assert "error" in result
        assert "Unknown command" in result["error"]

    @pytest.mark.asyncio
    async def test_activate(self, enhancer, tmp_path):
        """Test agent activation."""
        await enhancer.activate(tmp_path)
        
        assert enhancer.project_root == tmp_path

