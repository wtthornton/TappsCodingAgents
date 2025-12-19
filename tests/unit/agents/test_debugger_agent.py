"""
Unit tests for Debugger Agent.

Tests agent initialization, command handling, error analysis, code tracing,
and error handling.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.debugger.agent import DebuggerAgent

pytestmark = pytest.mark.unit


class TestDebuggerAgentInitialization:
    """Tests for DebuggerAgent initialization."""

    @patch("tapps_agents.agents.debugger.agent.load_config")
    def test_debugger_agent_init(self, mock_load_config):
        """Test DebuggerAgent initialization."""
        mock_config = MagicMock()
        mock_config.agents = MagicMock()
        mock_config.agents.debugger = MagicMock()
        mock_config.agents.debugger.include_code_examples = True
        mock_config.agents.debugger.max_context_lines = 50
        mock_load_config.return_value = mock_config
        
        agent = DebuggerAgent()
        assert agent.agent_id == "debugger"
        assert agent.agent_name == "Debugger Agent"
        assert agent.config is not None
        assert agent.error_analyzer is not None
        assert agent.include_code_examples is True

    @pytest.mark.asyncio
    async def test_debugger_agent_activate(self, temp_project_dir: Path):
        """Test DebuggerAgent activation."""
        agent = DebuggerAgent()
        await agent.activate(temp_project_dir)
        
        assert agent.config is not None

    @pytest.mark.asyncio
    async def test_debugger_agent_get_commands(self):
        """Test DebuggerAgent command list."""
        agent = DebuggerAgent()
        commands = agent.get_commands()
        
        assert isinstance(commands, list)
        assert len(commands) > 0
        command_names = [cmd["command"] for cmd in commands]
        assert "*debug" in command_names
        assert "*analyze-error" in command_names
        assert "*trace" in command_names


class TestDebuggerAgentDebugCommand:
    """Tests for debug command."""

    @pytest.mark.asyncio
    async def test_debug_command_success(self):
        """Test debug command with successful error analysis."""
        agent = DebuggerAgent()
        await agent.activate()
        
        # Mock error analyzer
        mock_analysis = {
            "error_type": "ValueError",
            "suggestions": ["Check input validation"],
            "fix_examples": ["def safe_parse(value): ..."]
        }
        agent.error_analyzer.analyze_error = AsyncMock(return_value=mock_analysis)
        
        result = await agent.run("debug", error_message="ValueError: invalid input")
        
        assert "type" in result
        assert result["type"] == "debug"
        assert "error_message" in result
        assert "analysis" in result
        assert "suggestions" in result
        assert "fix_examples" in result

    @pytest.mark.asyncio
    async def test_debug_command_missing_error_message(self):
        """Test debug command without error message."""
        agent = DebuggerAgent()
        await agent.activate()
        
        result = await agent.run("debug")
        
        assert "error" in result
        assert "error message required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_debug_command_with_file(self, sample_python_file):
        """Test debug command with file path."""
        agent = DebuggerAgent()
        await agent.activate()
        
        # Mock error analyzer
        mock_analysis = {
            "error_type": "ValueError",
            "suggestions": ["Check input validation"]
        }
        agent.error_analyzer.analyze_error = AsyncMock(return_value=mock_analysis)
        
        result = await agent.run(
            "debug",
            error_message="ValueError: invalid input",
            file=str(sample_python_file),
            line=5
        )
        
        assert "type" in result
        assert result["type"] == "debug"
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_debug_command_with_stack_trace(self):
        """Test debug command with stack trace."""
        agent = DebuggerAgent()
        await agent.activate()
        
        stack_trace = "Traceback (most recent call last):\n  File \"test.py\", line 5, in <module>\n    raise ValueError('test')"
        
        # Mock error analyzer
        mock_analysis = {
            "error_type": "ValueError",
            "suggestions": ["Check input validation"]
        }
        agent.error_analyzer.analyze_error = AsyncMock(return_value=mock_analysis)
        
        result = await agent.run(
            "debug",
            error_message="ValueError: test",
            stack_trace=stack_trace
        )
        
        assert "type" in result
        assert result["type"] == "debug"

    @pytest.mark.asyncio
    async def test_debug_command_file_not_found(self, tmp_path):
        """Test debug command with non-existent file."""
        agent = DebuggerAgent()
        await agent.activate()
        
        # Mock error analyzer
        mock_analysis = {"error_type": "ValueError", "suggestions": []}
        agent.error_analyzer.analyze_error = AsyncMock(return_value=mock_analysis)
        
        result = await agent.run(
            "debug",
            error_message="ValueError: test",
            file=str(tmp_path / "nonexistent.py")
        )
        
        # Should still work, just without file context
        assert "type" in result
        assert result["type"] == "debug"

    @pytest.mark.asyncio
    async def test_debug_command_without_code_examples(self):
        """Test debug command when code examples are disabled."""
        agent = DebuggerAgent()
        agent.include_code_examples = False
        await agent.activate()
        
        # Mock error analyzer
        mock_analysis = {
            "error_type": "ValueError",
            "suggestions": ["Check input validation"],
            "fix_examples": ["def safe_parse(value): ..."]
        }
        agent.error_analyzer.analyze_error = AsyncMock(return_value=mock_analysis)
        
        result = await agent.run("debug", error_message="ValueError: test")
        
        assert "type" in result
        assert result["fix_examples"] == []  # Should be empty when disabled

    @pytest.mark.asyncio
    async def test_debug_command_method(self):
        """Test debug_command method directly."""
        agent = DebuggerAgent()
        await agent.activate()
        
        # Mock error analyzer
        mock_analysis = {"error_type": "ValueError", "suggestions": []}
        agent.error_analyzer.analyze_error = AsyncMock(return_value=mock_analysis)
        
        result = await agent.debug_command(error_message="ValueError: test")
        
        assert "type" in result
        assert result["type"] == "debug"


class TestDebuggerAgentAnalyzeErrorCommand:
    """Tests for analyze-error command."""

    @pytest.mark.asyncio
    async def test_analyze_error_command_success(self):
        """Test analyze-error command with successful analysis."""
        agent = DebuggerAgent()
        await agent.activate()
        
        # Mock error analyzer
        mock_instruction = MagicMock()
        mock_instruction.to_dict.return_value = {"type": "error_analysis"}
        mock_instruction.to_skill_command.return_value = "@debugger *analyze-error"
        agent.error_analyzer.prepare_error_analysis = MagicMock(return_value=mock_instruction)
        
        result = await agent.run(
            "analyze-error",
            error_message="ValueError: invalid input"
        )
        
        assert "type" in result
        assert result["type"] == "error_analysis"
        assert "instruction" in result
        assert "skill_command" in result
        assert "error_message" in result

    @pytest.mark.asyncio
    async def test_analyze_error_command_missing_error_message(self):
        """Test analyze-error command without error message."""
        agent = DebuggerAgent()
        await agent.activate()
        
        result = await agent.run("analyze-error")
        
        assert "error" in result
        assert "error message required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_analyze_error_command_with_stack_trace(self):
        """Test analyze-error command with stack trace."""
        agent = DebuggerAgent()
        await agent.activate()
        
        stack_trace = "Traceback (most recent call last):\n  File \"test.py\", line 5"
        
        # Mock error analyzer
        mock_instruction = MagicMock()
        mock_instruction.to_dict.return_value = {"type": "error_analysis"}
        mock_instruction.to_skill_command.return_value = "@debugger *analyze-error"
        agent.error_analyzer.prepare_error_analysis = MagicMock(return_value=mock_instruction)
        
        result = await agent.run(
            "analyze-error",
            error_message="ValueError: test",
            stack_trace=stack_trace
        )
        
        assert "type" in result
        assert result["type"] == "error_analysis"

    @pytest.mark.asyncio
    async def test_analyze_error_command_with_code_context(self):
        """Test analyze-error command with code context."""
        agent = DebuggerAgent()
        await agent.activate()
        
        code_context = "def process(data):\n    return data[0]"
        
        # Mock error analyzer
        mock_instruction = MagicMock()
        mock_instruction.to_dict.return_value = {"type": "error_analysis"}
        mock_instruction.to_skill_command.return_value = "@debugger *analyze-error"
        agent.error_analyzer.prepare_error_analysis = MagicMock(return_value=mock_instruction)
        
        result = await agent.run(
            "analyze-error",
            error_message="IndexError: list index out of range",
            code_context=code_context
        )
        
        assert "type" in result
        assert result["type"] == "error_analysis"

    @pytest.mark.asyncio
    async def test_analyze_error_command_method(self):
        """Test analyze_error_command method directly."""
        agent = DebuggerAgent()
        await agent.activate()
        
        # Mock error analyzer
        mock_instruction = MagicMock()
        mock_instruction.to_dict.return_value = {"type": "error_analysis"}
        mock_instruction.to_skill_command.return_value = "@debugger *analyze-error"
        agent.error_analyzer.prepare_error_analysis = MagicMock(return_value=mock_instruction)
        
        result = await agent.analyze_error_command(error_message="ValueError: test")
        
        assert "type" in result
        assert result["type"] == "error_analysis"


class TestDebuggerAgentTraceCommand:
    """Tests for trace command."""

    @pytest.mark.asyncio
    async def test_trace_command_success(self, sample_python_file):
        """Test trace command with successful code tracing."""
        agent = DebuggerAgent()
        await agent.activate()
        
        # Mock error analyzer
        mock_instruction = MagicMock()
        mock_instruction.to_dict.return_value = {"type": "code_trace"}
        mock_instruction.to_skill_command.return_value = "@debugger *trace"
        agent.error_analyzer.prepare_code_trace = MagicMock(return_value=mock_instruction)
        
        result = await agent.run("trace", file=str(sample_python_file))
        
        assert "type" in result
        assert result["type"] == "trace"
        assert "instruction" in result
        assert "skill_command" in result
        assert "file" in result

    @pytest.mark.asyncio
    async def test_trace_command_file_not_found(self, tmp_path):
        """Test trace command with non-existent file."""
        agent = DebuggerAgent()
        await agent.activate()
        
        result = await agent.run("trace", file=str(tmp_path / "nonexistent.py"))
        
        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_trace_command_with_function(self, sample_python_file):
        """Test trace command with function name."""
        agent = DebuggerAgent()
        await agent.activate()
        
        # Mock error analyzer
        mock_instruction = MagicMock()
        mock_instruction.to_dict.return_value = {"type": "code_trace"}
        mock_instruction.to_skill_command.return_value = "@debugger *trace"
        agent.error_analyzer.prepare_code_trace = MagicMock(return_value=mock_instruction)
        
        result = await agent.run(
            "trace",
            file=str(sample_python_file),
            function="hello"
        )
        
        assert "type" in result
        assert result["type"] == "trace"
        assert result["function"] == "hello"

    @pytest.mark.asyncio
    async def test_trace_command_with_line(self, sample_python_file):
        """Test trace command with line number."""
        agent = DebuggerAgent()
        await agent.activate()
        
        # Mock error analyzer
        mock_instruction = MagicMock()
        mock_instruction.to_dict.return_value = {"type": "code_trace"}
        mock_instruction.to_skill_command.return_value = "@debugger *trace"
        agent.error_analyzer.prepare_code_trace = MagicMock(return_value=mock_instruction)
        
        result = await agent.run(
            "trace",
            file=str(sample_python_file),
            line=5
        )
        
        assert "type" in result
        assert result["type"] == "trace"
        assert result["line"] == 5

    @pytest.mark.asyncio
    async def test_trace_command_method(self, sample_python_file):
        """Test trace_command method directly."""
        agent = DebuggerAgent()
        await agent.activate()
        
        # Mock error analyzer
        mock_instruction = MagicMock()
        mock_instruction.to_dict.return_value = {"type": "code_trace"}
        mock_instruction.to_skill_command.return_value = "@debugger *trace"
        agent.error_analyzer.prepare_code_trace = MagicMock(return_value=mock_instruction)
        
        result = await agent.trace_command(file=str(sample_python_file))
        
        assert "type" in result
        assert result["type"] == "trace"


class TestDebuggerAgentErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_unknown_command(self):
        """Test unknown command handling."""
        agent = DebuggerAgent()
        await agent.activate()
        
        result = await agent.run("unknown-command")
        
        assert "error" in result
        assert "unknown command" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Test help command."""
        agent = DebuggerAgent()
        await agent.activate()
        
        result = await agent.run("help")
        
        assert "type" in result
        assert result["type"] == "help"
        assert "content" in result
        assert "*debug" in result["content"]

    @pytest.mark.asyncio
    async def test_debug_command_path_validation_error(self, tmp_path):
        """Test debug command handles path validation errors."""
        agent = DebuggerAgent()
        await agent.activate()
        
        # Create a file that will fail validation
        large_file = tmp_path / "large.py"
        large_file.write_text("x" * (11 * 1024 * 1024))  # Larger than 10MB
        
        # Mock error analyzer
        mock_analysis = {"error_type": "ValueError", "suggestions": []}
        agent.error_analyzer.analyze_error = AsyncMock(return_value=mock_analysis)
        
        # Mock _validate_path to raise ValueError
        with patch.object(agent, '_validate_path', side_effect=ValueError("File too large")):
            result = await agent.run(
                "debug",
                error_message="ValueError: test",
                file=str(large_file)
            )
            
            # Should still work, just without file context
            assert "type" in result or "error" in result


