"""
Integration tests for DebuggerAgent.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from tapps_agents.agents.debugger import DebuggerAgent


@pytest.mark.integration
class TestDebuggerAgent:
    """Integration tests for DebuggerAgent."""

    @pytest.fixture
    def mock_mal(self):
        """Create a mock MAL."""
        mal = MagicMock(spec=MAL)
        mal.generate = AsyncMock(
            return_value="""
ROOT_CAUSE: Missing import
ISSUE: Module not imported
SUGGESTIONS:
1. Add import statement
FIX_EXAMPLES:
```python
import module
```
"""
        )
        mal.close = AsyncMock()
        return mal

    @pytest.mark.asyncio
    async def test_activate(self, mock_mal):
        """Test agent activation."""
        agent = DebuggerAgent(mal=mock_mal)
        await agent.activate()

        assert agent.config is not None
        assert agent.error_analyzer is not None

    @pytest.mark.asyncio
    async def test_get_commands(self, mock_mal):
        """Test command list."""
        agent = DebuggerAgent(mal=mock_mal)
        await agent.activate()

        commands = agent.get_commands()
        command_names = [cmd["command"] for cmd in commands]

        assert "*help" in command_names
        assert "*debug" in command_names
        assert "*analyze-error" in command_names
        assert "*trace" in command_names

    @pytest.mark.asyncio
    async def test_debug_command(self, mock_mal):
        """Test debug command."""
        agent = DebuggerAgent(mal=mock_mal)
        await agent.activate()

        result = await agent.debug_command(
            error_message="NameError: name 'x' is not defined"
        )

        assert "type" in result
        assert result["type"] == "debug"
        assert "error_message" in result
        assert "suggestions" in result

    @pytest.mark.asyncio
    async def test_debug_command_with_file(self, mock_mal, tmp_path: Path):
        """Test debug command with file."""
        code_file = tmp_path / "test.py"
        code_file.write_text("def func():\n    print(x)")

        agent = DebuggerAgent(mal=mock_mal)
        await agent.activate()

        result = await agent.debug_command(
            error_message="NameError: name 'x' is not defined",
            file=str(code_file),
            line=2,
        )

        assert "type" in result
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_analyze_error_command(self, mock_mal):
        """Test analyze-error command."""
        agent = DebuggerAgent(mal=mock_mal)
        await agent.activate()

        result = await agent.analyze_error_command(
            error_message="ValueError: invalid input"
        )

        assert "type" in result
        assert result["type"] == "error_analysis"
        assert "error_type" in result
        assert "suggestions" in result

    @pytest.mark.asyncio
    async def test_trace_command(self, mock_mal, tmp_path: Path):
        """Test trace command."""
        code_file = tmp_path / "test.py"
        code_file.write_text("def func1():\n    return func2()\ndef func2():\n    pass")

        agent = DebuggerAgent(mal=mock_mal)
        await agent.activate()

        result = await agent.trace_command(file=str(code_file), function="func1")

        assert "type" in result
        assert result["type"] == "trace"
        assert "file" in result
        assert "trace_analysis" in result

    @pytest.mark.asyncio
    async def test_trace_command_file_not_found(self, mock_mal):
        """Test trace command with non-existent file."""
        agent = DebuggerAgent(mal=mock_mal)
        await agent.activate()

        result = await agent.trace_command(file="nonexistent.py")

        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_help_command(self, mock_mal):
        """Test help command."""
        agent = DebuggerAgent(mal=mock_mal)
        await agent.activate()

        result = await agent.run("help")

        assert "type" in result
        assert result["type"] == "help"
        assert "content" in result
        assert "*debug" in result["content"]

    @pytest.mark.asyncio
    async def test_unknown_command(self, mock_mal):
        """Test unknown command handling."""
        agent = DebuggerAgent(mal=mock_mal)
        await agent.activate()

        result = await agent.run("unknown_command")

        assert "error" in result

    @pytest.mark.asyncio
    async def test_close(self, mock_mal):
        """Test agent cleanup."""
        agent = DebuggerAgent(mal=mock_mal)
        await agent.activate()
        await agent.close()

        mock_mal.close.assert_called_once()
