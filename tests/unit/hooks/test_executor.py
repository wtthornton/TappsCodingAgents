"""
Unit tests for tapps_agents.hooks.executor: command execution, env vars, timeout, capture.
"""

import sys
from pathlib import Path

import pytest

from tapps_agents.hooks.config import HookDefinition
from tapps_agents.hooks.executor import (
    DEFAULT_TIMEOUT_SECONDS,
    HookResult,
    run_hook,
)


@pytest.mark.unit
class TestRunHook:
    """Tests for run_hook execution and capture."""

    def test_run_success_captures_stdout(self) -> None:
        """Successful command stdout is captured."""
        hook = HookDefinition(name="echo-test", command="echo ok")
        result = run_hook(hook, {}, timeout_seconds=5)
        assert result.success
        assert "ok" in result.stdout or "ok" in (result.stdout + result.stderr)
        assert result.returncode == 0
        assert result.timed_out is False

    def test_run_with_env_vars(self) -> None:
        """TAPPS_* env vars are passed to the process."""
        hook = HookDefinition(name="env-test", command="echo $TAPPS_PROMPT")
        # On Windows cmd/PowerShell echo $TAPPS_PROMPT may not expand; use Python
        if sys.platform == "win32":
            cmd = f'python -c "import os; print(os.environ.get(\\"TAPPS_PROMPT\\", \\"\\"))"'
        else:
            cmd = 'python -c "import os; print(os.environ.get(\'TAPPS_PROMPT\', \'\'))"'
        hook = HookDefinition(name="env-test", command=cmd)
        result = run_hook(hook, {"TAPPS_PROMPT": "hello world"}, timeout_seconds=5)
        assert result.success
        assert "hello world" in result.stdout

    def test_run_nonzero_exit_captured(self) -> None:
        """Non-zero exit is captured; success is False."""
        hook = HookDefinition(name="fail", command="exit 2")
        if sys.platform == "win32":
            hook = HookDefinition(name="fail", command="python -c \"import sys; sys.exit(2)\"")
        result = run_hook(hook, {}, timeout_seconds=5)
        assert not result.success
        assert result.returncode == 2
        assert result.timed_out is False

    def test_timeout_returns_timed_out_result(self) -> None:
        """When command exceeds timeout, timed_out is True and process is killed."""
        # Sleep 10s with 1s timeout
        if sys.platform == "win32":
            cmd = "python -c \"import time; time.sleep(10)\""
        else:
            cmd = "sleep 10"
        hook = HookDefinition(name="slow", command=cmd)
        result = run_hook(hook, {}, timeout_seconds=1)
        assert result.timed_out
        assert not result.success
        assert result.returncode == -1
        assert "timed out" in result.stderr or "TimeoutExpired" in result.stderr or result.stderr == ""

    def test_placeholder_substitution_in_command(self) -> None:
        """Command {TAPPS_FILE_PATH} is substituted from env before run."""
        # Executor substitutes {TAPPS_FILE_PATH} so command becomes "echo /tmp/foo.py"
        hook = HookDefinition(name="subst", command="echo {TAPPS_FILE_PATH}")
        result = run_hook(hook, {"TAPPS_FILE_PATH": "/tmp/foo.py"}, timeout_seconds=5)
        assert result.success
        assert "foo.py" in result.stdout


@pytest.mark.unit
class TestHookResult:
    """Tests for HookResult."""

    def test_success_true_when_zero_exit_and_not_timed_out(self) -> None:
        """success is True only when returncode 0 and not timed_out."""
        r = HookResult(stdout="", stderr="", returncode=0, timed_out=False, hook_name="h")
        assert r.success
        r2 = HookResult(stdout="", stderr="", returncode=1, timed_out=False, hook_name="h")
        assert not r2.success
        r3 = HookResult(stdout="", stderr="", returncode=0, timed_out=True, hook_name="h")
        assert not r3.success

    def test_default_timeout_constant(self) -> None:
        """DEFAULT_TIMEOUT_SECONDS is 30."""
        assert DEFAULT_TIMEOUT_SECONDS == 30
