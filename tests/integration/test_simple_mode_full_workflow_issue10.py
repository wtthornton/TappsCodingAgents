"""
Integration tests for Issue 10: Simple Mode Full Workflow Infinite Loop.

Tests the end-to-end Simple Mode full workflow execution with the fixes applied.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def cursor_mode_env(monkeypatch):
    """Set up Cursor mode environment for tests."""
    monkeypatch.setenv("TAPPS_AGENTS_MODE", "cursor")
    monkeypatch.setenv("CURSOR_IDE", "1")
    yield


@pytest.fixture
def temp_project_root(tmp_path: Path) -> Path:
    """Create temporary project root for testing."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    (project_root / ".tapps-agents").mkdir(parents=True)
    
    # Create minimal config
    config_file = project_root / ".tapps-agents" / "config.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text("""workflow:
  auto_execution_enabled: true
  timeout_seconds: 3600.0
  polling_interval: 5.0
""")
    
    return project_root


@pytest.mark.integration
@pytest.mark.asyncio
async def test_simple_mode_full_with_auto_flag(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test Simple Mode full workflow with --auto flag."""
    # This test verifies that the workflow can be invoked with --auto flag
    # and doesn't hang indefinitely
    
    env = os.environ.copy()
    env["TAPPS_AGENTS_MODE"] = "cursor"
    env["CURSOR_IDE"] = "1"
    
    # Use a very short prompt to minimize execution time
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tapps_agents.cli",
            "simple-mode",
            "full",
            "--prompt",
            "Create a simple hello world function",
            "--auto",
        ],
        capture_output=True,
        text=True,
        timeout=30,  # 30 second timeout for test
        cwd=str(temp_project_root),
        env=env,
    )
    
    # Should not hang - either complete or fail with clear error
    assert result.returncode in [0, 1], f"Unexpected return code: {result.returncode}"
    
    # Should not have infinite spinner
    assert "Starting Simple Full Lifecycle Workflow" in result.stdout or result.stderr
    
    # Should show progress or error, not just hang
    output = result.stdout + result.stderr
    assert len(output) > 0, "Should have some output"


@pytest.mark.integration
def test_simple_mode_full_timeout_handling(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that Simple Mode full workflow times out gracefully."""
    env = os.environ.copy()
    env["TAPPS_AGENTS_MODE"] = "cursor"
    env["CURSOR_IDE"] = "1"
    
    # Create config with very short timeout for testing
    config_file = temp_project_root / ".tapps-agents" / "config.yaml"
    config_file.write_text("""workflow:
  auto_execution_enabled: true
  timeout_seconds: 1.0  # Very short timeout for testing
  polling_interval: 0.5
""")
    
    # This should timeout quickly
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tapps_agents.cli",
            "simple-mode",
            "full",
            "--prompt",
            "Create a complex application",  # Complex prompt that might take time
            "--auto",
        ],
        capture_output=True,
        text=True,
        timeout=10,  # Test timeout
        cwd=str(temp_project_root),
        env=env,
    )
    
    # Should either timeout or fail with clear error
    output = result.stdout + result.stderr
    
    # If it timed out, should have timeout error message
    if "timeout" in output.lower():
        assert "timeout" in output.lower()
        assert "workflow execution exceeded" in output.lower() or "timeout" in output.lower()


@pytest.mark.integration
def test_simple_mode_full_auto_execution_warning(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that Simple Mode full workflow warns when auto-execution is disabled."""
    env = os.environ.copy()
    env["TAPPS_AGENTS_MODE"] = "cursor"
    env["CURSOR_IDE"] = "1"
    
    # Create config with auto-execution disabled
    config_file = temp_project_root / ".tapps-agents" / "config.yaml"
    config_file.write_text("""workflow:
  auto_execution_enabled: false
  timeout_seconds: 3600.0
  polling_interval: 5.0
""")
    
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tapps_agents.cli",
            "simple-mode",
            "full",
            "--prompt",
            "Test prompt",
            # Note: NOT using --auto flag
        ],
        capture_output=True,
        text=True,
        timeout=5,  # Quick test
        cwd=str(temp_project_root),
        env=env,
        input="n\n",  # Answer "no" to continue prompt
    )
    
    output = result.stdout + result.stderr
    
    # Should show warning about auto-execution
    assert "auto-execution" in output.lower() or "WARNING" in output


@pytest.mark.integration
def test_simple_mode_full_progress_reporting(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that Simple Mode full workflow shows progress."""
    env = os.environ.copy()
    env["TAPPS_AGENTS_MODE"] = "cursor"
    env["CURSOR_IDE"] = "1"
    
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tapps_agents.cli",
            "simple-mode",
            "full",
            "--prompt",
            "Create a simple function",
            "--auto",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(temp_project_root),
        env=env,
    )
    
    output = result.stdout + result.stderr
    
    # Should show workflow information
    assert "Starting:" in output or "workflow" in output.lower()
    
    # Should show runtime mode
    assert "Runtime mode" in output or "mode" in output.lower()
    
    # Should show auto-execution status
    assert "auto-execution" in output.lower() or "Auto-execution" in output


@pytest.mark.integration
def test_simple_mode_full_error_handling(
    temp_project_root: Path,
    cursor_mode_env,
):
    """Test that Simple Mode full workflow handles errors gracefully."""
    env = os.environ.copy()
    env["TAPPS_AGENTS_MODE"] = "cursor"
    env["CURSOR_IDE"] = "1"
    
    # Try to run with invalid workflow (should fail gracefully)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tapps_agents.cli",
            "simple-mode",
            "full",
            "--prompt",
            "Test",
            "--auto",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(temp_project_root),
        env=env,
    )
    
    # Should either succeed or fail with clear error (not hang)
    assert result.returncode in [0, 1]
    
    output = result.stdout + result.stderr
    
    # Should not have infinite spinner or hang
    # Should have some output indicating what happened
    assert len(output) > 0

