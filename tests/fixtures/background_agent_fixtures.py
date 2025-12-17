"""
Test fixtures for Background Agent auto-execution testing.

Provides mock Background Agent simulators and test utilities.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest


@pytest.fixture
def temp_project_root(tmp_path: Path) -> Path:
    """Create a temporary project root directory."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    (project_root / ".cursor").mkdir(exist_ok=True)
    (project_root / ".tapps-agents").mkdir(exist_ok=True)
    return project_root


@pytest.fixture
def mock_background_agent_config(temp_project_root: Path) -> Path:
    """Create a mock Background Agent configuration file."""
    config_path = temp_project_root / ".cursor" / "background-agents.yaml"
    config = {
        "agents": [
            {
                "name": "Test Workflow Executor",
                "type": "background",
                "commands": [
                    "python -m tapps_agents.cli workflow execute-skill-command --command-file {command_file_path}"
                ],
                "watch_paths": [".cursor-skill-command.txt"],
            }
        ]
    }
    import yaml

    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path


@pytest.fixture
def mock_command_file(temp_project_root: Path) -> Path:
    """Create a mock command file."""
    command_file = temp_project_root / ".cursor" / ".cursor-skill-command.txt"
    command_file.write_text("@analyst gather-requirements --target-file test.md")
    return command_file


@pytest.fixture
def mock_status_file(temp_project_root: Path) -> Path:
    """Create a mock status file."""
    status_file = temp_project_root / ".cursor" / ".cursor-skill-status.json"
    status_data = {
        "workflow_id": "test-workflow",
        "step_id": "test-step",
        "status": "completed",
        "success": True,
        "artifacts": ["test.md"],
    }
    with open(status_file, "w") as f:
        json.dump(status_data, f)
    return status_file


class MockBackgroundAgent:
    """Mock Background Agent simulator for testing."""

    def __init__(self, worktree_path: Path, delay_seconds: float = 0.1):
        """
        Initialize mock Background Agent.

        Args:
            worktree_path: Path to worktree
            delay_seconds: Delay before simulating completion
        """
        self.worktree_path = worktree_path
        self.delay_seconds = delay_seconds
        self.command_file = worktree_path / ".cursor" / ".cursor-skill-command.txt"
        self.status_file = worktree_path / ".cursor" / ".cursor-skill-status.json"

    async def simulate_execution(
        self,
        workflow_id: str = "test-workflow",
        step_id: str = "test-step",
        success: bool = True,
        artifacts: list[str] | None = None,
        error_message: str | None = None,
    ) -> None:
        """
        Simulate Background Agent execution.

        Args:
            workflow_id: Workflow ID
            step_id: Step ID
            success: Whether execution succeeded
            artifacts: List of artifact paths
            error_message: Error message if failed
        """
        import asyncio

        # Wait for delay to simulate execution time
        await asyncio.sleep(self.delay_seconds)

        # Read command file
        if self.command_file.exists():
            command = self.command_file.read_text()

        # Create status file
        status_data = {
            "workflow_id": workflow_id,
            "step_id": step_id,
            "status": "completed" if success else "failed",
            "success": success,
            "artifacts": artifacts or [],
        }
        if error_message:
            status_data["error"] = error_message

        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.status_file, "w") as f:
            json.dump(status_data, f)

        # Clean up command file
        if self.command_file.exists():
            self.command_file.unlink()


@pytest.fixture
def mock_background_agent(temp_project_root: Path) -> MockBackgroundAgent:
    """Create a mock Background Agent."""
    worktree_path = temp_project_root / "worktree"
    worktree_path.mkdir()
    (worktree_path / ".cursor").mkdir(exist_ok=True)
    return MockBackgroundAgent(worktree_path=worktree_path)


@pytest.fixture
def auto_execution_config_file(temp_project_root: Path) -> Path:
    """Create a test auto-execution configuration file."""
    config_path = temp_project_root / ".tapps-agents" / "auto_execution_config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "auto_execution": {
            "enabled": True,
            "retry": {
                "enabled": True,
                "max_attempts": 3,
                "backoff_multiplier": 2.0,
                "initial_delay_seconds": 1.0,
            },
            "polling": {
                "enabled": True,
                "interval_seconds": 0.5,  # Fast for testing
                "timeout_seconds": 10.0,  # Short for testing
            },
            "features": {
                "artifact_detection": True,
                "status_tracking": True,
                "error_handling": True,
                "metrics_collection": True,
                "audit_logging": True,
            },
            "version": "1.0",
        }
    }
    import yaml

    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path

