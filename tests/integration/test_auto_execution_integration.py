"""
Integration tests for Background Agent auto-execution.

Tests the integration between workflow executor and auto-execution system.
"""

from __future__ import annotations

import pytest
from pathlib import Path
import asyncio

from tests.fixtures.background_agent_fixtures import (
    MockBackgroundAgent,
)


@pytest.mark.asyncio
async def test_auto_executor_with_mock_agent(temp_project_root: Path, mock_background_agent: MockBackgroundAgent):
    """Test auto-executor with mock Background Agent."""
    from tapps_agents.workflow.background_auto_executor import BackgroundAgentAutoExecutor

    executor = BackgroundAgentAutoExecutor(
        polling_interval=0.1,
        timeout_seconds=5.0,
        project_root=temp_project_root,
        enable_metrics=True,
        enable_audit=True,
    )

    # Start mock agent execution in background
    execution_task = asyncio.create_task(
        mock_background_agent.simulate_execution(
            workflow_id="test-workflow",
            step_id="test-step",
            success=True,
            artifacts=["test.md"],
        )
    )

    # Execute command
    result = await executor.execute_command(
        command="@analyst gather-requirements --target-file test.md",
        worktree_path=mock_background_agent.worktree_path,
        workflow_id="test-workflow",
        step_id="test-step",
    )

    # Wait for mock agent to complete
    await execution_task

    # Verify result
    assert result["status"] == "completed"
    assert result["success"] is True
    assert "test.md" in result.get("artifacts", [])


@pytest.mark.asyncio
async def test_auto_executor_timeout(temp_project_root: Path):
    """Test auto-executor timeout handling."""
    from tapps_agents.workflow.background_auto_executor import BackgroundAgentAutoExecutor

    executor = BackgroundAgentAutoExecutor(
        polling_interval=0.1,
        timeout_seconds=0.5,  # Short timeout
        project_root=temp_project_root,
    )

    # Create worktree but don't create status file (will timeout)
    worktree_path = temp_project_root / "worktree"
    worktree_path.mkdir()
    (worktree_path / ".cursor").mkdir(exist_ok=True)

    result = await executor.execute_command(
        command="@analyst gather-requirements",
        worktree_path=worktree_path,
        workflow_id="test-workflow",
        step_id="test-step",
    )

    # Should timeout
    assert result["status"] == "timeout"
    assert result["success"] is False


@pytest.mark.asyncio
async def test_auto_executor_metrics_collection(temp_project_root: Path, mock_background_agent: MockBackgroundAgent):
    """Test metrics collection during auto-execution."""
    from tapps_agents.workflow.background_auto_executor import BackgroundAgentAutoExecutor
    from tapps_agents.workflow.execution_metrics import ExecutionMetricsCollector

    executor = BackgroundAgentAutoExecutor(
        polling_interval=0.1,
        timeout_seconds=5.0,
        project_root=temp_project_root,
        enable_metrics=True,
    )

    # Execute command
    execution_task = asyncio.create_task(
        mock_background_agent.simulate_execution(
            workflow_id="test-workflow",
            step_id="test-step",
            success=True,
        )
    )

    await executor.execute_command(
        command="@analyst gather-requirements",
        worktree_path=mock_background_agent.worktree_path,
        workflow_id="test-workflow",
        step_id="test-step",
    )

    await execution_task

    # Check metrics
    collector = ExecutionMetricsCollector(project_root=temp_project_root)
    metrics = collector.get_metrics(workflow_id="test-workflow", limit=10)

    assert len(metrics) >= 1
    assert metrics[0].workflow_id == "test-workflow"
    assert metrics[0].status == "success"


@pytest.mark.asyncio
async def test_auto_executor_audit_logging(temp_project_root: Path, mock_background_agent: MockBackgroundAgent):
    """Test audit logging during auto-execution."""
    from tapps_agents.workflow.background_auto_executor import BackgroundAgentAutoExecutor
    from tapps_agents.workflow.audit_logger import AuditLogger

    executor = BackgroundAgentAutoExecutor(
        polling_interval=0.1,
        timeout_seconds=5.0,
        project_root=temp_project_root,
        enable_audit=True,
    )

    # Execute command
    execution_task = asyncio.create_task(
        mock_background_agent.simulate_execution(
            workflow_id="test-workflow",
            step_id="test-step",
            success=True,
        )
    )

    await executor.execute_command(
        command="@analyst gather-requirements",
        worktree_path=mock_background_agent.worktree_path,
        workflow_id="test-workflow",
        step_id="test-step",
    )

    await execution_task

    # Check audit log
    logger = AuditLogger(project_root=temp_project_root)
    events = logger.query_events(workflow_id="test-workflow", limit=10)

    assert len(events) >= 2  # At least command_detected and execution_completed
    event_types = [e["event_type"] for e in events]
    assert "command_detected" in event_types
    assert "execution_completed" in event_types or "execution_started" in event_types

