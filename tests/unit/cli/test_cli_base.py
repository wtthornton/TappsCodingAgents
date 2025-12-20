"""
Unit tests for CLI base utilities.

Tests standardized utilities in tapps_agents/cli/base.py:
- Exit codes
- Output formatting
- Error handling
- Agent lifecycle management
- Async command execution
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.cli.base import (
    EXIT_CONFIG_ERROR,
    EXIT_GENERAL_ERROR,
    EXIT_SUCCESS,
    EXIT_USAGE_ERROR,
    format_error_output,
    format_output,
    handle_agent_error,
    normalize_command,
    run_agent_command,
    run_async_command,
    run_with_agent_lifecycle,
)


class TestNormalizeCommand:
    """Tests for normalize_command function."""

    def test_normalize_command_with_star(self):
        """Test normalizing command with star prefix."""
        assert normalize_command("*review") == "review"
        assert normalize_command("*score") == "score"

    def test_normalize_command_without_star(self):
        """Test normalizing command without star prefix."""
        assert normalize_command("review") == "review"
        assert normalize_command("score") == "score"

    def test_normalize_command_none(self):
        """Test normalizing None command."""
        assert normalize_command(None) is None


class TestFormatOutput:
    """Tests for format_output function."""

    def test_format_output_json_dict(self, capsys):
        """Test formatting dict as JSON."""
        data = {"result": "success", "value": 42}
        format_output(data, format_type="json")
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["success"] is True
        assert result["data"] == data

    def test_format_output_json_string(self, capsys):
        """Test formatting string as JSON (wraps in JSON structure)."""
        data = "simple string"
        format_output(data, format_type="json")
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["success"] is True
        assert result["data"]["content"] == data

    def test_format_output_text(self, capsys):
        """Test formatting as text."""
        data = "simple text output"
        format_output(data, format_type="text")
        captured = capsys.readouterr()
        assert captured.out.strip() == data


class TestFormatErrorOutput:
    """Tests for format_error_output function."""

    def test_format_error_output_json(self, capsys):
        """Test formatting error as JSON."""
        with pytest.raises(SystemExit) as exc_info:
            format_error_output(
                "Test error",
                error_type="test_error",
                exit_code=EXIT_GENERAL_ERROR,
                format_type="json",
            )
        assert exc_info.value.code == EXIT_GENERAL_ERROR
        captured = capsys.readouterr()
        error_data = json.loads(captured.err)
        assert error_data["success"] is False
        assert error_data["error"]["message"] == "Test error"
        assert error_data["error"]["code"] == "test_error"

    def test_format_error_output_json_with_details(self, capsys):
        """Test formatting error as JSON with details."""
        with pytest.raises(SystemExit) as exc_info:
            format_error_output(
                "Validation failed",
                error_type="validation_error",
                exit_code=EXIT_USAGE_ERROR,
                format_type="json",
                details={"field": "email", "reason": "Invalid format"},
            )
        assert exc_info.value.code == EXIT_USAGE_ERROR
        captured = capsys.readouterr()
        error_data = json.loads(captured.err)
        assert error_data["success"] is False
        assert error_data["error"]["message"] == "Validation failed"
        assert error_data["error"]["code"] == "validation_error"
        assert error_data["error"]["context"]["field"] == "email"

    def test_format_error_output_text(self, capsys):
        """Test formatting error as text."""
        with pytest.raises(SystemExit) as exc_info:
            format_error_output(
                "File not found",
                error_type="file_not_found",
                exit_code=EXIT_GENERAL_ERROR,
                format_type="text",
            )
        assert exc_info.value.code == EXIT_GENERAL_ERROR
        captured = capsys.readouterr()
        assert "Error: File not found" in captured.err

    def test_format_error_output_text_with_details(self, capsys):
        """Test formatting error as text with details."""
        with pytest.raises(SystemExit) as exc_info:
            format_error_output(
                "Validation failed",
                error_type="validation_error",
                exit_code=EXIT_USAGE_ERROR,
                format_type="text",
                details={"field": "email"},
            )
        assert exc_info.value.code == EXIT_USAGE_ERROR
        captured = capsys.readouterr()
        assert "Error: Validation failed" in captured.err
        assert "field: email" in captured.err


class TestHandleAgentError:
    """Tests for handle_agent_error function."""

    def test_handle_agent_error_no_error(self, capsys):
        """Test handling result without error (should not exit)."""
        result = {"success": True, "data": "test"}
        # Should not raise or exit
        handle_agent_error(result, format_type="json")
        captured = capsys.readouterr()
        # Should not output anything
        assert captured.err == ""

    def test_handle_agent_error_with_error_json(self, capsys):
        """Test handling result with error (JSON format)."""
        result = {"error": "Test error", "error_type": "test_error"}
        with pytest.raises(SystemExit) as exc_info:
            handle_agent_error(result, format_type="json")
        assert exc_info.value.code == EXIT_GENERAL_ERROR
        captured = capsys.readouterr()
        error_data = json.loads(captured.err)
        assert error_data["success"] is False
        assert error_data["error"]["message"] == "Test error"
        assert error_data["error"]["code"] == "test_error"

    def test_handle_agent_error_with_error_text(self, capsys):
        """Test handling result with error (text format)."""
        result = {"error": "Test error"}
        with pytest.raises(SystemExit) as exc_info:
            handle_agent_error(result, format_type="text")
        assert exc_info.value.code == EXIT_GENERAL_ERROR
        captured = capsys.readouterr()
        assert "Error: Test error" in captured.err

    def test_handle_agent_error_custom_exit_code(self, capsys):
        """Test handling error with custom exit code."""
        result = {"error": "Usage error"}
        with pytest.raises(SystemExit) as exc_info:
            handle_agent_error(result, format_type="json", exit_code=EXIT_USAGE_ERROR)
        assert exc_info.value.code == EXIT_USAGE_ERROR


class TestRunWithAgentLifecycle:
    """Tests for run_with_agent_lifecycle function."""

    @pytest.mark.asyncio
    async def test_run_with_agent_lifecycle_success(self):
        """Test successful agent lifecycle execution."""
        agent = MagicMock()
        agent.activate = AsyncMock()
        agent.close = AsyncMock()

        async def command_func():
            return {"result": "success"}

        result = await run_with_agent_lifecycle(agent, command_func)

        assert result == {"result": "success"}
        agent.activate.assert_called_once()
        agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_agent_lifecycle_with_args(self):
        """Test agent lifecycle with command function arguments."""
        agent = MagicMock()
        agent.activate = AsyncMock()
        agent.close = AsyncMock()

        async def command_func(arg1, arg2, kwarg1=None):
            return {"arg1": arg1, "arg2": arg2, "kwarg1": kwarg1}

        result = await run_with_agent_lifecycle(
            agent, command_func, "value1", "value2", kwarg1="value3"
        )

        assert result["arg1"] == "value1"
        assert result["arg2"] == "value2"
        assert result["kwarg1"] == "value3"
        agent.activate.assert_called_once()
        agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_agent_lifecycle_always_closes(self):
        """Test that agent.close() is called even if command raises exception."""
        agent = MagicMock()
        agent.activate = AsyncMock()
        agent.close = AsyncMock()

        async def command_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await run_with_agent_lifecycle(agent, command_func)

        agent.activate.assert_called_once()
        agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_agent_lifecycle_no_close_method(self):
        """Test lifecycle with agent that doesn't have close method."""
        # Create a simple object without close method
        class AgentWithoutClose:
            def __init__(self):
                self.activate_called = False
            
            async def activate(self):
                self.activate_called = True
        
        agent = AgentWithoutClose()

        async def command_func():
            return {"result": "success"}

        result = await run_with_agent_lifecycle(agent, command_func)

        assert result == {"result": "success"}
        assert agent.activate_called
        # Should not raise error if close doesn't exist


