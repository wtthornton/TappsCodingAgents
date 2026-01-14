"""
Unit tests for Analyst Agent.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.analyst.agent import AnalystAgent


@pytest.mark.unit
class TestAnalystAgent:
    """Test cases for AnalystAgent."""

    @pytest.fixture
    def analyst(self):
        """Create an AnalystAgent instance."""
        with patch("tapps_agents.agents.analyst.agent.load_config"):
            agent = AnalystAgent()
            return agent

    @pytest.mark.asyncio
    async def test_gather_requirements_success(self, analyst):
        """Test gathering requirements successfully."""
        result = await analyst.run(
            "gather-requirements", description="Test requirement"
        )

        assert "success" in result
        assert result["success"] is True
        assert "requirements" in result

    @pytest.mark.asyncio
    async def test_gather_requirements_no_description(self, analyst):
        """Test gathering requirements without description."""
        result = await analyst.run("gather-requirements", description="")

        assert "error" in result
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_gather_requirements_with_output_file(self, analyst, tmp_path):
        """Test gathering requirements with output file."""
        output_file = str(tmp_path / "requirements.json")
        result = await analyst.run(
            "gather-requirements", description="Test", output_file=output_file
        )

        assert result["success"] is True
        assert "output_file" in result["requirements"]

    @pytest.mark.asyncio
    async def test_analyze_stakeholders(self, analyst):
        """Test stakeholder analysis."""
        result = await analyst.run(
            "analyze-stakeholders",
            description="Test project",
            stakeholders=["PM", "Dev"],
        )

        assert "success" in result
        assert result["success"] is True
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_research_technology(self, analyst):
        """Test technology research."""
        result = await analyst.run(
            "research-technology", requirement="Need database", criteria=["performance"]
        )

        assert "success" in result
        assert result["success"] is True
        assert "research" in result

    @pytest.mark.asyncio
    async def test_estimate_effort(self, analyst):
        """Test effort estimation."""
        result = await analyst.run("estimate-effort", feature_description="New feature")

        assert "success" in result
        assert result["success"] is True
        assert "estimate" in result

    @pytest.mark.asyncio
    async def test_assess_risk(self, analyst):
        """Test risk assessment."""
        result = await analyst.run("assess-risk", feature_description="Risky feature")

        assert "success" in result
        assert result["success"] is True
        assert "risk_assessment" in result

    @pytest.mark.asyncio
    async def test_competitive_analysis(self, analyst):
        """Test competitive analysis."""
        result = await analyst.run(
            "competitive-analysis",
            product_description="My product",
            competitors=["Competitor1"],
        )

        assert "success" in result
        assert result["success"] is True
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_help(self, analyst):
        """Test help command."""
        result = await analyst.run("help")

        assert "type" in result
        assert result["type"] == "help"
        assert "content" in result

    @pytest.mark.asyncio
    async def test_unknown_command(self, analyst):
        """Test unknown command."""
        result = await analyst.run("unknown-command")

        assert "error" in result
        assert "Unknown command" in result["error"]

    @pytest.mark.asyncio
    async def test_gather_requirements_generates_markdown(self, analyst, tmp_path):
        """Test that gather-requirements generates markdown document in CLI mode."""
        output_file = str(tmp_path / "requirements.md")
        
        # Mock runtime mode to be CLI (not Cursor)
        with patch("tapps_agents.agents.analyst.agent.is_cursor_mode", return_value=False):
            with patch("tapps_agents.agents.analyst.agent.MAL") as mock_mal_class:
                mock_mal = AsyncMock()
                mock_mal.generate = AsyncMock(return_value='{"functional_requirements": ["User can login"], "non_functional_requirements": ["Secure"], "technical_constraints": [], "assumptions": [], "open_questions": []}')
                mock_mal_class.return_value = mock_mal
                
                with patch.object(analyst, "activate", new_callable=AsyncMock):
                    result = await analyst.run(
                        "gather-requirements",
                        description="Add user authentication",
                        output_file=output_file,
                    )

        assert result["success"] is True
        assert "markdown" in result["requirements"]
        assert "# Requirements:" in result["requirements"]["markdown"]
        assert "Functional Requirements" in result["requirements"]["markdown"]
        
        # Verify file was created
        output_path = Path(output_file)
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "# Requirements:" in content

    @pytest.mark.asyncio
    async def test_format_requirements_markdown(self, analyst):
        """Test _format_requirements_markdown method."""
        requirements_data = {
            "functional_requirements": [
                "User can login",
                "User can logout",
            ],
            "non_functional_requirements": [
                "Secure authentication",
            ],
            "technical_constraints": [
                "Must use OAuth2",
            ],
            "assumptions": [
                "Users have email addresses",
            ],
            "open_questions": [
                "Should we support social login?",
            ],
        }
        
        markdown = analyst._format_requirements_markdown(
            description="Add user authentication",
            context="Existing FastAPI app",
            requirements_data=requirements_data,
        )
        
        assert "# Requirements: Add user authentication" in markdown
        assert "## Context" in markdown
        assert "Existing FastAPI app" in markdown
        assert "## Functional Requirements" in markdown
        assert "1. User can login" in markdown
        assert "2. User can logout" in markdown
        assert "## Non-Functional Requirements" in markdown
        assert "1. Secure authentication" in markdown
        assert "## Technical Constraints" in markdown
        assert "1. Must use OAuth2" in markdown
        assert "## Assumptions" in markdown
        assert "1. Users have email addresses" in markdown
        assert "## Open Questions" in markdown
        assert "1. Should we support social login?" in markdown

    @pytest.mark.asyncio
    async def test_format_requirements_markdown_empty_sections(self, analyst):
        """Test _format_requirements_markdown with empty sections."""
        requirements_data = {
            "functional_requirements": [],
            "non_functional_requirements": [],
            "technical_constraints": [],
            "assumptions": [],
            "open_questions": [],
        }
        
        markdown = analyst._format_requirements_markdown(
            description="Test feature",
            context="",
            requirements_data=requirements_data,
        )
        
        assert "# Requirements: Test feature" in markdown
        assert "## Overview" in markdown
        # Empty sections should not appear
        assert "## Functional Requirements" not in markdown
        assert "## Non-Functional Requirements" not in markdown

    @pytest.mark.asyncio
    async def test_format_requirements_markdown_dict_format(self, analyst):
        """Test _format_requirements_markdown handles dict format requirements."""
        requirements_data = {
            "functional_requirements": [
                {"requirement": "User can login"},
                {"description": "User can logout"},
            ],
            "non_functional_requirements": [
                "Simple string",
                {"requirement": "Secure"},
            ],
        }
        
        markdown = analyst._format_requirements_markdown(
            description="Test",
            context="",
            requirements_data=requirements_data,
        )
        
        assert "1. User can login" in markdown
        assert "2. User can logout" in markdown
        assert "1. Simple string" in markdown
        assert "2. Secure" in markdown