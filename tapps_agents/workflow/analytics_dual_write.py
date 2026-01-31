"""
Dual-write from execution metrics to analytics.

When ExecutionMetricsCollector records a step or when a workflow completes,
optionally also write to AnalyticsCollector so health overview "usage" and
outcomes have real data. Best-effort: analytics failures do not block execution.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _should_record_from_execution(project_root: Path | None) -> bool:
    """Return True if config enables analytics record_from_execution."""
    try:
        from ..core.config import load_config

        config = load_config()
        return getattr(config.analytics, "record_from_execution", True)
    except Exception:  # pylint: disable=broad-except
        return True


def _get_analytics_collector(project_root: Path | None) -> Any | None:
    """Return AnalyticsCollector for project_root, or None on failure."""
    try:
        from ..core.analytics_dashboard import AnalyticsCollector

        root = project_root or Path.cwd()
        analytics_dir = root / ".tapps-agents" / "analytics"
        return AnalyticsCollector(analytics_dir=analytics_dir)
    except Exception:  # pylint: disable=broad-except
        return None


def record_agent_execution_to_analytics(
    project_root: Path | None,
    agent_id: str,
    agent_name: str,
    duration_seconds: float,
    success: bool,
    timestamp: datetime | None = None,
) -> None:
    """
    Best-effort dual-write: record one agent/step execution to analytics.

    Called after ExecutionMetricsCollector.record_execution (or enhanced).
    Does not raise; analytics failure does not block execution metrics.
    """
    if not _should_record_from_execution(project_root):
        return
    collector = _get_analytics_collector(project_root)
    if not collector:
        return
    try:
        collector.record_agent_execution(
            agent_id=agent_id,
            agent_name=agent_name,
            duration=duration_seconds,
            success=success,
            timestamp=timestamp,
        )
    except Exception as e:  # pylint: disable=broad-except
        logger.debug("Analytics dual-write (agent) failed: %s", e)


def record_workflow_execution_to_analytics(
    project_root: Path | None,
    workflow_id: str,
    workflow_name: str,
    duration_seconds: float,
    steps: int,
    success: bool,
    timestamp: datetime | None = None,
) -> None:
    """
    Best-effort dual-write: record workflow completion to analytics.

    Call when a workflow completes (status completed or failed).
    Does not raise; analytics failure does not block execution.
    """
    if not _should_record_from_execution(project_root):
        return
    collector = _get_analytics_collector(project_root)
    if not collector:
        return
    try:
        collector.record_workflow_execution(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            duration=duration_seconds,
            steps=steps,
            success=success,
            timestamp=timestamp,
        )
    except Exception as e:  # pylint: disable=broad-except
        logger.debug("Analytics dual-write (workflow) failed: %s", e)