class TestRunAsyncCommand:
    """Tests for run_async_command function."""

    def test_run_async_command_success(self):
        """Test running async command successfully."""
        async def coro():
            return "result"

        result = run_async_command(coro())
        assert result == "result"

    def test_run_async_command_with_exception(self):
        """Test running async command that raises exception."""
        async def coro():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            run_async_command(coro())

    @pytest.mark.asyncio
    async def test_run_async_command_in_loop_raises(self):
        """Test that run_async_command raises if called from within event loop."""
        async def coro():
            return "result"
        
        # Try to call run_async_command from within async context
        with pytest.raises(RuntimeError, match="cannot be called from a running event loop"):
            run_async_command(coro())


class TestRunAgentCommand:
    """Tests for run_agent_command function."""

    @pytest.mark.asyncio
    async def test_run_agent_command_success(self):
        """Test successful agent command execution."""
        agent = MagicMock()
        agent.activate = AsyncMock()
        agent.close = AsyncMock()
        agent.run = AsyncMock(return_value={"result": "success"})

        result = await run_agent_command(
            agent, "test-command", format_type="json", exit_on_error=False
        )

        assert result == {"result": "success"}
        agent.activate.assert_called_once()
        agent.run.assert_called_once_with("test-command")
        agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_agent_command_normalizes_command(self):
        """Test that command is normalized (star prefix removed)."""
        agent = MagicMock()
        agent.activate = AsyncMock()
        agent.close = AsyncMock()
        agent.run = AsyncMock(return_value={"result": "success"})

        await run_agent_command(
            agent, "*test-command", format_type="json", exit_on_error=False
        )

        # Should normalize *test-command to test-command
        agent.run.assert_called_once_with("test-command")

    @pytest.mark.asyncio
    async def test_run_agent_command_with_kwargs(self):
        """Test agent command with keyword arguments."""
        agent = MagicMock()
        agent.activate = AsyncMock()
        agent.close = AsyncMock()
        agent.run = AsyncMock(return_value={"result": "success"})

        await run_agent_command(
            agent,
            "test-command",
            format_type="json",
            exit_on_error=False,
            file="test.py",
        )

        agent.run.assert_called_once_with("test-command", file="test.py")

    @pytest.mark.asyncio
    async def test_run_agent_command_exit_on_error(self, capsys):
        """Test agent command that exits on error."""
        agent = MagicMock()
        agent.activate = AsyncMock()
        agent.close = AsyncMock()
        agent.run = AsyncMock(return_value={"error": "Test error"})

        with pytest.raises(SystemExit) as exc_info:
            await run_agent_command(
                agent, "test-command", format_type="json", exit_on_error=True
            )
        assert exc_info.value.code == EXIT_GENERAL_ERROR
        agent.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_agent_command_no_exit_on_error(self):
        """Test agent command that returns error instead of exiting."""
        agent = MagicMock()
        agent.activate = AsyncMock()
        agent.close = AsyncMock()
        agent.run = AsyncMock(return_value={"error": "Test error"})

        result = await run_agent_command(
            agent, "test-command", format_type="json", exit_on_error=False
        )

        assert result == {"error": "Test error"}
        agent.close.assert_called_once()


class TestExitCodes:
    """Tests for exit code constants."""

    def test_exit_codes_defined(self):
        """Test that exit codes are properly defined."""
        assert EXIT_SUCCESS == 0
        assert EXIT_GENERAL_ERROR == 1
        assert EXIT_USAGE_ERROR == 2
        assert EXIT_CONFIG_ERROR == 3

