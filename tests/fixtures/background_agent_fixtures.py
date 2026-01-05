"""
Fixtures for Background Agent auto-execution tests.

Provides mock Background Agent and test configuration fixtures.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from tapps_agents.workflow.cursor_skill_helper import write_structured_status_file


class MockBackgroundAgent:
    """Mock Background Agent for testing auto-execution."""

    def __init__(self, worktree_path: Path):
        """
        Initialize mock Background Agent.

        Args:
            worktree_path: Path to worktree directory
        """
        self.worktree_path = worktree_path
        self.worktree_path.mkdir(parents=True, exist_ok=True)
        (self.worktree_path / ".cursor").mkdir(exist_ok=True)

    async def simulate_execution(
        self,
        workflow_id: str,
        step_id: str,
        success: bool = True,
        artifacts: list[str] | None = None,
        delay: float = 0.1,
    ) -> None:
        """
        Simulate Background Agent execution.

        Args:
            workflow_id: Workflow ID
            step_id: Step ID
            success: Whether execution should succeed
            artifacts: List of artifact paths to create
            delay: Delay before completing (seconds)
        """
        # Small delay to simulate execution
        await asyncio.sleep(delay)

        status_file = self.worktree_path / ".cursor" / ".cursor-skill-status.json"

        if success:
            write_structured_status_file(
                status_file=status_file,
                status="completed",
                artifacts=artifacts or [],
                metadata={"workflow_id": workflow_id, "step_id": step_id},
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
            )
        else:
            write_structured_status_file(
                status_file=status_file,
                status="failed",
                error={
                    "message": "Simulated failure",
                    "code": "MOCK_ERROR",
                    "retryable": False,
                },
                metadata={"workflow_id": workflow_id, "step_id": step_id},
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
            )


@pytest.fixture
def temp_project_root(tmp_path: Path) -> Path:
    """
    Create temporary project root directory for tests.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Path to temporary project root
    """
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    (project_root / ".tapps-agents").mkdir(exist_ok=True)
    return project_root


@pytest.fixture
def auto_execution_config_file(temp_project_root: Path) -> Path:
    """
    Create auto-execution config file for tests.

    Args:
        temp_project_root: Temporary project root directory

    Returns:
        Path to config file
    """
    config_file = temp_project_root / ".tapps-agents" / "auto-execution.yaml"
    config_data = {
        "enabled": True,
        "polling_interval": 0.1,
        "timeout_seconds": 5.0,
    }
    config_file.write_text(json.dumps(config_data, indent=2), encoding="utf-8")
    return config_file


@pytest.fixture
def mock_background_agent(temp_project_root: Path) -> MockBackgroundAgent:
    """
    Create mock Background Agent fixture.

    Args:
        temp_project_root: Temporary project root directory

    Returns:
        MockBackgroundAgent instance
    """
    worktree_path = temp_project_root / "worktree"
    return MockBackgroundAgent(worktree_path=worktree_path)
