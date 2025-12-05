"""
Unit tests for Analyst Agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tapps_agents.agents.analyst.agent import AnalystAgent


@pytest.mark.unit
class TestAnalystAgent:
    """Test cases for AnalystAgent."""
    
    @pytest.fixture
    def analyst(self):
        """Create an AnalystAgent instance with mocked MAL."""
        with patch('tapps_agents.agents.analyst.agent.load_config'):
            with patch('tapps_agents.agents.analyst.agent.MAL') as mock_mal_class:
                mock_mal = MagicMock()
                mock_mal.generate = AsyncMock(return_value="Mocked analysis response")
                mock_mal_class.return_value = mock_mal
                agent = AnalystAgent()
                agent.mal = mock_mal
                return agent
    
    @pytest.mark.asyncio
    async def test_gather_requirements_success(self, analyst):
        """Test gathering requirements successfully."""
        result = await analyst.run("gather-requirements", description="Test requirement")
        
        assert "success" in result
        assert result["success"] is True
        assert "requirements" in result
        assert analyst.mal.generate.called
    
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
        result = await analyst.run("gather-requirements", description="Test", output_file=output_file)
        
        assert result["success"] is True
        assert "output_file" in result["requirements"]
    
    @pytest.mark.asyncio
    async def test_analyze_stakeholders(self, analyst):
        """Test stakeholder analysis."""
        result = await analyst.run("analyze-stakeholders", description="Test project", stakeholders=["PM", "Dev"])
        
        assert "success" in result
        assert result["success"] is True
        assert "analysis" in result
    
    @pytest.mark.asyncio
    async def test_research_technology(self, analyst):
        """Test technology research."""
        result = await analyst.run("research-technology", requirement="Need database", criteria=["performance"])
        
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
        result = await analyst.run("competitive-analysis", product_description="My product", competitors=["Competitor1"])
        
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

