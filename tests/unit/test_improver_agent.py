"""
Unit tests for Improver Agent.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from tapps_agents.agents.improver.agent import ImproverAgent
from tapps_agents.core.config import ProjectConfig, MALConfig


@pytest.fixture
def mock_config():
    return ProjectConfig(
        mal=MALConfig(default_model="test-model", default_local_model="test-local-model"),
        agents={}
    )


@pytest.fixture
def improver_agent(mock_config):
    with patch('tapps_agents.agents.improver.agent.load_config', return_value=mock_config):
        with patch('tapps_agents.agents.improver.agent.MAL') as mock_mal_class:
            mock_mal = MagicMock()
            mock_mal.generate = AsyncMock(return_value="```python\ndef refactored_code():\n    pass\n```")
            mock_mal_class.return_value = mock_mal
            agent = ImproverAgent(config=mock_config)
            agent.mal = mock_mal
            agent.project_root = Path("/mock/project")
            return agent


@pytest.mark.asyncio
class TestImproverAgent:
    async def test_init(self, improver_agent):
        assert improver_agent.agent_id == "improver"
        assert improver_agent.agent_name == "Improver Agent"
        assert improver_agent.config is not None
        assert improver_agent.mal is not None
    
    async def test_activate(self, mock_config):
        with patch('tapps_agents.agents.improver.agent.load_config', return_value=mock_config):
            with patch('tapps_agents.agents.improver.agent.MAL') as mock_mal_class:
                mock_mal = MagicMock()
                mock_mal.generate = AsyncMock(return_value="")
                mock_mal_class.return_value = mock_mal
                agent = ImproverAgent(config=mock_config)
                agent.mal = mock_mal
                with patch.object(agent, 'greet') as mock_greet, \
                     patch.object(agent, 'run', new_callable=AsyncMock) as mock_run:
                    await agent.activate()
                    mock_greet.assert_called_once()
                    mock_run.assert_called_once_with("help")
    
    async def test_refactor_success(self, improver_agent, tmp_path):
        test_file = tmp_path / "test_code.py"
        test_file.write_text("def old_code():\n    pass\n")
        improver_agent.project_root = tmp_path
        with patch.object(improver_agent, 'get_context', new_callable=AsyncMock) as mock_context, \
             patch.object(improver_agent, 'get_context_text', return_value=""):
            mock_context.return_value = {}
            result = await improver_agent.run("refactor", file_path=str(test_file))
        
        assert "message" in result
        assert "refactored" in result
        assert result["refactored"] is True
    
    async def test_refactor_file_not_found(self, improver_agent):
        # Use a file that doesn't exist relative to project root
        result = await improver_agent.run("refactor", file_path="does/not/exist.py")
        
        assert "error" in result
        assert "not found" in result["error"].lower() or "File not found" in result["error"]
    
    async def test_refactor_no_file_path(self, improver_agent):
        result = await improver_agent.run("refactor")
        
        assert "error" in result
        assert "required" in result["error"].lower()
    
    async def test_optimize_success(self, improver_agent, tmp_path):
        test_file = tmp_path / "test_code.py"
        test_file.write_text("def slow_code():\n    pass\n")
        improver_agent.project_root = tmp_path
        with patch.object(improver_agent, 'get_context', new_callable=AsyncMock) as mock_context, \
             patch.object(improver_agent, 'get_context_text', return_value=""):
            mock_context.return_value = {}
            result = await improver_agent.run("optimize", file_path=str(test_file), optimization_type="performance")
        
        assert "message" in result
        assert "optimized" in result
        assert result["optimized"] is True
        assert result["optimization_type"] == "performance"
    
    async def test_optimize_file_not_found(self, improver_agent):
        result = await improver_agent.run("optimize", file_path="does/not/exist.py")
        
        assert "error" in result
        assert "not found" in result["error"].lower() or "File not found" in result["error"]
    
    async def test_optimize_no_file_path(self, improver_agent):
        result = await improver_agent.run("optimize")
        
        assert "error" in result
        assert "required" in result["error"].lower()
    
    async def test_improve_quality_success(self, improver_agent, tmp_path):
        test_file = tmp_path / "test_code.py"
        test_file.write_text("def bad_code():\n    pass\n")
        improver_agent.project_root = tmp_path
        with patch.object(improver_agent, 'get_context', new_callable=AsyncMock) as mock_context, \
             patch.object(improver_agent, 'get_context_text', return_value=""):
            mock_context.return_value = {}
            result = await improver_agent.run("improve-quality", file_path=str(test_file))
        
        assert "message" in result
        assert "improved" in result
        assert result["improved"] is True
    
    async def test_improve_quality_file_not_found(self, improver_agent):
        result = await improver_agent.run("improve-quality", file_path="does/not/exist.py")
        
        assert "error" in result
        assert "not found" in result["error"].lower() or "File not found" in result["error"]
    
    async def test_improve_quality_no_file_path(self, improver_agent):
        result = await improver_agent.run("improve-quality")
        
        assert "error" in result
        assert "required" in result["error"].lower()
    
    async def test_help(self, improver_agent):
        result = await improver_agent.run("help")
        
        assert "content" in result
        assert isinstance(result["content"], dict)
        # Check that help commands are in the keys
        assert any("*refactor" in key for key in result["content"].keys())
        assert any("*optimize" in key for key in result["content"].keys())
        assert any("*improve-quality" in key for key in result["content"].keys())
        assert "*help" in result["content"]
    
    async def test_unknown_command(self, improver_agent):
        result = await improver_agent.run("unknown-command")
        
        assert "error" in result
        assert "Unknown command" in result["error"]
    
    async def test_extract_code_from_response(self, improver_agent):
        # Test with Python code block
        response = "```python\ndef code():\n    pass\n```"
        code = improver_agent._extract_code_from_response(response)
        assert "def code():" in code
        
        # Test with generic code block
        response = "```\ndef code():\n    pass\n```"
        code = improver_agent._extract_code_from_response(response)
        assert "def code():" in code
        
        # Test with no code block
        response = "def code():\n    pass"
        code = improver_agent._extract_code_from_response(response)
        assert "def code():" in code

