"""
CLI session lifecycle for TappsCodingAgents.

Provides session tracking (session ID), SessionStart on first command,
SessionEnd on process exit via atexit, and optional session log/state
under .tapps-agents/sessions/.
"""

from .manager import (
    ensure_session_started,
    get_session_id,
    register_session_end_atexit,
)

__all__ = [
    "get_session_id",
    "ensure_session_started",
    "register_session_end_atexit",
]
