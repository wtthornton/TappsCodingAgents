"""
Runtime mode detection for TappsCodingAgents.

Design goal:
- When invoked from Cursor Skills / Cursor Background Agents, Cursor is the only "brain".
  The framework operates in tools-only mode.
- When invoked headlessly (CLI/CI/outside Cursor), the framework operates in headless mode.

This module provides a single source of truth for runtime mode detection.
"""

from __future__ import annotations

import os
from enum import StrEnum


class RuntimeMode(StrEnum):
    CURSOR = "cursor"
    HEADLESS = "headless"


def detect_runtime_mode() -> RuntimeMode:
    """
    Determine runtime mode.

    Precedence:
    1) Explicit override via TAPPS_AGENTS_MODE
       - cursor/background  -> RuntimeMode.CURSOR
       - headless/cli       -> RuntimeMode.HEADLESS
    2) Best-effort auto-detection of Cursor runtime markers
    3) Default to headless (safer for standalone CLI behavior)
    """

    raw = (os.getenv("TAPPS_AGENTS_MODE") or "").strip().lower()
    if raw in ("cursor", "background"):
        return RuntimeMode.CURSOR
    if raw in ("headless", "cli"):
        return RuntimeMode.HEADLESS

    # Best-effort Cursor detection (non-exhaustive; safe if missing).
    cursor_markers = (
        "CURSOR",
        "CURSOR_IDE",
        "CURSOR_SESSION_ID",
        "CURSOR_WORKSPACE_ROOT",
        "CURSOR_TRACE_ID",
    )
    if any(os.getenv(k) for k in cursor_markers):
        return RuntimeMode.CURSOR

    return RuntimeMode.HEADLESS


def is_cursor_mode() -> bool:
    """Convenience helper."""

    return detect_runtime_mode() == RuntimeMode.CURSOR


