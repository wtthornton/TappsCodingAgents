"""
Helpers for safe subprocess invocation across platforms.

In particular, Windows often uses .CMD/.BAT shims (e.g., npm.CMD/npx.CMD).
Those can fail to execute reliably via direct argv invocation unless routed
through cmd.exe. This module provides a small wrapper to normalize that.
"""

from __future__ import annotations

import platform
import shutil


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


