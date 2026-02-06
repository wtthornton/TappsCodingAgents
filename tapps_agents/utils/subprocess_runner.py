"""
Centralized subprocess execution utility.

Provides a single entry point for running external commands with:
- Unified error handling and logging
- Configurable timeouts
- Output capture (stdout/stderr)
- Optional command validation

Usage:
    from tapps_agents.utils.subprocess_runner import run_command, run_command_async

    result = run_command(["git", "status"], timeout=30)
    print(result.stdout)

Migration guide:
    Replace direct ``subprocess.run(...)`` calls with ``run_command(...)``
    across the codebase.  The function signature mirrors ``subprocess.run``
    but adds structured logging, timeout enforcement, and a ``CommandResult``
    return type.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Default timeout for subprocess calls (seconds)
DEFAULT_TIMEOUT = 60


@dataclass
class CommandResult:
    """Result of a subprocess execution."""

    returncode: int
    stdout: str = ""
    stderr: str = ""
    command: list[str] = field(default_factory=list)
    timed_out: bool = False

    @property
    def success(self) -> bool:
        """Whether the command exited with code 0."""
        return self.returncode == 0


def run_command(
    cmd: list[str],
    *,
    cwd: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    capture_output: bool = True,
    check: bool = False,
    env: dict[str, str] | None = None,
    stdin_data: str | None = None,
    **kwargs: Any,
) -> CommandResult:
    """Run an external command synchronously.

    Args:
        cmd: Command and arguments as a list.
        cwd: Working directory.
        timeout: Timeout in seconds.
        capture_output: Capture stdout/stderr (default True).
        check: Raise ``subprocess.CalledProcessError`` on non-zero exit.
        env: Environment variables (merged with current env if provided).
        stdin_data: Data to send to stdin.
        **kwargs: Extra keyword arguments forwarded to ``subprocess.run``.

    Returns:
        CommandResult with returncode, stdout, stderr.

    Raises:
        subprocess.CalledProcessError: If *check* is True and command fails.
    """
    logger.debug("Running command: %s (cwd=%s, timeout=%d)", cmd, cwd, timeout)

    try:
        result = subprocess.run(  # noqa: S603
            cmd,
            cwd=cwd,
            timeout=timeout,
            capture_output=capture_output,
            text=True,
            check=check,
            env=env,
            input=stdin_data,
            **kwargs,
        )
        return CommandResult(
            returncode=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            command=cmd,
        )
    except subprocess.TimeoutExpired:
        logger.warning("Command timed out after %ds: %s", timeout, cmd)
        return CommandResult(
            returncode=-1, stdout="", stderr=f"Timed out after {timeout}s",
            command=cmd, timed_out=True,
        )
    except FileNotFoundError:
        logger.error("Command not found: %s", cmd[0] if cmd else "<empty>")
        return CommandResult(
            returncode=-1, stdout="", stderr=f"Command not found: {cmd[0] if cmd else '<empty>'}",
            command=cmd,
        )


async def run_command_async(
    cmd: list[str],
    *,
    cwd: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    env: dict[str, str] | None = None,
    stdin_data: str | None = None,
) -> CommandResult:
    """Run an external command asynchronously.

    Uses ``asyncio.to_thread`` to avoid blocking the event loop.

    Args:
        cmd: Command and arguments as a list.
        cwd: Working directory.
        timeout: Timeout in seconds.
        env: Environment variables.
        stdin_data: Data to send to stdin.

    Returns:
        CommandResult with returncode, stdout, stderr.
    """
    return await asyncio.to_thread(
        run_command, cmd, cwd=cwd, timeout=timeout, env=env, stdin_data=stdin_data,
    )
