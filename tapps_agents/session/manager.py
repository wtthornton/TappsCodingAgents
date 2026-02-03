"""
CLI session lifecycle manager.

SessionStart on first tapps-agents command, SessionEnd on exit via atexit;
session tracking with session ID (TAPPS_SESSION_ID) and optional log/state
under .tapps-agents/sessions/ when configured.
"""

from __future__ import annotations

import atexit
import json
import logging
import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tapps_agents.hooks.manager import HookManager

logger = logging.getLogger(__name__)

# Process-global: session id and whether we have already started/registered atexit
_session_id: str | None = None
_started: bool = False
_atexit_registered: bool = False
_project_root: Path | None = None


def _reset_state_for_testing() -> None:
    """Reset process-global session state. For use in unit tests only."""
    global _session_id, _started, _atexit_registered, _project_root
    _session_id = None
    _started = False
    _atexit_registered = False
    _project_root = None


def get_session_id() -> str | None:
    """Return current session ID, or None if session not started."""
    return _session_id


def _get_sessions_dir(project_root: Path) -> Path | None:
    """
    Return .tapps-agents/sessions path if session state is enabled.

    Session log/state is written when:
    - TAPPS_SESSION_STATE=1 or TAPPS_SESSION_LOG=1, or
    - The directory .tapps-agents/sessions already exists (user-configured).
    """
    sessions_dir = project_root / ".tapps-agents" / "sessions"
    if os.environ.get("TAPPS_SESSION_STATE", "") == "1":
        return sessions_dir
    if os.environ.get("TAPPS_SESSION_LOG", "") == "1":
        return sessions_dir
    if sessions_dir.exists():
        return sessions_dir
    return None


def _write_session_state(session_id: str, project_root: Path, started: bool) -> None:
    """Write optional session state file under .tapps-agents/sessions/."""
    sessions_dir = _get_sessions_dir(project_root)
    if not sessions_dir:
        return
    try:
        sessions_dir.mkdir(parents=True, exist_ok=True)
        path = sessions_dir / f"{session_id}.json"
        state = {
            "session_id": session_id,
            "project_root": str(project_root),
            "started": started,
        }
        path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError as e:
        logger.debug("Could not write session state: %s", e)


def _session_hydration_enabled(project_root: Path) -> bool:
    """True if session lifecycle hydration is enabled (not disabled and task-specs configured)."""
    if os.environ.get("TAPPS_SESSION_HYDRATION", "").strip().lower() in ("0", "false", "no"):
        return False
    task_specs_dir = project_root / ".tapps-agents" / "task-specs"
    return task_specs_dir.exists()


def _run_session_start_hydration(project_root: Path, *, show_ready: bool = False) -> None:
    """
    On SessionStart: hydrate task specs to Beads; optionally run bd ready and log output.
    No-op if hydration disabled or bd/task-specs not configured.
    """
    if not _session_hydration_enabled(project_root):
        return
    try:
        from tapps_agents.beads.hydration import hydrate_to_beads
        from tapps_agents.beads.client import is_available, run_bd

        if not is_available(project_root):
            return
        report = hydrate_to_beads(project_root=project_root)
        if report.bd_unavailable:
            return
        if report.created or report.deps_added:
            logger.info(
                "Session hydration: created=%d skipped=%d deps_added=%d",
                report.created,
                report.skipped,
                report.deps_added,
            )
        if show_ready or os.environ.get("TAPPS_SESSION_SHOW_READY", "").strip() == "1":
            r = run_bd(project_root, ["ready"])
            if r.returncode == 0 and r.stdout:
                logger.info("Beads ready: %s", r.stdout.strip()[:500])
    except Exception as e:
        logger.warning("SessionStart hydration error: %s", e)


def _run_session_end_dehydration(project_root: Path) -> None:
    """
    On SessionEnd: dehydrate from Beads and log short report (updated count).
    No-op if hydration disabled or bd not available.
    """
    if not _session_hydration_enabled(project_root):
        return
    try:
        from tapps_agents.beads.hydration import dehydrate_from_beads

        updated = dehydrate_from_beads(project_root=project_root)
        if updated > 0:
            logger.info("Session hydration: %d spec(s) updated from Beads", updated)
    except Exception as e:
        logger.warning("SessionEnd dehydration error: %s", e)


def _fire_session_start(project_root: Path, hook_manager: HookManager) -> None:
    """Fire SessionStart hook with current session ID and project root."""
    sid = get_session_id()
    if not sid:
        return
    from tapps_agents.hooks.events import SessionStartEvent

    payload = SessionStartEvent(session_id=sid, project_root=str(project_root))
    try:
        hook_manager.trigger("SessionStart", payload)
    except Exception as e:
        logger.warning("SessionStart hook error: %s", e)
    _run_session_start_hydration(project_root)


def _fire_session_end(project_root: Path, hook_manager: HookManager) -> None:
    """Fire SessionEnd hook; run dehydrate and log hydration report."""
    _run_session_end_dehydration(project_root)
    sid = get_session_id()
    if not sid:
        return
    from tapps_agents.hooks.events import SessionEndEvent

    payload = SessionEndEvent(session_id=sid, project_root=str(project_root))
    try:
        hook_manager.trigger("SessionEnd", payload)
    except Exception as e:
        logger.warning("SessionEnd hook error: %s", e)


def ensure_session_started(
    project_root: Path | str | None = None,
    *,
    hook_manager: HookManager | None = None,
) -> str:
    """
    Start CLI session on first call: generate session ID, fire SessionStart, register atexit.

    Idempotent: later calls in the same process return the same session ID and do not
    fire SessionStart again.

    Args:
        project_root: Project root (default: cwd). Used for hooks and optional state.
        hook_manager: HookManager instance. If None, one is created for project_root.

    Returns:
        Current session ID (UUID string).
    """
    global _session_id, _started, _atexit_registered, _project_root

    root = Path(project_root) if project_root else Path.cwd()

    if _started:
        assert _session_id is not None
        return _session_id

    _session_id = str(uuid.uuid4())
    _started = True
    _project_root = root

    if hook_manager is None:
        from tapps_agents.hooks.manager import HookManager

        hook_manager = HookManager(project_root=root)

    _write_session_state(_session_id, root, started=True)
    _fire_session_start(root, hook_manager)

    if not _atexit_registered:
        _atexit_registered = True
        _hm = hook_manager

        def _on_exit() -> None:
            global _session_id, _project_root
            root = _project_root or Path.cwd()
            _fire_session_end(root, _hm)
            if _session_id and _project_root:
                _write_session_state(_session_id, _project_root, started=False)

        atexit.register(_on_exit)

    return _session_id


def register_session_end_atexit(
    project_root: Path | str | None = None,
    *,
    hook_manager: HookManager | None = None,
) -> None:
    """
    Register atexit handler for SessionEnd only (does not start session).

    Use when you have already started the session via ensure_session_started
    and want to ensure SessionEnd is registered. If ensure_session_started
    was called, atexit is already registered; this is for edge cases or tests.
    """
    global _atexit_registered, _project_root

    root = Path(project_root) if project_root else Path.cwd()
    _project_root = _project_root or root

    if hook_manager is None:
        from tapps_agents.hooks.manager import HookManager

        hook_manager = HookManager(project_root=root)

    if _atexit_registered:
        return

    _atexit_registered = True
    _hm = hook_manager

    def _on_exit() -> None:
        global _session_id, _project_root
        root = _project_root or Path.cwd()
        _fire_session_end(root, _hm)
        if _session_id and _project_root:
            _write_session_state(_session_id, _project_root, started=False)

    atexit.register(_on_exit)
