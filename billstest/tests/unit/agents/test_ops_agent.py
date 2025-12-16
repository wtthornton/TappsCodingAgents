"""
Unit tests for Ops Agent.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.ops.agent import OpsAgent


@pytest.mark.unit
class TestOpsAgent:
    """Test cases for OpsAgent."""

    @pytest.fixture
    def ops(self, tmp_path):
        """Create an OpsAgent instance with mocked MAL."""
        with patch("tapps_agents.agents.ops.agent.load_config"):
            with patch("tapps_agents.agents.ops.agent.MAL") as mock_mal_class:
                mock_mal = MagicMock()
                mock_mal.generate = AsyncMock(return_value="Mocked ops response")
                mock_mal_class.return_value = mock_mal
                
                agent = OpsAgent(project_root=tmp_path)
                agent.mal = mock_mal
                agent.expert_registry = None
                return agent

    @pytest.mark.asyncio
    async def test_security_scan_success(self, ops, tmp_path):
        """Test security scan command."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")
        
        result = await ops.run("security-scan", target=str(test_file))

        assert "success" in result or "issues" in result or "scan" in result

    @pytest.mark.asyncio
    async def test_security_scan_invalid_target(self, ops):
        """Test security scan with invalid target."""
        result = await ops.run("security-scan", target="/nonexistent/path")

        assert "error" in result

    @pytest.mark.asyncio
    async def test_dependency_audit(self, ops, tmp_path):
        """Test dependency audit command."""
        result = await ops.run("dependency-audit")

        assert "success" in result or "dependencies" in result or "audit" in result

    @pytest.mark.asyncio
    async def test_compliance_check(self, ops):
        """Test compliance check command."""
        result = await ops.run("compliance-check", standard="GDPR")

        assert "success" in result or "compliance" in result or "check" in result

    @pytest.mark.asyncio
    async def test_deployment_plan(self, ops):
        """Test deployment plan command."""
        result = await ops.run("deployment-plan", environment="production")

        assert "success" in result or "plan" in result or "deployment" in result

    @pytest.mark.asyncio
    async def test_help(self, ops):
        """Test help command."""
        result = await ops.run("help")

        assert "type" in result or "content" in result

    @pytest.mark.asyncio
    async def test_unknown_command(self, ops):
        """Test unknown command."""
        result = await ops.run("unknown-command")

        assert "error" in result
        assert "Unknown command" in result["error"]

