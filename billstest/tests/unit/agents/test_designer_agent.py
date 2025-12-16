"""
Unit tests for Designer Agent.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.designer.agent import DesignerAgent


@pytest.mark.unit
class TestDesignerAgent:
    """Test cases for DesignerAgent."""

    @pytest.fixture
    def designer(self):
        """Create a DesignerAgent instance with mocked MAL."""
        with patch("tapps_agents.agents.designer.agent.load_config"):
            with patch("tapps_agents.agents.designer.agent.MAL") as mock_mal_class:
                mock_mal = MagicMock()
                mock_mal.generate = AsyncMock(return_value="Mocked design response")
                mock_mal_class.return_value = mock_mal
                
                agent = DesignerAgent()
                agent.mal = mock_mal
                agent.expert_registry = None
                agent.context7 = None
                return agent

    @pytest.mark.asyncio
    async def test_design_api_success(self, designer):
        """Test design API command."""
        result = await designer.run("design-api", requirements="Test requirements")

        assert "success" in result or "api" in result
        assert designer.mal.generate.called

    @pytest.mark.asyncio
    async def test_design_data_model(self, designer):
        """Test design data model command."""
        result = await designer.run(
            "design-data-model",
            requirements="Test requirements"
        )

        assert "success" in result or "model" in result

    @pytest.mark.asyncio
    async def test_design_ui(self, designer):
        """Test design UI command."""
        result = await designer.run("design-ui", requirements="Test requirements")

        assert "success" in result or "ui" in result

    @pytest.mark.asyncio
    async def test_create_wireframe(self, designer):
        """Test create wireframe command."""
        result = await designer.run(
            "create-wireframe",
            page_description="Login page"
        )

        assert "success" in result or "wireframe" in result

    @pytest.mark.asyncio
    async def test_define_design_system(self, designer):
        """Test define design system command."""
        result = await designer.run("define-design-system", requirements="Test")

        assert "success" in result or "design_system" in result

    @pytest.mark.asyncio
    async def test_help(self, designer):
        """Test help command."""
        result = await designer.run("help")

        assert "type" in result
        assert result["type"] == "help"
        assert "content" in result

    @pytest.mark.asyncio
    async def test_unknown_command(self, designer):
        """Test unknown command."""
        result = await designer.run("unknown-command")

        assert "error" in result
        assert "Unknown command" in result["error"]

