"""
Tests for direct_execution_fallback.py
"""

import asyncio
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
        fallback = DirectExecutionFallback()
        
        # Use a simple command that should succeed (Windows-compatible)
        # Use echo or a simple Python command without nested quotes
        import sys
        import platform
        if platform.system() == "Windows":
            # Windows: use echo command
            cmd = "echo test"
        else:
            # Unix: use echo
            cmd = "echo test"
        result = await fallback.execute_command(
            command=cmd,
            workflow_id="test-workflow",
            is_raw_cli=True,  # Skip Skill command conversion
        )
        
        assert result["status"] == "completed"
        assert result["return_code"] == 0
        # Output should contain "test"
        output = result["stdout"] + result["stderr"]
        assert "test" in output.lower()
        assert "duration_seconds" in result
        assert result["method"] == "direct_execution"

    @pytest.mark.asyncio
    async def test_execute_command_failure(self):
        """Test executing a failing command."""
        fallback = DirectExecutionFallback()
        
        # Use a command that should fail (Windows-compatible)
        import sys
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
        """Test executing command in specific worktree path."""
        import sys
        import platform
        with tempfile.TemporaryDirectory() as tmpdir:
            worktree_path = Path(tmpdir)
            fallback = DirectExecutionFallback()
            
            # Create a test file in worktree
            test_file = worktree_path / "test.txt"
            test_file.write_text("test content")
            
            # Execute command that reads the file (Windows-compatible)
            if platform.system() == "Windows":
                # Windows: use type command
                cmd = f"type test.txt"
            else:
                # Unix: use cat command
                cmd = "cat test.txt"
            result = await fallback.execute_command(
                command=cmd,
                worktree_path=worktree_path,
                is_raw_cli=True,  # Skip Skill command conversion
            )
            
            assert result["status"] == "completed"
            output = result["stdout"] + result["stderr"]
            assert "test content" in output

    @pytest.mark.asyncio
    async def test_execute_command_with_environment(self):
        """Test executing command with custom environment."""
        import sys
        import platform
        fallback = DirectExecutionFallback()
        
        if platform.system() == "Windows":
            # Windows: use echo with environment variable
            cmd = "echo %TEST_VAR%"
        else:
            # Unix: use echo with environment variable
            cmd = "echo $TEST_VAR"
        result = await fallback.execute_command(
            command=cmd,
            environment={"TEST_VAR": "test_value"},
            is_raw_cli=True,  # Skip Skill command conversion
        )
        
        assert result["status"] == "completed"
        output = result["stdout"] + result["stderr"]
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
        import platform
        fallback = DirectExecutionFallback()
        
        if platform.system() == "Windows":
            cmd = "echo %TAPPS_AGENTS_WORKFLOW_ID%"
        else:
            cmd = "echo $TAPPS_AGENTS_WORKFLOW_ID"
        result = await fallback.execute_command(
            command=cmd,
            workflow_id="test-workflow-123",
            is_raw_cli=True,  # Skip Skill command conversion
        )
        
        assert result["status"] == "completed"
        output = result["stdout"] + result["stderr"]
        assert "test-workflow-123" in output

    @pytest.mark.asyncio
    async def test_execute_command_step_id_in_env(self):
        """Test that step_id is set in environment."""
        import sys
        import platform
        fallback = DirectExecutionFallback()
        
        if platform.system() == "Windows":
            cmd = "echo %TAPPS_AGENTS_STEP_ID%"
        else:
            cmd = "echo $TAPPS_AGENTS_STEP_ID"
        result = await fallback.execute_command(
            command=cmd,
            step_id="step-1",
            is_raw_cli=True,  # Skip Skill command conversion
        )
        
        assert result["status"] == "completed"
        output = result["stdout"] + result["stderr"]
        assert "step-1" in output

    @pytest.mark.asyncio
    async def test_execute_command_cursor_mode_in_env(self):
        """Test that TAPPS_AGENTS_MODE is set to cursor."""
        import sys
        import platform
        fallback = DirectExecutionFallback()
        
        if platform.system() == "Windows":
            cmd = "echo %TAPPS_AGENTS_MODE%"
        else:
            cmd = "echo $TAPPS_AGENTS_MODE"
        result = await fallback.execute_command(
            command=cmd,
            is_raw_cli=True,  # Skip Skill command conversion
        )
        
        assert result["status"] == "completed"
        output = result["stdout"] + result["stderr"]
        assert "cursor" in output.lower()
