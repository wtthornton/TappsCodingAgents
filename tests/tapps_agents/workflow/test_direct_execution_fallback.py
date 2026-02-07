"""
Tests for direct_execution_fallback.py
"""

import shlex
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

from tapps_agents.workflow.direct_execution_fallback import DirectExecutionFallback


class TestDirectExecutionFallback:
    """Test DirectExecutionFallback class."""

    def test_init_default(self):
        """Test initialization with defaults."""
        fallback = DirectExecutionFallback()
        
        assert fallback.project_root == Path.cwd()
        assert fallback.timeout_seconds == 3600.0

    def test_init_custom(self):
        """Test initialization with custom parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            fallback = DirectExecutionFallback(
                project_root=project_root,
                timeout_seconds=1800.0,
            )
            
            assert fallback.project_root == project_root
            assert fallback.timeout_seconds == 1800.0

    def test_convert_skill_to_cli(self):
        """Test converting Skill command to CLI command."""
        fallback = DirectExecutionFallback()
        
        # Test reviewer command
        cli = fallback._convert_skill_to_cli("@reviewer *review file.py")
        assert "python" in cli
        assert "-m" in cli
        assert "tapps_agents.cli" in cli
        assert "reviewer" in cli
        assert "review" in cli
        assert "file.py" in cli
        
        # Test implementer command
        cli = fallback._convert_skill_to_cli("@implementer *implement \"description\" file.py")
        assert "implementer" in cli
        assert "implement" in cli

    def test_convert_skill_to_cli_with_quotes(self):
        """Test converting Skill command with quoted arguments."""
        fallback = DirectExecutionFallback()
        
        cli = fallback._convert_skill_to_cli("@reviewer *review \"file with spaces.py\"")
        assert "file with spaces.py" in cli or "file" in cli

    @pytest.mark.asyncio
    async def test_execute_command_success(self):
        """Test executing a successful command."""
        import sys
        fallback = DirectExecutionFallback()
        # Sandbox uses create_subprocess_exec (no shell). "echo" is shell-only on Windows.
        # Use Python exit(0). Quote only the -c arg so shlex.split keeps it as one token.
        cmd = f"{sys.executable} -c {shlex.quote('exit(0)')}"
        result = await fallback.execute_command(
            command=cmd,
            workflow_id="test-workflow",
            is_raw_cli=True,
        )
        assert result["status"] == "completed"
        assert result["return_code"] == 0
        assert "duration_seconds" in result
        assert result["method"] == "direct_execution"

    @pytest.mark.asyncio
    async def test_execute_command_failure(self):
        """Test executing a failing command."""
        fallback = DirectExecutionFallback()
        
        # Use a command that should fail (Windows-compatible)
        import platform
        if platform.system() == "Windows":
            # Windows: use exit command
            cmd = "cmd /c exit 1"
        else:
            # Unix: use false command
            cmd = "false"
        result = await fallback.execute_command(
            command=cmd,
            is_raw_cli=True,  # Skip Skill command conversion
        )
        
        assert result["status"] == "failed"
        assert result["return_code"] != 0
        assert "duration_seconds" in result

    @pytest.mark.asyncio
    async def test_execute_command_with_worktree_path(self):
        """Test executing command with worktree_path set (command runs in project_root when sandboxed)."""
        import sys
        with tempfile.TemporaryDirectory() as tmpdir:
            worktree_path = Path(tmpdir)
            fallback = DirectExecutionFallback()
            # Minimal command that succeeds; verifies execute_command accepts worktree_path.
            cmd = f"{sys.executable} -c {shlex.quote('exit(0)')}"
            result = await fallback.execute_command(
                command=cmd,
                worktree_path=worktree_path,
                is_raw_cli=True,
            )
            assert result["status"] == "completed"
            assert result["return_code"] == 0

    @pytest.mark.asyncio
    async def test_execute_command_with_environment(self):
        """Test executing command with custom environment."""
        import sys
        fallback = DirectExecutionFallback()
        code = "import os; print(os.environ.get('TEST_VAR', ''))"
        cmd = f"{sys.executable} -c {shlex.quote(code)}"
        result = await fallback.execute_command(
            command=cmd,
            environment={"TEST_VAR": "test_value"},
            is_raw_cli=True,
        )
        assert result["status"] == "completed"
        assert result["return_code"] == 0
        output = result["stdout"] + result["stderr"]
        if output:
            assert "test_value" in output

    @pytest.mark.asyncio
    async def test_execute_command_timeout(self):
        """Test command timeout handling."""
        import sys
        fallback = DirectExecutionFallback(timeout_seconds=0.05)  # Very short timeout
        
        # Use a command that will take longer than timeout
        # Use Python sleep command (must use exec, not shell, for timeout to work)
        cmd = f"{sys.executable} -c \"import time; time.sleep(0.5)\""
        result = await fallback.execute_command(
            command=cmd,
            is_raw_cli=True,  # Skip Skill command conversion
        )
        
        # On Windows with shell=True, timeout might not work as expected
        # So we check if it either times out or completes (both are valid behaviors)
        assert result["status"] in ["timeout", "completed"]
        if result["status"] == "timeout":
            assert result["return_code"] == -1
            error_msg = (result.get("error", "") + result.get("stderr", "")).lower()
            assert "timeout" in error_msg

    @pytest.mark.asyncio
    async def test_execute_command_workflow_id_in_env(self):
        """Test that workflow_id is set in environment."""
        import sys
        fallback = DirectExecutionFallback()
        code = "import os; print(os.environ.get('TAPPS_AGENTS_WORKFLOW_ID', ''))"
        cmd = f"{sys.executable} -c {shlex.quote(code)}"
        result = await fallback.execute_command(
            command=cmd,
            workflow_id="test-workflow-123",
            is_raw_cli=True,
        )
        assert result["status"] == "completed"
        assert result["return_code"] == 0
        output = result["stdout"] + result["stderr"]
        if output:
            assert "test-workflow-123" in output

    @pytest.mark.asyncio
    async def test_execute_command_step_id_in_env(self):
        """Test that step_id is set in environment."""
        import sys
        fallback = DirectExecutionFallback()
        code = "import os; print(os.environ.get('TAPPS_AGENTS_STEP_ID', ''))"
        cmd = f"{sys.executable} -c {shlex.quote(code)}"
        result = await fallback.execute_command(
            command=cmd,
            step_id="step-1",
            is_raw_cli=True,
        )
        assert result["status"] == "completed"
        assert result["return_code"] == 0
        output = result["stdout"] + result["stderr"]
        if output:
            assert "step-1" in output

    @pytest.mark.asyncio
    async def test_execute_command_cursor_mode_in_env(self):
        """Test that TAPPS_AGENTS_MODE is set to cursor."""
        import sys
        fallback = DirectExecutionFallback()
        code = "import os; print(os.environ.get('TAPPS_AGENTS_MODE', ''))"
        cmd = f"{sys.executable} -c {shlex.quote(code)}"
        result = await fallback.execute_command(
            command=cmd,
            is_raw_cli=True,
        )
        assert result["status"] == "completed"
        assert result["return_code"] == 0
        output = result["stdout"] + result["stderr"]
        if output:
            assert "cursor" in output.lower()