class TestDebuggerAgentCodeContextExtraction:
    """Tests for code context extraction in debug command."""

    @pytest.mark.asyncio
    async def test_debug_command_extracts_context_around_line(self, tmp_path):
        """Test debug command extracts context around specified line."""
        agent = DebuggerAgent()
        agent.max_context_lines = 10
        await agent.activate()
        
        # Create a file with many lines
        test_file = tmp_path / "test.py"
        lines = [f"line {i}" for i in range(100)]
        test_file.write_text("\n".join(lines))
        
        # Mock error analyzer
        mock_analysis = {"error_type": "ValueError", "suggestions": []}
        agent.error_analyzer.analyze_error = AsyncMock(return_value=mock_analysis)
        
        result = await agent.run(
            "debug",
            error_message="ValueError: test",
            file=str(test_file),
            line=50
        )
        
        assert "type" in result
        # Verify error analyzer was called with context
        assert agent.error_analyzer.analyze_error.called
        call_args = agent.error_analyzer.analyze_error.call_args
        code_context = call_args.kwargs.get("code_context")
        if code_context:
            # Should contain lines around line 50
            assert "line 45" in code_context or "line 50" in code_context

    @pytest.mark.asyncio
    async def test_debug_command_extracts_first_lines_when_no_line_specified(self, tmp_path):
        """Test debug command extracts first lines when no line specified."""
        agent = DebuggerAgent()
        await agent.activate()
        
        # Create a file with many lines
        test_file = tmp_path / "test.py"
        lines = [f"line {i}" for i in range(200)]
        test_file.write_text("\n".join(lines))
        
        # Mock error analyzer
        mock_analysis = {"error_type": "ValueError", "suggestions": []}
        agent.error_analyzer.analyze_error = AsyncMock(return_value=mock_analysis)
        
        result = await agent.run(
            "debug",
            error_message="ValueError: test",
            file=str(test_file)
        )
        
        assert "type" in result
        # Verify error analyzer was called with context
        assert agent.error_analyzer.analyze_error.called
        call_args = agent.error_analyzer.analyze_error.call_args
        code_context = call_args.kwargs.get("code_context")
        if code_context:
            # Should contain first lines
            assert "line 0" in code_context or "line 1" in code_context

