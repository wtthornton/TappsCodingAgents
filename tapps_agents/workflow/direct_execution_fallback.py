"""
Direct Execution Fallback - Execute commands directly when Background Agent API is unavailable.

This module provides a simpler fallback mechanism that executes commands directly
via subprocess instead of relying on file-based triggers. This eliminates the
need for watch_paths configuration and provides more reliable execution.

Plan 2.2: When GuardrailConfig.sandbox_subprocess is True, never use shell
(create_subprocess_shell); use create_subprocess_exec only. Prefer exec for
python -m tapps_agents.cli (already the case when not is_raw_cli).
"""

import asyncio
import logging
import shlex
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _get_guardrail_config() -> Any:
    """Load GuardrailConfig from project config; return defaults on failure."""
    try:
        from ..core.config import GuardrailConfig, load_config

        cfg = load_config()
        return getattr(cfg, "guardrails", None) or GuardrailConfig()
    except Exception:  # pylint: disable=broad-except
        from ..core.config import GuardrailConfig

        return GuardrailConfig()


class DirectExecutionFallback:
    """
    Direct execution fallback for when Background Agent API is unavailable.
    
    This class executes commands directly via subprocess instead of using
    file-based triggers, providing a simpler and more reliable fallback.
    """

    def __init__(
        self,
        project_root: Path | None = None,
        timeout_seconds: float = 3600.0,
        guardrail_config: Any = None,
    ):
        """
        Initialize direct execution fallback.

        Args:
            project_root: Project root directory
            timeout_seconds: Maximum execution time in seconds
            guardrail_config: Optional GuardrailConfig; if None, loaded from project config
        """
        self.project_root = Path(project_root or Path.cwd())
        self.timeout_seconds = timeout_seconds
        self._guardrail = guardrail_config if guardrail_config is not None else _get_guardrail_config()

    async def execute_command(
        self,
        command: str,
        worktree_path: Path | None = None,
        workflow_id: str | None = None,
        step_id: str | None = None,
        environment: dict[str, str] | None = None,
        is_raw_cli: bool = False,
    ) -> dict[str, Any]:
        """
        Execute a command directly via subprocess.

        This method converts Cursor Skill commands (e.g., "@reviewer *review file.py")
        to CLI commands (e.g., "python -m tapps_agents.cli reviewer review file.py")
        and executes them directly.

        Args:
            command: Skill command string (e.g., "@reviewer *review file.py") or raw CLI command
            worktree_path: Optional worktree path (uses project_root if None)
            workflow_id: Optional workflow ID for tracking
            step_id: Optional step ID for tracking
            environment: Optional environment variables
            is_raw_cli: If True, treat command as raw CLI command (skip Skill conversion)

        Returns:
            Execution result dictionary:
            - status: "completed", "failed", or "timeout"
            - command: The command that was executed
            - stdout: Standard output
            - stderr: Standard error
            - return_code: Process return code
            - duration_seconds: Execution duration
            - method: "direct_execution"
        """
        import time

        start_time = time.time()
        execution_path = worktree_path or self.project_root

        # Convert Skill command to CLI command (unless it's already a raw CLI command)
        if is_raw_cli or (not command.startswith("@") and not command.startswith("python -m tapps_agents.cli")):
            # Already a CLI command, use as-is
            cli_command = command
        else:
            cli_command = self._convert_skill_to_cli(command)

        # Prepare environment
        env = dict(os.environ) if (os := __import__("os")) else {}
        if environment:
            env.update(environment)
        env["TAPPS_AGENTS_MODE"] = "cursor"
        if workflow_id:
            env["TAPPS_AGENTS_WORKFLOW_ID"] = workflow_id
        if step_id:
            env["TAPPS_AGENTS_STEP_ID"] = step_id

        logger.info(
            f"Executing command directly (fallback mode): {cli_command}",
            extra={
                "command": cli_command,
                "worktree": str(execution_path),
                "method": "direct_execution",
            },
        )

        try:
            # Execute command in worktree directory
            # Use shlex.split() to properly handle quoted strings
            import platform
            is_windows = platform.system() == "Windows"
            
            # Plan 2.2: when sandbox_subprocess, never use shell
            sandbox = getattr(self._guardrail, "sandbox_subprocess", True)
            if sandbox:
                use_shell = False
            elif is_windows and is_raw_cli:
                # On Windows, for raw CLI commands, use shell=True only for a fixed
                # whitelist of builtins; do not interpolate user input into the shell string
                first_word = cli_command.split()[0] if cli_command.split() else ""
                shell_builtins = {"echo", "type", "dir", "cd", "set"}
                use_shell = first_word.lower() in shell_builtins
            else:
                use_shell = False

            # Plan 2.2: when sandbox_subprocess, use cwd=project_root
            cwd = self.project_root if sandbox else execution_path

            if use_shell:
                # Use shell=True for Windows built-in commands only when not sandboxed
                process = await asyncio.create_subprocess_shell(
                    cli_command,
                    cwd=cwd,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            else:
                # Use exec for regular commands (and always when sandboxed)
                command_parts = shlex.split(cli_command, posix=not is_windows)
                process = await asyncio.create_subprocess_exec(
                    *command_parts,
                    cwd=cwd,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout_seconds,
                )
                return_code = process.returncode
            except TimeoutError:
                process.kill()
                await process.wait()
                duration = time.time() - start_time
                return {
                    "status": "timeout",
                    "command": cli_command,
                    "stdout": "",
                    "stderr": f"Command execution exceeded timeout of {self.timeout_seconds}s",
                    "return_code": -1,
                    "duration_seconds": duration,
                    "method": "direct_execution",
                    "error": "Timeout",
                }

            duration = time.time() - start_time
            stdout_text = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_text = stderr.decode("utf-8", errors="replace") if stderr else ""

            # Determine status based on return code
            if return_code == 0:
                status = "completed"
            else:
                status = "failed"

            logger.info(
                f"Direct execution completed: {status} (return code: {return_code})",
                extra={
                    "command": cli_command,
                    "status": status,
                    "return_code": return_code,
                    "duration_seconds": duration,
                },
            )

            return {
                "status": status,
                "command": cli_command,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "return_code": return_code,
                "duration_seconds": duration,
                "method": "direct_execution",
            }

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Direct execution failed: {e}",
                extra={
                    "command": cli_command,
                    "error": str(e),
                    "duration_seconds": duration,
                },
                exc_info=True,
            )
            return {
                "status": "failed",
                "command": cli_command,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "duration_seconds": duration,
                "method": "direct_execution",
                "error": str(e),
            }

    def _convert_skill_to_cli(self, skill_command: str) -> str:
        """
        Convert Cursor Skill command to CLI command.

        Examples:
            "@reviewer *review file.py" -> "python -m tapps_agents.cli reviewer review file.py"
            "@analyst gather-requirements \"desc\"" -> "python -m tapps_agents.cli analyst gather-requirements \"desc\""

        Args:
            skill_command: Skill command string

        Returns:
            CLI command string
        """
        # Remove leading "@" if present
        if skill_command.startswith("@"):
            skill_command = skill_command[1:]

        # Split into parts
        parts = skill_command.split()

        if not parts:
            raise ValueError(f"Invalid skill command: {skill_command}")

        # First part is agent name
        agent_name = parts[0]

        # Second part is command (may have "*" prefix)
        if len(parts) > 1:
            command_name = parts[1]
            if command_name.startswith("*"):
                command_name = command_name[1:]
            remaining_args = parts[2:]
        else:
            command_name = None
            remaining_args = []

        # Build CLI command
        cli_parts = ["python", "-m", "tapps_agents.cli", agent_name]

        if command_name:
            cli_parts.append(command_name)

        cli_parts.extend(remaining_args)

        return " ".join(cli_parts)

