"""
Metrics Integration Module

Provides integration between enhanced metrics and existing codebase.
Allows gradual migration to enhanced metrics while maintaining backward compatibility.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .execution_metrics import ExecutionMetricsCollector
from .metrics_enhancements import EnhancedExecutionMetricsCollector

logger = logging.getLogger(__name__)


def get_metrics_collector(
    use_enhanced: bool = True,
    metrics_dir: Path | None = None,
    project_root: Path | None = None,
    **kwargs: Any,
) -> ExecutionMetricsCollector | EnhancedExecutionMetricsCollector:
    """
    Get metrics collector (enhanced or standard).
    
    Args:
        use_enhanced: Whether to use enhanced collector (default: True)
        metrics_dir: Directory to store metrics
        project_root: Project root directory
        **kwargs: Additional arguments for enhanced collector
        
    Returns:
        Metrics collector instance
    """
    if use_enhanced:
        return EnhancedExecutionMetricsCollector(
            metrics_dir=metrics_dir,
            project_root=project_root,
            **kwargs,
        )
    else:
        return ExecutionMetricsCollector(
            metrics_dir=metrics_dir,
            project_root=project_root,
        )


class MetricsCollectorAdapter:
    """
    Adapter to use enhanced metrics collector with existing code.
    
    Provides backward-compatible interface while using enhanced features.
    """

    def __init__(
        self,
        use_enhanced: bool = True,
        metrics_dir: Path | None = None,
        project_root: Path | None = None,
        **enhanced_kwargs: Any,
    ):
        """
        Initialize adapter.
        
        Args:
            use_enhanced: Whether to use enhanced collector
            metrics_dir: Directory to store metrics
            project_root: Project root directory
            **enhanced_kwargs: Additional arguments for enhanced collector
        """
        self.collector = get_metrics_collector(
            use_enhanced=use_enhanced,
            metrics_dir=metrics_dir,
            project_root=project_root,
            **enhanced_kwargs,
        )
        self.use_enhanced = use_enhanced

    def record_execution(
        self,
        workflow_id: str,
        step_id: str,
        command: str,
        status: str,
        duration_ms: float,
        retry_count: int = 0,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Record execution metric (backward compatible).
        
        Returns:
            ExecutionMetric instance
        """
        if self.use_enhanced and isinstance(self.collector, EnhancedExecutionMetricsCollector):
            return self.collector.record_execution(
                workflow_id=workflow_id,
                step_id=step_id,
                command=command,
                status=status,
                duration_ms=duration_ms,
                retry_count=retry_count,
                started_at=started_at,
                completed_at=completed_at,
                error_message=error_message,
                metadata=metadata,
            )
        else:
            return self.collector.record_execution(
                workflow_id=workflow_id,
                step_id=step_id,
                command=command,
                status=status,
                duration_ms=duration_ms,
                retry_count=retry_count,
                started_at=started_at,
                completed_at=completed_at,
                error_message=error_message,
            )

    def get_metrics(
        self,
        workflow_id: str | None = None,
        step_id: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        """
        Get metrics with enhanced filtering (backward compatible).
        
        Returns:
            List of ExecutionMetric instances
        """
        if self.use_enhanced and isinstance(self.collector, EnhancedExecutionMetricsCollector):
            return self.collector.get_metrics(
                workflow_id=workflow_id,
                step_id=step_id,
                status=status,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset,
            )
        else:
            # Standard collector doesn't support date range or offset
            return self.collector.get_metrics(
                workflow_id=workflow_id,
                step_id=step_id,
                status=status,
                limit=limit,
            )

    def get_summary(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get metrics summary with optional date range (backward compatible).
        
        Returns:
            Summary dictionary
        """
        if self.use_enhanced and isinstance(self.collector, EnhancedExecutionMetricsCollector):
            return self.collector.get_summary(
                start_date=start_date,
                end_date=end_date,
            )
        else:
            return self.collector.get_summary()

    def flush(self) -> None:
        """Flush write buffer (enhanced only)."""
        if self.use_enhanced and isinstance(self.collector, EnhancedExecutionMetricsCollector):
            self.collector.flush()

    def cleanup_old_metrics(self, days_to_keep: int | None = None) -> int:
        """
        Clean up old metrics (enhanced only).
        
        Returns:
            Number of files deleted
        """
        if self.use_enhanced and isinstance(self.collector, EnhancedExecutionMetricsCollector):
            return self.collector.cleanup_old_metrics(days_to_keep=days_to_keep)
        return 0

    def get_stats(self) -> dict[str, Any]:
        """Get collector statistics (enhanced only)."""
        if self.use_enhanced and isinstance(self.collector, EnhancedExecutionMetricsCollector):
            return self.collector.get_stats()
        return {}
