"""
Smoke E2E tests for agent activation lifecycle.

Tests validate that:
- Agents can be activated
- Agents can execute commands (with mocked MAL)
- Agents can be closed/cleaned up
- Multiple agents can run in sequence
"""

import pytest

from tapps_agents.core.agent_base import BaseAgent
from tapps_agents.core.mal import MAL


@pytest.mark.e2e_smoke
@pytest.mark.template_type("minimal")
class TestAgentLifecycle:
    """Test agent activation lifecycle."""

    @pytest.mark.asyncio
    async def test_agent_activation(self, e2e_project, mock_mal):
        """Test agent activation."""
        # Create a simple test agent
        class TestAgent(BaseAgent):
            def __init__(self):
                super().__init__(agent_id="test-agent", agent_name="Test Agent")
            
            async def run(self, command: str, **kwargs):
                return {"status": "success", "command": command}
        
        agent = TestAgent()
        
        # Activate agent
        await agent.activate(e2e_project)
        
        # Verify activation
        assert agent.config is not None
        assert agent.agent_id == "test-agent"
        assert agent.agent_name == "Test Agent"

    @pytest.mark.asyncio
    async def test_agent_execution(self, e2e_project, mock_mal):
        """Test agent execution with mocked MAL."""
        class TestAgent(BaseAgent):
            def __init__(self, mal: MAL):
                super().__init__(agent_id="test-agent", agent_name="Test Agent")
                self.mal = mal
            
            async def run(self, command: str, **kwargs):
                # Simulate using MAL
                if command == "test":
                    response = await self.mal.generate("test prompt")
                    return {"status": "success", "response": response}
                return {"status": "unknown_command"}
        
        agent = TestAgent(mock_mal)
        await agent.activate(e2e_project)
        
        # Execute command
        result = await agent.run("test")
        
        assert result["status"] == "success"
        assert "response" in result
        # Verify MAL was called (mocked)
        mock_mal.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_cleanup(self, e2e_project, mock_mal):
        """Test agent cleanup (close method)."""
        class TestAgent(BaseAgent):
            def __init__(self, mal: MAL):
                super().__init__(agent_id="test-agent", agent_name="Test Agent")
                self.mal = mal
            
            async def run(self, command: str, **kwargs):
                return {"status": "success"}
            
            async def close(self):
                if self.mal:
                    await self.mal.close()
        
        agent = TestAgent(mock_mal)
        await agent.activate(e2e_project)
        
        # Close agent
        await agent.close()
        
        # Verify MAL close was called
        mock_mal.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_agents_sequence(self, e2e_project, mock_mal):
        """Test that multiple agents can run in sequence."""
        class TestAgent(BaseAgent):
            def __init__(self, agent_id: str, agent_name: str):
                super().__init__(agent_id=agent_id, agent_name=agent_name)
            
            async def run(self, command: str, **kwargs):
                return {"status": "success", "agent": self.agent_id}
        
        # Create and activate multiple agents
        agent1 = TestAgent("agent1", "Agent 1")
        agent2 = TestAgent("agent2", "Agent 2")
        
        await agent1.activate(e2e_project)
        result1 = await agent1.run("test")
        
        await agent2.activate(e2e_project)
        result2 = await agent2.run("test")
        
        # Verify both agents executed successfully
        assert result1["status"] == "success"
        assert result1["agent"] == "agent1"
        assert result2["status"] == "success"
        assert result2["agent"] == "agent2"

    @pytest.mark.asyncio
    async def test_agent_contract_validation(self, e2e_project, mock_mal):
        """Test agent contract (activation state, execution results)."""
        class TestAgent(BaseAgent):
            def __init__(self):
                super().__init__(agent_id="test-agent", agent_name="Test Agent")
            
            async def run(self, command: str, **kwargs):
                return {
                    "status": "success",
                    "command": command,
                    "agent_id": self.agent_id,
                }
        
        agent = TestAgent()
        await agent.activate(e2e_project)
        
        # Verify agent contract
        assert agent.agent_id is not None
        assert agent.agent_name is not None
        assert agent.config is not None
        
        # Execute and verify result contract
        result = await agent.run("test")
        
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "success"
        assert "command" in result
        assert "agent_id" in result
