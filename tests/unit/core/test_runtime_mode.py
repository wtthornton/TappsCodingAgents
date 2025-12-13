"""
Tests for runtime mode detection (Cursor-first policy).
"""

import os

import pytest

from tapps_agents.core.runtime_mode import RuntimeMode, detect_runtime_mode


pytestmark = pytest.mark.unit


class TestDetectRuntimeMode:
    def test_explicit_cursor_mode(self, monkeypatch):
        monkeypatch.setenv("TAPPS_AGENTS_MODE", "cursor")
        assert detect_runtime_mode() == RuntimeMode.CURSOR

    def test_explicit_background_maps_to_cursor(self, monkeypatch):
        monkeypatch.setenv("TAPPS_AGENTS_MODE", "background")
        assert detect_runtime_mode() == RuntimeMode.CURSOR

    def test_explicit_headless_mode(self, monkeypatch):
        monkeypatch.setenv("TAPPS_AGENTS_MODE", "headless")
        assert detect_runtime_mode() == RuntimeMode.HEADLESS

    def test_explicit_cli_maps_to_headless(self, monkeypatch):
        monkeypatch.setenv("TAPPS_AGENTS_MODE", "cli")
        assert detect_runtime_mode() == RuntimeMode.HEADLESS

    def test_auto_detect_cursor_markers(self, monkeypatch):
        monkeypatch.delenv("TAPPS_AGENTS_MODE", raising=False)
        # Ensure no other cursor markers are set from the environment running the tests
        for key in (
            "CURSOR",
            "CURSOR_IDE",
            "CURSOR_SESSION_ID",
            "CURSOR_WORKSPACE_ROOT",
            "CURSOR_TRACE_ID",
        ):
            monkeypatch.delenv(key, raising=False)

        monkeypatch.setenv("CURSOR_SESSION_ID", "test-session")
        assert detect_runtime_mode() == RuntimeMode.CURSOR

    def test_default_is_headless(self, monkeypatch):
        monkeypatch.delenv("TAPPS_AGENTS_MODE", raising=False)
        for key in (
            "CURSOR",
            "CURSOR_IDE",
            "CURSOR_SESSION_ID",
            "CURSOR_WORKSPACE_ROOT",
            "CURSOR_TRACE_ID",
        ):
            monkeypatch.delenv(key, raising=False)
        assert detect_runtime_mode() == RuntimeMode.HEADLESS


