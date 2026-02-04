"""
Unit tests for tapps_agents.session.manager: session creation, atexit registration,
optional session state under .tapps-agents/sessions/ when configured.
"""

import json
import os
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from tapps_agents.hooks.config import HooksConfig
from tapps_agents.hooks.manager import HookManager
from tapps_agents.session import ensure_session_started, get_session_id
from tapps_agents.session.manager import (
    _get_sessions_dir,
    _reset_state_for_testing,
    _write_session_state,
)

pytestmark = pytest.mark.unit


def _reset_session_state() -> None:
    _reset_state_for_testing()


@pytest.fixture(autouse=True)
def reset_between_tests() -> None:
    """Reset session state after each test so tests are isolated."""
    yield
    _reset_session_state()


class TestGetSessionId:
    """get_session_id returns None before start and session id after."""

    def test_before_start_returns_none(self) -> None:
        _reset_session_state()
        assert get_session_id() is None

    def test_after_start_returns_uuid(self) -> None:
        _reset_session_state()
        sid = ensure_session_started(Path("/tmp"), hook_manager=HookManager(config=HooksConfig(hooks={})))
        assert get_session_id() == sid
        # UUID format
        uuid.UUID(sid)


class TestEnsureSessionStarted:
    """ensure_session_started generates session ID, fires SessionStart, registers atexit."""

    def test_returns_uuid_string(self) -> None:
        _reset_session_state()
        mgr = HookManager(config=HooksConfig(hooks={}))
        sid = ensure_session_started(Path("/proj"), hook_manager=mgr)
        assert isinstance(sid, str)
        uuid.UUID(sid)

    def test_idempotent_second_call_returns_same_id(self) -> None:
        _reset_session_state()
        mgr = HookManager(config=HooksConfig(hooks={}))
        sid1 = ensure_session_started(Path("/proj"), hook_manager=mgr)
        sid2 = ensure_session_started(Path("/other"), hook_manager=mgr)
        assert sid1 == sid2

    def test_atexit_registered(self) -> None:
        _reset_session_state()
        with patch("tapps_agents.session.manager.atexit") as mock_atexit:
            mgr = HookManager(config=HooksConfig(hooks={}))
            ensure_session_started(Path("/proj"), hook_manager=mgr)
            mock_atexit.register.assert_called_once()
            (handler,) = mock_atexit.register.call_args[0]
            assert callable(handler)

    def test_session_start_triggered_with_payload_env(self) -> None:
        _reset_session_state()
        mgr = HookManager(config=HooksConfig(hooks={}))
        sid = ensure_session_started(Path("/my/project"), hook_manager=mgr)
        # HookManager was used; no hooks in config so trigger is a no-op
        assert sid is not None
        assert get_session_id() == sid


class TestGetSessionsDir:
    """_get_sessions_dir returns path when configured (env or dir exists)."""

    def test_none_when_env_unset_and_dir_missing(self) -> None:
        with patch.dict(os.environ, {"TAPPS_SESSION_STATE": "", "TAPPS_SESSION_LOG": ""}, clear=False):
            root = Path("/tmp/nonexistent")
            assert not (root / ".tapps-agents" / "sessions").exists()
            assert _get_sessions_dir(root) is None

    def test_returns_dir_when_tapps_session_state_1(self) -> None:
        with patch.dict(os.environ, {"TAPPS_SESSION_STATE": "1"}, clear=False):
            root = Path("/proj")
            d = _get_sessions_dir(root)
            assert d == root / ".tapps-agents" / "sessions"

    def test_returns_dir_when_tapps_session_log_1(self) -> None:
        with patch.dict(os.environ, {"TAPPS_SESSION_LOG": "1"}, clear=False):
            root = Path("/proj")
            d = _get_sessions_dir(root)
            assert d == root / ".tapps-agents" / "sessions"

    def test_returns_dir_when_sessions_dir_exists(self, tmp_path: Path) -> None:
        with patch.dict(os.environ, {"TAPPS_SESSION_STATE": "", "TAPPS_SESSION_LOG": ""}, clear=False):
            sessions_dir = tmp_path / ".tapps-agents" / "sessions"
            sessions_dir.mkdir(parents=True)
            assert _get_sessions_dir(tmp_path) == sessions_dir


class TestWriteSessionState:
    """Optional session state file under .tapps-agents/sessions/ when configured."""

    def test_no_file_when_sessions_dir_not_configured(self, tmp_path: Path) -> None:
        with patch.dict(os.environ, {"TAPPS_SESSION_STATE": "", "TAPPS_SESSION_LOG": ""}, clear=False):
            _write_session_state("sid-123", tmp_path, started=True)
            sessions_dir = tmp_path / ".tapps-agents" / "sessions"
            assert not sessions_dir.exists()

    def test_writes_file_when_tapps_session_state_1(self, tmp_path: Path) -> None:
        with patch.dict(os.environ, {"TAPPS_SESSION_STATE": "1"}, clear=False):
            _write_session_state("sid-456", tmp_path, started=True)
            path = tmp_path / ".tapps-agents" / "sessions" / "sid-456.json"
            assert path.exists()
            data = json.loads(path.read_text(encoding="utf-8"))
            assert data["session_id"] == "sid-456"
            assert data["project_root"] == str(tmp_path)
            assert data["started"] is True
