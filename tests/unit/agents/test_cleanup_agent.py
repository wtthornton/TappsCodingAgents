"""
Unit tests for Cleanup Agent.

Tests agent initialization, command handling, analysis, planning, and execution.
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.cleanup.agent import CleanupAgent

pytestmark = pytest.mark.unit


class TestCleanupAgentInitialization:
    """Tests for CleanupAgent initialization."""

    @patch("tapps_agents.agents.cleanup.agent.load_config")
    def test_cleanup_agent_init(self, mock_load_config):
        """Test CleanupAgent initialization."""
        mock_config = MagicMock()
        mock_config.agents = MagicMock()
        mock_config.agents.cleanup_agent = MagicMock()
        mock_config.agents.cleanup_agent.dry_run_default = True
        mock_config.agents.cleanup_agent.backup_enabled = True
        mock_config.agents.cleanup_agent.interactive_mode = True
        mock_load_config.return_value = mock_config

        agent = CleanupAgent()
        assert agent.agent_id == "cleanup-agent"
        assert agent.agent_name == "Cleanup Agent"
        assert agent.config is not None
        assert agent.dry_run_default is True
        assert agent.backup_enabled is True

    @pytest.mark.asyncio
    async def test_cleanup_agent_activate(self):
        """Test CleanupAgent activation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            agent = CleanupAgent()
            await agent.activate(temp_path)

            assert agent.config is not None

    @pytest.mark.asyncio
    async def test_cleanup_agent_get_commands(self):
        """Test CleanupAgent command list."""
        agent = CleanupAgent()
        commands = agent.get_commands()

        assert isinstance(commands, list)
        assert len(commands) > 0
        command_names = [cmd["command"] for cmd in commands]
        assert "*analyze" in command_names
        assert "*plan" in command_names
        assert "*execute" in command_names
        assert "*run" in command_names


class TestCleanupAgentAnalyzeCommand:
    """Tests for analyze command."""

    @pytest.mark.asyncio
    async def test_analyze_command_path_not_exists(self):
        """Test analyze command with non-existent path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            agent = CleanupAgent()
            await agent.activate(temp_path)

            result = await agent.run(
                "analyze", path=str(temp_path / "nonexistent")
            )

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_analyze_command_success(self):
        """Test analyze command with valid path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create some test files
            docs_dir = temp_path / "docs"
            docs_dir.mkdir()
            (docs_dir / "test1.md").write_text("# Test 1\nContent")
            (docs_dir / "test2.md").write_text("# Test 2\nContent")

            agent = CleanupAgent()
            await agent.activate(temp_path)

            result = await agent.run("analyze", path=str(docs_dir))

            assert result["type"] == "analyze"
            assert result["success"] is True
            assert "report" in result
            assert result["report"]["total_files"] == 2


class TestCleanupAgentPlanCommand:
    """Tests for plan command."""

    @pytest.mark.asyncio
    async def test_plan_command_success(self):
        """Test plan command with valid path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create some test files
            docs_dir = temp_path / "docs"
            docs_dir.mkdir()
            (docs_dir / "test1.md").write_text("# Test 1\nContent")
            (docs_dir / "test1_copy.md").write_text("# Test 1\nContent")  # Duplicate

            agent = CleanupAgent()
            await agent.activate(temp_path)

            result = await agent.run("plan", path=str(docs_dir))

            assert result["type"] == "plan"
            assert result["success"] is True
            assert "plan" in result
            assert "total_actions" in result["plan"]


class TestCleanupAgentExecuteCommand:
    """Tests for execute command."""

    @pytest.mark.asyncio
    async def test_execute_command_dry_run(self):
        """Test execute command in dry-run mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create some test files
            docs_dir = temp_path / "docs"
            docs_dir.mkdir()
            (docs_dir / "test1.md").write_text("# Test 1\nContent")

            agent = CleanupAgent()
            await agent.activate(temp_path)

            result = await agent.run(
                "execute", path=str(docs_dir), dry_run=True, backup=False
            )

            assert result["type"] == "execute"
            assert result["success"] is True
            assert result["dry_run"] is True


class TestCleanupAgentRunCommand:
    """Tests for run command (full workflow)."""

    @pytest.mark.asyncio
    async def test_run_command_path_not_exists(self):
        """Test run command with non-existent path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            agent = CleanupAgent()
            await agent.activate(temp_path)

            result = await agent.run(
                "run", path=str(temp_path / "nonexistent")
            )

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_run_command_success(self):
        """Test run command with valid path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create some test files
            docs_dir = temp_path / "docs"
            docs_dir.mkdir()
            (docs_dir / "test1.md").write_text("# Test 1\nContent")
            (docs_dir / "test2.md").write_text("# Test 2\nDifferent content")

            agent = CleanupAgent()
            await agent.activate(temp_path)

            result = await agent.run(
                "run", path=str(docs_dir), dry_run=True, backup=False
            )

            assert result["type"] == "run"
            assert result["success"] is True
            assert result["dry_run"] is True
            assert "analysis" in result
            assert "plan" in result
            assert "execution" in result


class TestCleanupAgentHelp:
    """Tests for help command."""

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Test help command."""
        agent = CleanupAgent()
        result = await agent.run("help")

        assert result["type"] == "help"
        assert "content" in result
        assert "*analyze" in result["content"]
        assert "*plan" in result["content"]
        assert "*execute" in result["content"]
        assert "*run" in result["content"]


class TestCleanupAgentUnknownCommand:
    """Tests for unknown command handling."""

    @pytest.mark.asyncio
    async def test_unknown_command(self):
        """Test unknown command returns error."""
        agent = CleanupAgent()
        result = await agent.run("unknown_command")

        assert "error" in result
        assert "unknown command" in result["error"].lower()
