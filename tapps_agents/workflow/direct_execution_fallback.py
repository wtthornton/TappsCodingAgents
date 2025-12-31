"""
Direct Execution Fallback - Execute commands directly when Background Agent API is unavailable.

This module provides a simpler fallback mechanism that executes commands directly
via subprocess instead of relying on file-based triggers. This eliminates the
need for watch_paths configuration and provides more reliable execution.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


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
    ):
        """
        Initialize direct execution fallback.

        Args:
            project_root: Project root directory
            timeout_seconds: Maximum execution time in seconds
        """
        self.project_root = project_root or Path.cwd()
        self.timeout_seconds = timeout_seconds

    async def execute_command(
        self,
        command: str,
        worktree_path: Path | None = None,
        workflow_id: str | None = None,
        step_id: str | None = None,
        environment: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a command directly via subprocess.

        This method converts Cursor Skill commands (e.g., "@reviewer *review file.py")
        to CLI commands (e.g., "python -m tapps_agents.cli reviewer review file.py")
        and executes them directly.

        Args:
            command: Skill command string (e.g., "@reviewer *review file.py")
            worktree_path: Optional worktree path (uses project_root if None)
            workflow_id: Optional workflow ID for tracking
            step_id: Optional step ID for tracking
            environment: Optional environment variables

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

        # Convert Skill command to CLI command
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
            process = await asyncio.create_subprocess_exec(
                *cli_command.split(),
                cwd=execution_path,
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

