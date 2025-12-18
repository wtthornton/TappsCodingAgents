"""
Unit tests for Debugger Agent.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.debugger.agent import DebuggerAgent


@pytest.mark.unit
class TestDebuggerAgent:
    """Test cases for DebuggerAgent."""

    @pytest.fixture
    def debugger(self):
        """Create a DebuggerAgent instance with mocked MAL."""
        with patch("tapps_agents.agents.debugger.agent.load_config"):
            with patch("tapps_agents.agents.debugger.agent.MAL") as mock_mal_class:
                mock_mal = MagicMock()
                mock_mal.generate = AsyncMock(return_value="Mocked debug response")
                mock_mal_class.return_value = mock_mal
                
                with patch("tapps_agents.agents.debugger.agent.ErrorAnalyzer"):
                    agent = DebuggerAgent()
                    agent.mal = mock_mal
                    agent.error_analyzer = MagicMock()
                    agent.error_analyzer.analyze = AsyncMock(
                        return_value={"error": "test", "suggestions": []}
                    )
                    return agent

    @pytest.mark.asyncio
    async def test_debug_success(self, debugger):
        """Test debug command."""
        result = await debugger.run(
            "debug",
            error_message="Test error",
            file="test.py",
            line=10
        )

        assert "success" in result or "analysis" in result or "suggestions" in result

    @pytest.mark.asyncio
    async def test_debug_no_error_message(self, debugger):
        """Test debug command without error message."""
        result = await debugger.run("debug", error_message="")

        assert "error" in result
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_analyze_error(self, debugger):
        """Test analyze error command."""
        result = await debugger.run(
            "analyze-error",
            error_message="Test error",
            stack_trace="Traceback..."
        )

        assert "success" in result or "analysis" in result

    @pytest.mark.asyncio
    async def test_trace(self, debugger, tmp_path):
        """Test trace command."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")
        
        result = await debugger.run("trace", file=str(test_file), function="test")

        assert "success" in result or "trace" in result

    @pytest.mark.asyncio
    async def test_help(self, debugger):
        """Test help command."""
        result = await debugger.run("help")

        assert "type" in result or "content" in result

    @pytest.mark.asyncio
    async def test_unknown_command(self, debugger):
        """Test unknown command."""
        result = await debugger.run("unknown-command")

        assert "error" in result
        assert "Unknown command" in result["error"]

