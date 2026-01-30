"""
Unit tests for tapps_agents.beads.client: resolve_bd_path, is_available, run_bd.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from tapps_agents.beads.client import (
    BeadsRequiredError,
    is_available,
    is_ready,
    require_beads,
    resolve_bd_path,
    run_bd,
)


@pytest.mark.unit
class TestResolveBdPath:
    """Tests for resolve_bd_path."""

    def test_prefers_tools_bd_exe_on_windows(self, tmp_path: Path) -> None:
        """When tools/bd/bd.exe exists on Windows, return it."""
        (tmp_path / "tools" / "bd").mkdir(parents=True)
        exe = tmp_path / "tools" / "bd" / "bd.exe"
        exe.write_text("", encoding="utf-8")
        with patch("tapps_agents.beads.client.sys.platform", "win32"):
            assert resolve_bd_path(tmp_path) == str(exe)

    def test_prefers_tools_bd_on_unix(self, tmp_path: Path) -> None:
        """When tools/bd/bd exists on non-Windows, return it."""
        (tmp_path / "tools" / "bd").mkdir(parents=True)
        bd = tmp_path / "tools" / "bd" / "bd"
        bd.write_text("", encoding="utf-8")
        with patch("tapps_agents.beads.client.sys.platform", "darwin"):
            assert resolve_bd_path(tmp_path) == str(bd)

    def test_returns_none_when_no_local_and_which_none(self, tmp_path: Path) -> None:
        """When tools/bd does not exist and bd not on PATH, return None."""
        with patch("tapps_agents.beads.client.shutil.which", return_value=None):
            assert resolve_bd_path(tmp_path) is None

    def test_returns_which_result_when_no_local(self, tmp_path: Path) -> None:
        """When tools/bd does not exist, return shutil.which('bd')."""
        with patch("tapps_agents.beads.client.shutil.which", return_value="/usr/bin/bd"):
            assert resolve_bd_path(tmp_path) == "/usr/bin/bd"


@pytest.mark.unit
class TestIsAvailable:
    """Tests for is_available."""

    def test_true_when_resolve_returns_path(self, tmp_path: Path) -> None:
        """is_available is True when resolve_bd_path returns a path."""
        (tmp_path / "tools" / "bd").mkdir(parents=True)
        (tmp_path / "tools" / "bd" / ("bd.exe" if sys.platform == "win32" else "bd")).write_text(
            "", encoding="utf-8"
        )
        assert is_available(tmp_path) is True

    def test_false_when_resolve_returns_none(self, tmp_path: Path) -> None:
        """is_available is False when resolve_bd_path returns None."""
        with patch("tapps_agents.beads.client.shutil.which", return_value=None):
            assert is_available(tmp_path) is False


@pytest.mark.unit
class TestIsReady:
    """Tests for is_ready (available and .beads exists)."""

    def test_true_when_available_and_beads_dir_exists(self, tmp_path: Path) -> None:
        """is_ready True when bd available and (project_root / ".beads").exists()."""
        (tmp_path / "tools" / "bd").mkdir(parents=True)
        (tmp_path / "tools" / "bd" / ("bd.exe" if sys.platform == "win32" else "bd")).write_text(
            "", encoding="utf-8"
        )
        (tmp_path / ".beads").mkdir()
        assert is_ready(tmp_path) is True

    def test_false_when_beads_dir_missing(self, tmp_path: Path) -> None:
        """is_ready False when bd available but .beads does not exist."""
        (tmp_path / "tools" / "bd").mkdir(parents=True)
        (tmp_path / "tools" / "bd" / ("bd.exe" if sys.platform == "win32" else "bd")).write_text(
            "", encoding="utf-8"
        )
        assert is_ready(tmp_path) is False

    def test_false_when_not_available(self, tmp_path: Path) -> None:
        """is_ready False when is_available is False (even if .beads exists)."""
        (tmp_path / ".beads").mkdir()
        with patch("tapps_agents.beads.client.shutil.which", return_value=None):
            assert is_ready(tmp_path) is False


@pytest.mark.unit
class TestRunBd:
    """Tests for run_bd."""

    def test_raises_when_bd_not_found(self, tmp_path: Path) -> None:
        """run_bd raises FileNotFoundError when bd cannot be resolved."""
        with patch("tapps_agents.beads.client.shutil.which", return_value=None):
            with pytest.raises(FileNotFoundError, match="bd not found"):
                run_bd(tmp_path, ["ready"])

    def test_calls_subprocess_with_resolved_path_and_args(self, tmp_path: Path) -> None:
        """run_bd invokes subprocess.run with [path, *args] and cwd."""
        fake_path = "/fake/tools/bd/bd.exe"
        with patch("tapps_agents.beads.client.resolve_bd_path", return_value=fake_path):
            with patch("tapps_agents.beads.client.subprocess.run") as m_run:
                m_run.return_value = type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
                run_bd(tmp_path, ["ready", "--foo"])
        m_run.assert_called_once()
        call_args = m_run.call_args
        assert call_args[0][0] == [fake_path, "ready", "--foo"]
        assert call_args[1]["cwd"] == tmp_path
        assert call_args[1]["capture_output"] is True

    def test_uses_cwd_override(self, tmp_path: Path) -> None:
        """run_bd uses cwd when provided."""
        fake_path = "/fake/bd"
        cwd_override = tmp_path / "other"
        cwd_override.mkdir(parents=True)
        with patch("tapps_agents.beads.client.resolve_bd_path", return_value=fake_path):
            with patch("tapps_agents.beads.client.subprocess.run") as m_run:
                m_run.return_value = type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
                run_bd(tmp_path, ["ready"], cwd=cwd_override)
        assert m_run.call_args[1]["cwd"] == cwd_override

    def test_capture_output_false(self, tmp_path: Path) -> None:
        """run_bd passes capture_output=False when requested."""
        with patch("tapps_agents.beads.client.resolve_bd_path", return_value="/fake/bd"):
            with patch("tapps_agents.beads.client.subprocess.run") as m_run:
                m_run.return_value = type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
                run_bd(tmp_path, ["ready"], capture_output=False)
        assert m_run.call_args[1]["capture_output"] is False


@pytest.mark.unit
class TestRequireBeads:
    """Tests for require_beads."""

    def test_no_op_when_beads_disabled(self, tmp_path: Path) -> None:
        """require_beads is a no-op when beads.enabled is False."""
        config = type("C", (), {"beads": type("B", (), {"enabled": False, "required": True})()})()
        require_beads(config, tmp_path)

    def test_no_op_when_required_false(self, tmp_path: Path) -> None:
        """require_beads is a no-op when beads.required is False."""
        config = type("C", (), {"beads": type("B", (), {"enabled": True, "required": False})()})()
        with patch("tapps_agents.beads.client.shutil.which", return_value=None):
            require_beads(config, tmp_path)

    def test_raises_when_required_and_bd_not_available(self, tmp_path: Path) -> None:
        """require_beads raises BeadsRequiredError when required and bd not found."""
        config = type("C", (), {"beads": type("B", (), {"enabled": True, "required": True})()})()
        with patch("tapps_agents.beads.client.shutil.which", return_value=None):
            with pytest.raises(BeadsRequiredError, match="bd was not found"):
                require_beads(config, tmp_path)

    def test_raises_when_required_and_beads_not_initialized(self, tmp_path: Path) -> None:
        """require_beads raises when required, bd available, but .beads missing."""
        (tmp_path / "tools" / "bd").mkdir(parents=True)
        (tmp_path / "tools" / "bd" / ("bd.exe" if sys.platform == "win32" else "bd")).write_text(
            "", encoding="utf-8"
        )
        config = type("C", (), {"beads": type("B", (), {"enabled": True, "required": True})()})()
        with pytest.raises(BeadsRequiredError, match="not initialized"):
            require_beads(config, tmp_path)

    def test_passes_when_required_and_ready(self, tmp_path: Path) -> None:
        """require_beads passes when required and bd is available and initialized."""
        (tmp_path / "tools" / "bd").mkdir(parents=True)
        (tmp_path / "tools" / "bd" / ("bd.exe" if sys.platform == "win32" else "bd")).write_text(
            "", encoding="utf-8"
        )
        (tmp_path / ".beads").mkdir()
        config = type("C", (), {"beads": type("B", (), {"enabled": True, "required": True})()})()
        require_beads(config, tmp_path)
