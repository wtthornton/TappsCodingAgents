"""
Unit tests for Ops Agent.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.ops.agent import OpsAgent
from tapps_agents.core.config import MALConfig, ProjectConfig

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_config():
    return ProjectConfig(
        mal=MALConfig(
            default_model="test-model", default_local_model="test-local-model"
        ),
        agents={},
    )


@pytest.fixture
def ops_agent(mock_config):
    with patch("tapps_agents.agents.ops.agent.load_config", return_value=mock_config):
        with patch("tapps_agents.agents.ops.agent.MAL") as mock_mal_class:
            mock_mal = MagicMock()
            mock_scan_response = json.dumps(
                {
                    "issues": [
                        {
                            "severity": "high",
                            "type": "sql_injection",
                            "description": "Potential SQL injection",
                            "line": 10,
                        }
                    ]
                }
            )
            mock_compliance_response = json.dumps(
                {
                    "compliance_status": "compliant",
                    "checks": [
                        {
                            "check": "Documentation",
                            "status": "pass",
                            "message": "README found",
                        }
                    ],
                }
            )
            mock_deploy_response = json.dumps(
                {
                    "steps": [
                        {
                            "step": 1,
                            "action": "Install dependencies",
                            "command": "pip install -r requirements.txt",
                        }
                    ],
                    "rollback_steps": [],
                }
            )

            def mock_generate_side_effect(prompt):
                if "security" in prompt.lower():
                    return mock_scan_response
                elif "compliance" in prompt.lower():
                    return mock_compliance_response
                elif "deploy" in prompt.lower() or "deployment" in prompt.lower():
                    return mock_deploy_response
                elif "docker" in prompt.lower():
                    return "FROM python:3.9\nWORKDIR /app\nCOPY . ."
                return "{}"

            mock_mal.generate = AsyncMock(side_effect=mock_generate_side_effect)
            mock_mal_class.return_value = mock_mal
            agent = OpsAgent(config=mock_config)
            agent.mal = mock_mal
            return agent


@pytest.mark.asyncio
class TestOpsAgent:
    async def test_init(self, ops_agent):
        assert ops_agent.agent_id == "ops"
        assert ops_agent.agent_name == "Ops Agent"
        assert ops_agent.config is not None
        assert ops_agent.mal is not None

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
        test_file.write_text("def vulnerable_code():\n    pass\n")
        ops_agent.project_root = tmp_path

        result = await ops_agent.run("security-scan", target=str(test_file))

        assert "message" in result
        assert "issues" in result
        assert "issue_count" in result
        assert isinstance(result["issues"], list)

    async def test_security_scan_directory(self, ops_agent, tmp_path):
        ops_agent.project_root = tmp_path
        (tmp_path / "test.py").write_text("code")

        result = await ops_agent.run("security-scan", target=str(tmp_path))

        assert "message" in result
        assert "issues" in result
        assert isinstance(result["issues"], list)

    async def test_security_scan_default_target(self, ops_agent, tmp_path):
        ops_agent.project_root = tmp_path
        result = await ops_agent.run("security-scan")

        assert "message" in result
        assert "target" in result

    async def test_compliance_check_general(self, ops_agent, tmp_path):
        ops_agent.project_root = tmp_path
        result = await ops_agent.run("compliance-check", compliance_type="general")

        assert "message" in result
        assert "compliance_type" in result
        assert "checks" in result
        assert isinstance(result["checks"], list)

    async def test_compliance_check_gdpr(self, ops_agent, tmp_path):
        ops_agent.project_root = tmp_path
        result = await ops_agent.run("compliance-check", compliance_type="GDPR")

        assert "message" in result
        assert "compliance_type" in result
        assert result["compliance_type"] == "GDPR"

    async def test_deploy_local(self, ops_agent, tmp_path):
        ops_agent.project_root = tmp_path
        result = await ops_agent.run("deploy", target="local")

        assert "message" in result
        assert "target" in result
        assert result["target"] == "local"
        assert "deployment_plan" in result

    async def test_deploy_staging(self, ops_agent, tmp_path):
        ops_agent.project_root = tmp_path
        result = await ops_agent.run(
            "deploy", target="staging", environment="staging-env"
        )

        assert "message" in result
        assert "target" in result
        assert result["target"] == "staging"
        assert "environment" in result

    async def test_infrastructure_setup_docker(self, ops_agent, tmp_path):
        ops_agent.project_root = tmp_path

        result = await ops_agent.run(
            "infrastructure-setup", infrastructure_type="docker"
        )

        assert "message" in result
        assert "infrastructure_type" in result
        assert result["infrastructure_type"] == "docker"
        assert "status" in result

    async def test_infrastructure_setup_unsupported(self, ops_agent):
        result = await ops_agent.run(
            "infrastructure-setup", infrastructure_type="kubernetes"
        )

        assert "message" in result
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_help(self, ops_agent):
        result = await ops_agent.run("help")

        assert "content" in result
        assert isinstance(result["content"], dict)
        # Check that help commands are in the keys
        assert any("*security-scan" in key for key in result["content"].keys())
        assert any("*compliance-check" in key for key in result["content"].keys())
        assert any("*deploy" in key for key in result["content"].keys())
        assert any("*infrastructure-setup" in key for key in result["content"].keys())
        assert "*help" in result["content"]

    async def test_unknown_command(self, ops_agent):
        result = await ops_agent.run("unknown-command")

        assert "error" in result
        assert "Unknown command" in result["error"]
