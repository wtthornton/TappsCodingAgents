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
        """Create a DesignerAgent instance."""
        with patch("tapps_agents.agents.designer.agent.load_config"):
            agent = DesignerAgent()
            return agent

    @pytest.mark.asyncio
    async def test_design_api_success(self, designer):
        """Test designing API successfully."""
        result = await designer.run(
            "design-api", requirements="Test API", api_type="REST"
        )

        assert "success" in result
        assert result["success"] is True
        assert "api_design" in result

    @pytest.mark.asyncio
    async def test_design_api_no_requirements(self, designer):
        """Test designing API without requirements."""
        result = await designer.run("design-api", requirements="")

        assert "error" in result
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_design_data_model(self, designer):
        """Test designing data model."""
        result = await designer.run("design-data-model", requirements="Test data model")

        assert "success" in result
        assert result["success"] is True
        assert "data_model" in result

    @pytest.mark.asyncio
    async def test_design_data_model_no_requirements(self, designer):
        """Test designing data model without requirements."""
        result = await designer.run("design-data-model", requirements="")

        assert "error" in result

    @pytest.mark.asyncio
    async def test_design_ui(self, designer):
        """Test designing UI/UX."""
        result = await designer.run(
            "design-ui", feature_description="Test feature", user_stories=["Story1"]
        )

        assert "success" in result
        assert result["success"] is True
        assert "ui_design" in result

    @pytest.mark.asyncio
    async def test_design_ui_no_description(self, designer):
        """Test designing UI without description."""
        result = await designer.run("design-ui", feature_description="")

        assert "error" in result

    @pytest.mark.asyncio
    async def test_create_wireframe(self, designer):
        """Test creating wireframe."""
        result = await designer.run(
            "create-wireframe", screen_description="Test screen", wireframe_type="page"
        )

        assert "success" in result
        assert result["success"] is True
        assert "wireframe" in result

    @pytest.mark.asyncio
    async def test_create_wireframe_no_description(self, designer):
        """Test creating wireframe without description."""
        result = await designer.run("create-wireframe", screen_description="")

        assert "error" in result

    @pytest.mark.asyncio
    async def test_define_design_system(self, designer):
        """Test defining design system."""
        result = await designer.run(
            "define-design-system", project_description="Test project"
        )

        assert "success" in result
        assert result["success"] is True
        assert "design_system" in result

    @pytest.mark.asyncio
    async def test_define_design_system_no_description(self, designer):
        """Test defining design system without description."""
        result = await designer.run("define-design-system", project_description="")

        assert "error" in result

    @pytest.mark.asyncio
    async def test_help(self, designer):
        """Test help command."""
        result = await designer.run("help")

        assert "type" in result
        assert result["type"] == "help"

    @pytest.mark.asyncio
    async def test_unknown_command(self, designer):
        """Test unknown command."""
        result = await designer.run("unknown-command")

        assert "error" in result
