"""
Integration test for CLI session lifecycle: SessionStart on first command,
SessionEnd via atexit, session state under .tapps-agents/sessions/ when configured.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from tapps_agents.cli.main import (
    create_root_parser,
    register_all_parsers,
    route_command,
)


@pytest.mark.integration
def test_cli_session_start_invoked_on_real_command() -> None:
    """
    When routing a real command (e.g. doctor), ensure_session_started is called with Path.cwd().
    """
    parser = create_root_parser()
    register_all_parsers(parser)
    with patch("tapps_agents.session.ensure_session_started") as mock_start:
        args = parser.parse_args(["--no-progress", "doctor"])
        route_command(args)
        mock_start.assert_called_once()
        call_args = mock_start.call_args[0]
        call_kwargs = mock_start.call_args[1]
        assert len(call_args) >= 1
        assert call_args[0] == Path.cwd() or (call_args[0].resolve() == Path.cwd().resolve())
        assert call_kwargs.get("hook_manager") is None


@pytest.mark.integration
def test_cli_session_lifecycle_session_state_in_process(tmp_path: Path) -> None:
    """
    In-process: ensure_session_started with tmp_path and sessions dir creates state file.
    Verifies session state file is written when configured (sessions dir exists).
    """
    import json

    from tapps_agents.hooks.config import HooksConfig
    from tapps_agents.hooks.manager import HookManager
    from tapps_agents.session import ensure_session_started, get_session_id
    from tapps_agents.session.manager import _reset_state_for_testing

    sessions_dir = tmp_path / ".tapps-agents" / "sessions"
    sessions_dir.mkdir(parents=True)
    _reset_state_for_testing()
    try:
        mgr = HookManager(config=HooksConfig(hooks={}), project_root=tmp_path)
        sid = ensure_session_started(tmp_path, hook_manager=mgr)
        assert get_session_id() == sid
        files = list(sessions_dir.glob("*.json"))
        assert len(files) >= 1
        content = json.loads(files[0].read_text(encoding="utf-8"))
        assert content["session_id"] == sid
        assert content["project_root"] == str(tmp_path)
    finally:
        _reset_state_for_testing()


@pytest.mark.integration
def test_session_lifecycle_hydration_on_start_when_configured(tmp_path: Path) -> None:
    """
    When task-specs dir exists and hydration not disabled, SessionStart runs hydrate_to_beads.
    """
    from tapps_agents.beads.hydration import HydrationReport
    from tapps_agents.session.manager import (
        _reset_state_for_testing,
        _run_session_start_hydration,
        _session_hydration_enabled,
    )

    (tmp_path / ".tapps-agents" / "task-specs").mkdir(parents=True)
    _reset_state_for_testing()

    assert _session_hydration_enabled(tmp_path) is True

    with (
        patch("tapps_agents.beads.client.is_available", return_value=True),
        patch("tapps_agents.beads.hydration.hydrate_to_beads") as mock_hydrate,
    ):
        mock_hydrate.return_value = HydrationReport(created=0, skipped=0)
        _run_session_start_hydration(tmp_path)
        mock_hydrate.assert_called_once_with(project_root=tmp_path)

    _reset_state_for_testing()


@pytest.mark.integration
def test_session_hydration_disabled_by_env(tmp_path: Path) -> None:
    """When TAPPS_SESSION_HYDRATION=0, hydration is disabled."""
    import os

    from tapps_agents.session.manager import _session_hydration_enabled

    (tmp_path / ".tapps-agents" / "task-specs").mkdir(parents=True)
    with patch.dict(os.environ, {"TAPPS_SESSION_HYDRATION": "0"}):
        assert _session_hydration_enabled(tmp_path) is False
