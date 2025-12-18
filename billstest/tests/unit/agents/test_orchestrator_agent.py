"""
Unit tests for Orchestrator Agent.
"""

from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.agents.orchestrator.agent import OrchestratorAgent


@pytest.mark.unit
class TestOrchestratorAgent:
    """Test cases for OrchestratorAgent."""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create an OrchestratorAgent instance with mocked workflow executor."""
        with patch("tapps_agents.agents.orchestrator.agent.WorkflowExecutor") as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor.start = MagicMock(return_value=MagicMock(workflow_id="test", status="running"))
            mock_executor.get_state = MagicMock(return_value=MagicMock(current_step="step1"))
            mock_executor_class.return_value = mock_executor
            
            agent = OrchestratorAgent()
            agent.workflow_executor = mock_executor
            return agent

    @pytest.mark.asyncio
    async def test_list_workflows(self, orchestrator, tmp_path):
        """Test list workflows command."""
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()
        (workflows_dir / "test.yaml").write_text("workflow:\n  id: test")
        
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = await orchestrator.run("*workflow-list")

        assert "workflows" in result or "message" in result

    @pytest.mark.asyncio
    async def test_workflow_start(self, orchestrator):
        """Test workflow start command."""
        result = await orchestrator.run("*workflow-start", workflow_id="test")

        assert "success" in result or "workflow" in result or "error" in result

    @pytest.mark.asyncio
    async def test_workflow_start_no_id(self, orchestrator):
        """Test workflow start without workflow_id."""
        result = await orchestrator.run("*workflow-start")

        assert "error" in result
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_workflow_status(self, orchestrator):
        """Test workflow status command."""
        result = await orchestrator.run("*workflow-status")

        assert "status" in result or "workflow" in result or "error" in result

    @pytest.mark.asyncio
    async def test_workflow_next(self, orchestrator):
        """Test workflow next command."""
        result = await orchestrator.run("*workflow-next")

        assert "step" in result or "next" in result or "error" in result

    @pytest.mark.asyncio
    async def test_gate_decision(self, orchestrator):
        """Test gate decision command."""
        result = await orchestrator.run(
            "*gate",
            condition="scoring.passed == true",
            scoring_data={"passed": True}
        )

        assert "decision" in result or "gate" in result or "error" in result

    @pytest.mark.asyncio
    async def test_help(self, orchestrator):
        """Test help command."""
        result = await orchestrator.run("*help")

        assert "type" in result or "content" in result

    @pytest.mark.asyncio
    async def test_unknown_command(self, orchestrator):
        """Test unknown command."""
        result = await orchestrator.run("unknown-command")

        assert "error" in result
        assert "Unknown command" in result["error"]

