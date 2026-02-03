"""
Hook executor: run hook shell commands with TAPPS_* env vars, timeout, and capture.

Runs hooks synchronously; captures stdout/stderr; configurable timeout (default 30s).
Non-zero exit is logged and optionally fails the workflow when fail_on_error is True.
"""

from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import HookDefinition

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 30


@dataclass
class HookResult:
    """Result of running a single hook."""

    stdout: str
    stderr: str
    returncode: int
    timed_out: bool
    hook_name: str

    @property
    def success(self) -> bool:
        """True if hook completed without timeout and returncode 0."""
        return not self.timed_out and self.returncode == 0


def _substitute_placeholders(command: str, env: dict[str, str]) -> str:
    """Replace {name} in command with env value; names are lower-case env keys."""
    result = command
    for key, value in env.items():
        # Support both {TAPPS_FILE_PATH} and {file_path} style
        placeholder = "{" + key + "}"
        if placeholder in result:
            result = result.replace(placeholder, value)
        # Snake-case style: TAPPS_FILE_PATH -> file_path
        snake = key.replace("TAPPS_", "").lower()
        if "{" + snake + "}" in result:
            result = result.replace("{" + snake + "}", value)
    return result


def run_hook(
    hook: HookDefinition,
    env: dict[str, str],
    *,
    timeout_seconds: int | None = None,
    project_root: Path | None = None,
) -> HookResult:
    """
    Execute a hook's shell command with the given environment.

    Args:
        hook: Hook definition (name, command, fail_on_error).
        env: Environment variables for the process (e.g. TAPPS_FILE_PATH, TAPPS_PROMPT).
            Merged over current process env; passed to the subprocess.
        timeout_seconds: Max run time in seconds; default DEFAULT_TIMEOUT_SECONDS.
        project_root: Optional project root; cwd for the subprocess when set.

    Returns:
        HookResult with stdout, stderr, returncode, timed_out, hook_name.
    """
    timeout_seconds = timeout_seconds if timeout_seconds is not None else DEFAULT_TIMEOUT_SECONDS
    full_env = {**os.environ, **env}
    command = _substitute_placeholders(hook.command, full_env)
    cwd = Path(project_root) if project_root else None

    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=full_env,
            cwd=cwd,
            timeout=timeout_seconds,
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        if stderr.strip():
            logger.warning("Hook %s stderr: %s", hook.name, stderr.strip())
        if proc.returncode != 0:
            logger.error(
                "Hook %s exited with code %d: %s",
                hook.name,
                proc.returncode,
                stderr.strip() or stdout.strip() or "(no output)",
            )
        return HookResult(
            stdout=stdout,
            stderr=stderr,
            returncode=proc.returncode,
            timed_out=False,
            hook_name=hook.name,
        )
    except subprocess.TimeoutExpired as e:
        logger.error("Hook %s timed out after %s seconds", hook.name, timeout_seconds)
        stdout = (e.stdout or b"").decode("utf-8", errors="replace") if e.stdout else ""
        stderr = (e.stderr or b"").decode("utf-8", errors="replace") if e.stderr else ""
        return HookResult(
            stdout=stdout,
            stderr=stderr + f"\n(Hook timed out after {timeout_seconds}s)",
            returncode=-1,
            timed_out=True,
            hook_name=hook.name,
        )
    except Exception as e:
        logger.exception("Hook %s failed: %s", hook.name, e)
        return HookResult(
            stdout="",
            stderr=str(e),
            returncode=-1,
            timed_out=False,
            hook_name=hook.name,
        )
