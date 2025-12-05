"""
Unit tests for Architect Agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tapps_agents.agents.architect.agent import ArchitectAgent


@pytest.mark.unit
class TestArchitectAgent:
    """Test cases for ArchitectAgent."""
    
    @pytest.fixture
    def architect(self):
        """Create an ArchitectAgent instance with mocked MAL."""
        with patch('tapps_agents.agents.architect.agent.load_config'):
            with patch('tapps_agents.agents.architect.agent.MAL') as mock_mal_class:
                mock_mal = MagicMock()
                mock_mal.generate = AsyncMock(return_value="Mocked architecture response")
                mock_mal_class.return_value = mock_mal
                agent = ArchitectAgent()
                agent.mal = mock_mal
                return agent
    
    @pytest.mark.asyncio
    async def test_design_system_success(self, architect):
        """Test designing system architecture successfully."""
        result = await architect.run("design-system", requirements="Test requirements")
        
        assert "success" in result
        assert result["success"] is True
        assert "architecture" in result
    
    @pytest.mark.asyncio
    async def test_design_system_no_requirements(self, architect):
        """Test designing system without requirements."""
        result = await architect.run("design-system", requirements="")
        
        assert "error" in result
        assert "required" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_create_diagram(self, architect):
        """Test creating architecture diagram."""
        result = await architect.run("create-diagram", architecture_description="Test architecture", diagram_type="component")
        
        assert "success" in result
        assert result["success"] is True
        assert "diagram" in result
    
    @pytest.mark.asyncio
    async def test_create_diagram_no_description(self, architect):
        """Test creating diagram without description."""
        result = await architect.run("create-diagram", architecture_description="")
        
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_select_technology(self, architect):
        """Test technology selection."""
        result = await architect.run("select-technology", component_description="Database", requirements="Fast queries")
        
        assert "success" in result
        assert result["success"] is True
        assert "technology_selection" in result
    
    @pytest.mark.asyncio
    async def test_design_security(self, architect):
        """Test security architecture design."""
        result = await architect.run("design-security", system_description="Secure system")
        
        assert "success" in result
        assert result["success"] is True
        assert "security_design" in result
    
    @pytest.mark.asyncio
    async def test_design_security_no_description(self, architect):
        """Test security design without description."""
        result = await architect.run("design-security", system_description="")
        
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_define_boundaries(self, architect):
        """Test defining system boundaries."""
        result = await architect.run("define-boundaries", system_description="System description")
        
        assert "success" in result
        assert result["success"] is True
        assert "boundaries" in result
    
    @pytest.mark.asyncio
    async def test_define_boundaries_no_description(self, architect):
        """Test defining boundaries without description."""
        result = await architect.run("define-boundaries", system_description="")
        
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_help(self, architect):
        """Test help command."""
        result = await architect.run("help")
        
        assert "type" in result
        assert result["type"] == "help"
    
    @pytest.mark.asyncio
    async def test_unknown_command(self, architect):
        """Test unknown command."""
        result = await architect.run("unknown-command")
        
        assert "error" in result

