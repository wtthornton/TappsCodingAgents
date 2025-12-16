"""
Unit tests for Architect Agent.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.architect.agent import ArchitectAgent


@pytest.mark.unit
class TestArchitectAgent:
    """Test cases for ArchitectAgent."""

    @pytest.fixture
    def architect(self):
        """Create an ArchitectAgent instance with mocked MAL."""
        with patch("tapps_agents.agents.architect.agent.load_config"):
            with patch("tapps_agents.agents.architect.agent.MAL") as mock_mal_class:
                mock_mal = MagicMock()
                mock_mal.generate = AsyncMock(return_value="Mocked architecture response")
                mock_mal_class.return_value = mock_mal
                
                agent = ArchitectAgent()
                agent.mal = mock_mal
                agent.expert_registry = None
                agent.context7 = None
                return agent

    @pytest.mark.asyncio
    async def test_design_system_success(self, architect):
        """Test design system command."""
        result = await architect.run("design-system", requirements="Test requirements")

        assert "success" in result or "architecture" in result
        assert architect.mal.generate.called

    @pytest.mark.asyncio
    async def test_create_diagram(self, architect):
        """Test create diagram command."""
        result = await architect.run(
            "create-diagram",
            architecture_description="Test architecture",
            diagram_type="component"
        )

        assert "success" in result or "diagram" in result

    @pytest.mark.asyncio
    async def test_select_technology(self, architect):
        """Test select technology command."""
        result = await architect.run(
            "select-technology",
            component_description="Database",
            requirements="High performance"
        )

        assert "success" in result or "technology" in result

    @pytest.mark.asyncio
    async def test_design_security(self, architect):
        """Test design security command."""
        result = await architect.run(
            "design-security",
            system_description="Test system"
        )

        assert "success" in result or "security" in result

    @pytest.mark.asyncio
    async def test_define_boundaries(self, architect):
        """Test define boundaries command."""
        result = await architect.run(
            "define-boundaries",
            system_description="Test system"
        )

        assert "success" in result or "boundaries" in result

    @pytest.mark.asyncio
    async def test_help(self, architect):
        """Test help command."""
        result = await architect.run("help")

        assert "type" in result
        assert result["type"] == "help"
        assert "content" in result

    @pytest.mark.asyncio
    async def test_unknown_command(self, architect):
        """Test unknown command."""
        result = await architect.run("unknown-command")

        assert "error" in result
        assert "Unknown command" in result["error"]

