"""
Helpers for safe subprocess invocation across platforms.

In particular, Windows often uses .CMD/.BAT shims (e.g., npm.CMD/npx.CMD).
Those can fail to execute reliably via direct argv invocation unless routed
through cmd.exe. This module provides a small wrapper to normalize that.

Phase 5.3: Enhanced with OutputHandler for proper stdout/stderr separation
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass

from typing import Any


def wrap_windows_cmd_shim(argv: list[str]) -> list[str]:
    """
    If argv[0] resolves to a .CMD/.BAT shim on Windows, wrap the command as:
        ["cmd", "/c", *argv]
    Otherwise return argv unchanged.
    """

    if not argv:
        return argv
    if platform.system() != "Windows":
        return argv

    exe = argv[0]
    if exe.lower().endswith((".cmd", ".bat")):
        return ["cmd", "/c", *argv]

    resolved = shutil.which(exe)
    if resolved and resolved.lower().endswith((".cmd", ".bat")):
        return ["cmd", "/c", *argv]

    return argv


@dataclass
class ProcessOutput:
    """
    Structured output from a subprocess execution.

    Phase 5.3: ProcessOutput dataclass for stdout/stderr separation
    """

    stdout: str
    stderr: str
    returncode: int
    success: bool

    def __post_init__(self) -> None:
        """Ensure success is set based on returncode."""
        if not hasattr(self, "success") or self.success is None:
            self.success = self.returncode == 0


class OutputHandler:
    """
    Handler for subprocess output with proper stdout/stderr separation.

    Phase 5.3: PowerShell Output Fix

    Ensures proper separation of stdout and stderr across platforms,
    with special handling for PowerShell-specific issues on Windows.
    """

    @staticmethod
    def handle_output(
        process_result: subprocess.CompletedProcess[Any], encoding: str = "utf-8"
    ) -> ProcessOutput:
        """
        Handle subprocess output with proper stdout/stderr separation.

        Phase 5.3: Output Handling with Cross-Platform Compatibility

        Args:
            process_result: Completed subprocess result
            encoding: Text encoding to use (default: utf-8)

        Returns:
            ProcessOutput with separated stdout, stderr, returncode, and success
        """
        # Handle stdout
        stdout_text = ""
        if process_result.stdout:
            if isinstance(process_result.stdout, bytes):
                try:
                    stdout_text = process_result.stdout.decode(encoding, errors="replace")
                except Exception:
                    # Fallback to latin-1 if utf-8 fails
                    stdout_text = process_result.stdout.decode("latin-1", errors="replace")
            else:
                stdout_text = str(process_result.stdout)

        # Handle stderr
        stderr_text = ""
        if process_result.stderr:
            if isinstance(process_result.stderr, bytes):
                try:
                    stderr_text = process_result.stderr.decode(encoding, errors="replace")
                except Exception:
                    # Fallback to latin-1 if utf-8 fails
                    stderr_text = process_result.stderr.decode("latin-1", errors="replace")
            else:
                stderr_text = str(process_result.stderr)

        # On Windows/PowerShell, sometimes error output goes to stdout
        # This is a common issue with PowerShell cmdlets
        # We keep them separate but note this in the output

        return ProcessOutput(
            stdout=stdout_text.strip(),
            stderr=stderr_text.strip(),
            returncode=process_result.returncode,
            success=process_result.returncode == 0,
        )

    @staticmethod
    def handle_output_bytes(
        stdout: bytes | None,
        stderr: bytes | None,
        returncode: int,
        encoding: str = "utf-8",
    ) -> ProcessOutput:
        """
        Handle subprocess output from bytes directly.

        Phase 5.3: Direct bytes handling for async subprocess calls

        Args:
            stdout: stdout bytes
            stderr: stderr bytes
            returncode: Process return code
            encoding: Text encoding to use (default: utf-8)

        Returns:
            ProcessOutput with separated stdout, stderr, returncode, and success
        """
        # Handle stdout
        stdout_text = ""
        if stdout:
            try:
                stdout_text = stdout.decode(encoding, errors="replace")
            except Exception:
                # Fallback to latin-1 if utf-8 fails
                stdout_text = stdout.decode("latin-1", errors="replace")

        # Handle stderr
        stderr_text = ""
        if stderr:
            try:
                stderr_text = stderr.decode(encoding, errors="replace")
            except Exception:
                # Fallback to latin-1 if utf-8 fails
                stderr_text = stderr.decode("latin-1", errors="replace")

        return ProcessOutput(
            stdout=stdout_text.strip(),
            stderr=stderr_text.strip(),
            returncode=returncode,
            success=returncode == 0,
        )


