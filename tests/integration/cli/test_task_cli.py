"""
Integration tests for task CLI: create, list, show, update, close, hydrate, dehydrate.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Ensure subprocess uses project root so "task" command is available
# tests/integration/cli/test_task_cli.py -> cli=0, integration=1, tests=2, repo=3
_REPO_ROOT = Path(__file__).resolve().parents[3]


def _task_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(_REPO_ROOT)
    return env


@pytest.mark.integration
def test_task_create_and_list(tmp_path: Path) -> None:
    """task create creates a spec file; task list shows it."""
    result = subprocess.run(
        [sys.executable, "-m", "tapps_agents.cli", "task", "create", "cli-test-1", "--title", "CLI test task"],
        cwd=tmp_path,
        env=_task_env(),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    spec_file = tmp_path / ".tapps-agents" / "task-specs" / "cli-test-1.yaml"
    assert spec_file.exists()

    result2 = subprocess.run(
        [sys.executable, "-m", "tapps_agents.cli", "task", "list"],
        cwd=tmp_path,
        env=_task_env(),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result2.returncode == 0
    assert "cli-test-1" in result2.stdout
    assert "CLI test task" in result2.stdout


@pytest.mark.integration
def test_task_show(tmp_path: Path) -> None:
    """task show displays spec by id."""
    subprocess.run(
        [sys.executable, "-m", "tapps_agents.cli", "task", "create", "show-me", "--title", "Show me"],
        cwd=tmp_path,
        env=_task_env(),
        capture_output=True,
        text=True,
        timeout=15,
    )
    result = subprocess.run(
        [sys.executable, "-m", "tapps_agents.cli", "task", "show", "show-me"],
        cwd=tmp_path,
        env=_task_env(),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0
    assert "show-me" in result.stdout
    assert "Show me" in result.stdout


@pytest.mark.integration
def test_task_update_and_close(tmp_path: Path) -> None:
    """task update --status and task close update the spec."""
    subprocess.run(
        [sys.executable, "-m", "tapps_agents.cli", "task", "create", "close-me", "--title", "Close me"],
        cwd=tmp_path,
        env=_task_env(),
        capture_output=True,
        text=True,
        timeout=15,
    )
    result = subprocess.run(
        [sys.executable, "-m", "tapps_agents.cli", "task", "update", "close-me", "--status", "in-progress"],
        cwd=tmp_path,
        env=_task_env(),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0
    result2 = subprocess.run(
        [sys.executable, "-m", "tapps_agents.cli", "task", "close", "close-me"],
        cwd=tmp_path,
        env=_task_env(),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result2.returncode == 0
    result3 = subprocess.run(
        [sys.executable, "-m", "tapps_agents.cli", "task", "list", "--status", "done"],
        cwd=tmp_path,
        env=_task_env(),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result3.returncode == 0
    assert "close-me" in result3.stdout
