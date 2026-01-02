"""
Unit tests for Improver Agent.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from tapps_agents.agents.improver.agent import ImproverAgent
from tapps_agents.core.config import ProjectConfig

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_config():
    return ProjectConfig(
        agents={},
    )


@pytest.fixture
def improver_agent(mock_config):
    with patch(
        "tapps_agents.agents.improver.agent.load_config", return_value=mock_config
    ):
        agent = ImproverAgent(config=mock_config)
        agent.project_root = Path("/mock/project")
        return agent


@pytest.mark.asyncio
class TestImproverAgent:
    async def test_init(self, improver_agent):
        assert improver_agent.agent_id == "improver"
        assert improver_agent.agent_name == "Improver Agent"
        assert improver_agent.config is not None

    async def test_activate(self, mock_config):
        with patch(
            "tapps_agents.agents.improver.agent.load_config", return_value=mock_config
        ):
            agent = ImproverAgent(config=mock_config)
            with (
                patch.object(agent, "greet") as mock_greet,
                patch.object(agent, "run", new_callable=AsyncMock) as mock_run,
            ):
                await agent.activate()
                mock_greet.assert_called_once()
                mock_run.assert_called_once_with("help")

    async def test_refactor_success(self, improver_agent, tmp_path):
        test_file = tmp_path / "test_code.py"
        test_file.write_text("def old_code():\n    pass\n", encoding="utf-8")
        improver_agent.project_root = tmp_path
        with (
            patch.object(
                improver_agent, "get_context", new_callable=AsyncMock
            ) as mock_context,
            patch.object(improver_agent, "get_context_text", return_value=""),
        ):
            mock_context.return_value = {}
            result = await improver_agent.run("refactor", file_path=str(test_file))

        assert "message" in result or "instruction" in result

    async def test_refactor_file_not_found(self, improver_agent):
        # Use a file that doesn't exist relative to project root
        result = await improver_agent.run("refactor", file_path="does/not/exist.py")

        assert "error" in result
        assert (
            "not found" in result["error"].lower()
            or "File not found" in result["error"]
            or "outside allowed roots" in result["error"].lower()
        )

    async def test_refactor_no_file_path(self, improver_agent):
        result = await improver_agent.run("refactor")

        assert "error" in result
        assert "required" in result["error"].lower()

    async def test_optimize_success(self, improver_agent, tmp_path):
        test_file = tmp_path / "test_code.py"
        test_file.write_text("def slow_code():\n    pass\n", encoding="utf-8")
        improver_agent.project_root = tmp_path
        with (
            patch.object(
                improver_agent, "get_context", new_callable=AsyncMock
            ) as mock_context,
            patch.object(improver_agent, "get_context_text", return_value=""),
        ):
            mock_context.return_value = {}
            result = await improver_agent.run(
                "optimize", file_path=str(test_file), optimization_type="performance"
            )

        assert "message" in result or "instruction" in result

    async def test_optimize_file_not_found(self, improver_agent):
        result = await improver_agent.run("optimize", file_path="does/not/exist.py")

        assert "error" in result
        assert (
            "not found" in result["error"].lower()
            or "File not found" in result["error"]
            or "outside allowed roots" in result["error"].lower()
        )

    async def test_optimize_no_file_path(self, improver_agent):
        result = await improver_agent.run("optimize")

        assert "error" in result
        assert "required" in result["error"].lower()

    async def test_improve_quality_success(self, improver_agent, tmp_path):
        test_file = tmp_path / "test_code.py"
        test_file.write_text("def bad_code():\n    pass\n", encoding="utf-8")
        improver_agent.project_root = tmp_path
        with (
            patch.object(
                improver_agent, "get_context", new_callable=AsyncMock
            ) as mock_context,
            patch.object(improver_agent, "get_context_text", return_value=""),
        ):
            mock_context.return_value = {}
            result = await improver_agent.run(
                "improve-quality", file_path=str(test_file)
            )

        assert "message" in result or "instruction" in result

    async def test_improve_quality_file_not_found(self, improver_agent):
        result = await improver_agent.run(
            "improve-quality", file_path="does/not/exist.py"
        )

        assert "error" in result
        assert (
            "not found" in result["error"].lower()
            or "File not found" in result["error"]
            or "outside allowed roots" in result["error"].lower()
        )

    async def test_improve_quality_no_file_path(self, improver_agent):
        result = await improver_agent.run("improve-quality")

        assert "error" in result
        assert "required" in result["error"].lower()

    async def test_improve_quality_with_focus(self, improver_agent, tmp_path):
        test_file = tmp_path / "test_code.py"
        test_file.write_text("def bad_code():\n    pass\n", encoding="utf-8")
        improver_agent.project_root = tmp_path
        with (
            patch.object(
                improver_agent, "get_context", new_callable=AsyncMock
            ) as mock_context,
            patch.object(improver_agent, "get_context_text", return_value=""),
        ):
            mock_context.return_value = {}
            result = await improver_agent.run(
                "improve-quality",
                file_path=str(test_file),
                focus="security, maintainability, type-safety",
            )

        assert "message" in result or "instruction" in result
        # Verify focus is incorporated into the prompt
        if "instruction" in result:
            instruction = result["instruction"]
            if isinstance(instruction, dict) and "prompt" in instruction:
                prompt = instruction["prompt"]
                assert "security" in prompt.lower() or "maintainability" in prompt.lower()

    async def test_improve_quality_with_single_focus(self, improver_agent, tmp_path):
        test_file = tmp_path / "test_code.py"
        test_file.write_text("def bad_code():\n    pass\n", encoding="utf-8")
        improver_agent.project_root = tmp_path
        with (
            patch.object(
                improver_agent, "get_context", new_callable=AsyncMock
            ) as mock_context,
            patch.object(improver_agent, "get_context_text", return_value=""),
        ):
            mock_context.return_value = {}
            result = await improver_agent.run(
                "improve-quality", file_path=str(test_file), focus="security"
            )

        assert "message" in result or "instruction" in result

    async def test_improve_quality_without_focus(self, improver_agent, tmp_path):
        """Test that improve-quality works without focus (backward compatibility)"""
        test_file = tmp_path / "test_code.py"
        test_file.write_text("def bad_code():\n    pass\n", encoding="utf-8")
        improver_agent.project_root = tmp_path
        with (
            patch.object(
                improver_agent, "get_context", new_callable=AsyncMock
            ) as mock_context,
            patch.object(improver_agent, "get_context_text", return_value=""),
        ):
            mock_context.return_value = {}
            result = await improver_agent.run(
                "improve-quality", file_path=str(test_file)
            )

        assert "message" in result or "instruction" in result

    async def test_help(self, improver_agent):
        result = await improver_agent.run("help")

        assert "content" in result
        # Help content can be either dict or string
        if isinstance(result["content"], dict):
            # Check that help commands are in the keys
            assert any("*refactor" in key for key in result["content"].keys())
            assert any("*optimize" in key for key in result["content"].keys())
            assert any("*improve-quality" in key for key in result["content"].keys())
            assert "*help" in result["content"]
        else:
            # If it's a string, check that commands are mentioned
            content_str = str(result["content"])
            assert "*refactor" in content_str or "refactor" in content_str.lower()
            assert "*optimize" in content_str or "optimize" in content_str.lower()
            assert "*improve-quality" in content_str or "improve-quality" in content_str.lower()

    async def test_unknown_command(self, improver_agent):
        result = await improver_agent.run("unknown-command")

        assert "error" in result
        assert "Unknown command" in result["error"]

    async def test_activate_with_offline_mode(self, mock_config):
        """Test activate() accepts offline_mode parameter."""
        with patch(
            "tapps_agents.agents.improver.agent.load_config", return_value=mock_config
        ):
            agent = ImproverAgent(config=mock_config)
            with (
                patch.object(agent, "greet") as mock_greet,
                patch.object(agent, "run", new_callable=AsyncMock) as mock_run,
            ):
                # Test with offline_mode=True
                await agent.activate(offline_mode=True)
                mock_greet.assert_called_once()
                mock_run.assert_called_once_with("help")
                
                # Reset mocks
                mock_greet.reset_mock()
                mock_run.reset_mock()
                
                # Test with offline_mode=False
                await agent.activate(offline_mode=False)
                mock_greet.assert_called_once()
                mock_run.assert_called_once_with("help")

    async def test_activate_passes_offline_mode_to_base(self, mock_config):
        """Test activate() passes offline_mode to BaseAgent.activate()."""
        with patch(
            "tapps_agents.agents.improver.agent.load_config", return_value=mock_config
        ):
            agent = ImproverAgent(config=mock_config)
            with (
                patch.object(agent, "greet"),
                patch.object(agent, "run", new_callable=AsyncMock),
                patch.object(agent.__class__.__bases__[0], "activate", new_callable=AsyncMock) as mock_base_activate,
            ):
                await agent.activate(project_root=Path("/test"), offline_mode=True)
                
                # Verify BaseAgent.activate() was called with offline_mode
                mock_base_activate.assert_called_once_with(Path("/test"), offline_mode=True)

    async def test_run_handles_sync_handler(self, improver_agent):
        """Test run() correctly handles synchronous handlers (like _handle_help)."""
        # The help handler is synchronous, so run() should not await it
        result = await improver_agent.run("help")
        
        assert "type" in result or "content" in result
        # Verify it's a dict (not a coroutine)
        assert isinstance(result, dict)

    async def test_run_handles_async_handler(self, improver_agent, tmp_path):
        """Test run() correctly handles asynchronous handlers."""
        test_file = tmp_path / "test_code.py"
        test_file.write_text("def code():\n    pass\n", encoding="utf-8")
        improver_agent.project_root = tmp_path
        
        with (
            patch.object(
                improver_agent, "get_context", new_callable=AsyncMock
            ) as mock_context,
            patch.object(improver_agent, "get_context_text", return_value=""),
        ):
            mock_context.return_value = {}
            # refactor handler is async, so run() should await it
            result = await improver_agent.run("refactor", file_path=str(test_file))
            
            assert "message" in result or "instruction" in result
            assert isinstance(result, dict)