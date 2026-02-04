"""
Unit tests for Ops Agent.
"""

from unittest.mock import AsyncMock, patch

import pytest

from tapps_agents.agents.ops.agent import OpsAgent
from tapps_agents.core.config import ProjectConfig

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_config():
    return ProjectConfig(
        agents={},
    )


@pytest.fixture
def ops_agent(mock_config):
    with patch("tapps_agents.agents.ops.agent.load_config", return_value=mock_config):
        agent = OpsAgent(config=mock_config)
        return agent


@pytest.mark.asyncio
class TestOpsAgent:
    async def test_init(self, ops_agent):
        assert ops_agent.agent_id == "ops"
        assert ops_agent.agent_name == "Ops Agent"
        assert ops_agent.config is not None

    async def test_activate(self, ops_agent):
        with (
            patch.object(ops_agent, "greet") as mock_greet,
            patch.object(ops_agent, "run", new_callable=AsyncMock) as mock_run,
        ):
            await ops_agent.activate()
            mock_greet.assert_called_once()
            mock_run.assert_called_once_with("help")

    async def test_security_scan_file(self, ops_agent, tmp_path):
        test_file = tmp_path / "test_code.py"
        test_file.write_text("def vulnerable_code():\n    pass\n", encoding="utf-8")
        ops_agent.project_root = tmp_path

        result = await ops_agent.run("security-scan", target=str(test_file))

        assert "message" in result or "instruction" in result

    async def test_security_scan_directory(self, ops_agent, tmp_path):
        ops_agent.project_root = tmp_path
        (tmp_path / "test.py").write_text("code", encoding="utf-8")

        result = await ops_agent.run("security-scan", target=str(tmp_path))

        assert "message" in result or "instruction" in result

    async def test_security_scan_default_target(self, ops_agent, tmp_path):
        ops_agent.project_root = tmp_path
        result = await ops_agent.run("security-scan")

        assert "message" in result or "target" in result

    async def test_compliance_check_general(self, ops_agent, tmp_path):
        ops_agent.project_root = tmp_path
        result = await ops_agent.run("compliance-check", compliance_type="general")

        assert "message" in result or "instruction" in result

    async def test_compliance_check_gdpr(self, ops_agent, tmp_path):
        ops_agent.project_root = tmp_path
        result = await ops_agent.run("compliance-check", compliance_type="GDPR")

        assert "message" in result or "instruction" in result

    async def test_deploy_local(self, ops_agent, tmp_path):
        ops_agent.project_root = tmp_path
        result = await ops_agent.run("deploy", target="local")

        assert "message" in result or "instruction" in result

    async def test_deploy_staging(self, ops_agent, tmp_path):
        ops_agent.project_root = tmp_path
        result = await ops_agent.run(
            "deploy", target="staging", environment="staging-env"
        )

        assert "message" in result or "instruction" in result

    async def test_infrastructure_setup_docker(self, ops_agent, tmp_path):
        ops_agent.project_root = tmp_path

        result = await ops_agent.run(
            "infrastructure-setup", infrastructure_type="docker"
        )

        assert "message" in result or "instruction" in result

    async def test_infrastructure_setup_unsupported(self, ops_agent):
        result = await ops_agent.run(
            "infrastructure-setup", infrastructure_type="kubernetes"
        )

        assert "message" in result or "status" in result

    async def test_help(self, ops_agent):
        result = await ops_agent.run("help")

        assert "content" in result
        # Help content can be either dict or string
        if isinstance(result["content"], dict):
            # Check that help commands are in the keys
            assert any("*security-scan" in key for key in result["content"].keys())
            assert any("*compliance-check" in key for key in result["content"].keys())
            assert any("*deploy" in key for key in result["content"].keys())
            assert any("*infrastructure-setup" in key for key in result["content"].keys())
            assert "*help" in result["content"]
        else:
            # If it's a string, check that commands are mentioned
            content_str = str(result["content"])
            assert "*security-scan" in content_str or "security-scan" in content_str.lower()
            assert "*compliance-check" in content_str or "compliance-check" in content_str.lower()
            assert "*deploy" in content_str or "deploy" in content_str.lower()
            assert "*infrastructure-setup" in content_str or "infrastructure-setup" in content_str.lower()

    async def test_unknown_command(self, ops_agent):
        result = await ops_agent.run("unknown-command")

        assert "error" in result
        assert "Unknown command" in result["error"]
