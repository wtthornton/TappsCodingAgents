"""
Analytics Data Access Layer for Cursor Integration

Epic 15 / Story 15.1: Analytics Data Access
Provides unified interface for accessing analytics data with caching and query optimization.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..core.analytics_dashboard import AnalyticsDashboard

logger = logging.getLogger(__name__)


class CursorAnalyticsAccessor:
    """
    Analytics data access layer for Cursor integration.
    
    Provides unified interface for fetching analytics metrics with caching
    and query optimization.
    """

    def __init__(
        self,
        analytics_dir: Path | None = None,
        cache_ttl_seconds: int = 60,
        enable_cache: bool = True,
    ):
        """
        Initialize analytics accessor.

        Args:
            analytics_dir: Directory for analytics data
            cache_ttl_seconds: Cache TTL in seconds (default: 60)
            enable_cache: Whether to enable caching (default: True)
        """
        self.dashboard = AnalyticsDashboard(analytics_dir)
        self.cache_ttl = cache_ttl_seconds
        self.enable_cache = enable_cache
        
        # Cache storage
        self._cache: dict[str, tuple[datetime, Any]] = {}
        
    def _get_cache_key(self, query_type: str, **filters: Any) -> str:
        """Generate cache key from query type and filters."""
        filter_str = "_".join(f"{k}={v}" for k, v in sorted(filters.items()))
        return f"{query_type}:{filter_str}"
    
    def _is_cache_valid(self, cache_entry: tuple[datetime, Any]) -> bool:
        """Check if cache entry is still valid."""
        if not self.enable_cache:
            return False
        cached_time, _ = cache_entry
        age = (datetime.now() - cached_time).total_seconds()
        return age < self.cache_ttl
    
    def _get_from_cache(self, cache_key: str) -> Any | None:
        """Get value from cache if valid."""
        if not self.enable_cache:
            return None
        
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if self._is_cache_valid(entry):
                logger.debug(f"Cache hit: {cache_key}")
                return entry[1]
            else:
                # Remove expired entry
                del self._cache[cache_key]
        
        return None
    
    def _set_cache(self, cache_key: str, value: Any) -> None:
        """Set value in cache."""
        if self.enable_cache:
            self._cache[cache_key] = (datetime.now(), value)
            logger.debug(f"Cached: {cache_key}")
    
    def invalidate_cache(self, query_type: str | None = None) -> None:
        """
        Invalidate cache entries.
        
        Args:
            query_type: Optional query type to invalidate (invalidates all if None)
        """
        if query_type:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{query_type}:")]
            for key in keys_to_remove:
                del self._cache[key]
            logger.debug(f"Invalidated cache for: {query_type}")
        else:
            self._cache.clear()
            logger.debug("Invalidated all cache")
    
    def get_system_metrics(self, use_cache: bool = True) -> dict[str, Any]:
        """
        Get system metrics.
        
        Args:
            use_cache: Whether to use cache
            
        Returns:
            System metrics dictionary
        """
        cache_key = self._get_cache_key("system")
        
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached
        
        metrics = self.dashboard.get_system_status()
        
        if use_cache:
            self._set_cache(cache_key, metrics)
        
        return metrics
    
    def get_agent_metrics(
        self,
        agent_id: str | None = None,
        days: int = 30,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Get agent performance metrics.
        
        Args:
            agent_id: Optional agent ID to filter by
            days: Number of days to look back
            use_cache: Whether to use cache
            
        Returns:
            List of agent metrics dictionaries
        """
        cache_key = self._get_cache_key("agents", agent_id=agent_id, days=days)
        
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached
        
        metrics = self.dashboard.get_agent_performance(agent_id=agent_id)
        
        # Filter by days if needed (dashboard doesn't support days filter directly)
        if days < 30:
            cutoff = datetime.now() - timedelta(days=days)
            filtered = []
            for metric in metrics:
                if metric.get("last_execution"):
                    last_exec = datetime.fromisoformat(metric["last_execution"])
                    if last_exec >= cutoff:
                        filtered.append(metric)
            metrics = filtered
        
        if use_cache:
            self._set_cache(cache_key, metrics)
        
        return metrics
    
    def get_workflow_metrics(
        self,
        workflow_id: str | None = None,
        days: int = 30,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Get workflow performance metrics.
        
        Args:
            workflow_id: Optional workflow ID to filter by
            days: Number of days to look back
            use_cache: Whether to use cache
            
        Returns:
            List of workflow metrics dictionaries
        """
        cache_key = self._get_cache_key("workflows", workflow_id=workflow_id, days=days)
        
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached
        
        metrics = self.dashboard.get_workflow_performance(workflow_id=workflow_id)
        
        # Filter by days if needed
        if days < 30:
            cutoff = datetime.now() - timedelta(days=days)
            filtered = []
            for metric in metrics:
                if metric.get("last_execution"):
                    last_exec = datetime.fromisoformat(metric["last_execution"])
                    if last_exec >= cutoff:
                        filtered.append(metric)
            metrics = filtered
        
        if use_cache:
            self._set_cache(cache_key, metrics)
        
        return metrics
    
    def get_trends(
        self,
        metric_type: str,
        days: int = 30,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Get trend data.
        
        Args:
            metric_type: Type of metric (agent_duration, workflow_duration, etc.)
            days: Number of days to look back
            use_cache: Whether to use cache
            
        Returns:
            List of trend data dictionaries
        """
        cache_key = self._get_cache_key("trends", metric_type=metric_type, days=days)
        
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached
        
        trends = self.dashboard.get_trends(metric_type, days=days)
        
        if use_cache:
            self._set_cache(cache_key, trends)
        
        return trends
    
    def get_dashboard_data(self, use_cache: bool = True) -> dict[str, Any]:
        """
        Get comprehensive dashboard data.
        
        Args:
            use_cache: Whether to use cache
            
        Returns:
            Complete dashboard data dictionary
        """
        cache_key = self._get_cache_key("dashboard")
        
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached
        
        data = self.dashboard.get_dashboard_data()
        
        if use_cache:
            self._set_cache(cache_key, data)
        
        return data
    
    def aggregate_metrics(
        self,
        metrics: list[dict[str, Any]],
        aggregation_type: str = "summary",
    ) -> dict[str, Any]:
        """
        Aggregate metrics into summary statistics.
        
        Args:
            metrics: List of metric dictionaries
            aggregation_type: Type of aggregation (summary, totals, averages)
            
        Returns:
            Aggregated metrics dictionary
        """
        if not metrics:
            return {
                "count": 0,
                "total": 0,
                "average": 0.0,
                "min": 0.0,
                "max": 0.0,
            }
        
        if aggregation_type == "summary":
            # Calculate summary statistics
            total_executions = sum(m.get("total_executions", 0) for m in metrics)
            total_successful = sum(m.get("successful_executions", 0) for m in metrics)
            total_failed = sum(m.get("failed_executions", 0) for m in metrics)
            
            durations = []
            for m in metrics:
                if "average_duration" in m:
                    durations.append(m["average_duration"])
            
            avg_duration = sum(durations) / len(durations) if durations else 0.0
            min_duration = min(durations) if durations else 0.0
            max_duration = max(durations) if durations else 0.0
            
            success_rate = (
                total_successful / total_executions if total_executions > 0 else 0.0
            )
            
            return {
                "count": len(metrics),
                "total_executions": total_executions,
                "total_successful": total_successful,
                "total_failed": total_failed,
                "success_rate": success_rate,
                "average_duration": avg_duration,
                "min_duration": min_duration,
                "max_duration": max_duration,
            }
        
        elif aggregation_type == "totals":
            return {
                "count": len(metrics),
                "total_executions": sum(m.get("total_executions", 0) for m in metrics),
                "total_successful": sum(m.get("successful_executions", 0) for m in metrics),
                "total_failed": sum(m.get("failed_executions", 0) for m in metrics),
            }
        
        elif aggregation_type == "averages":
            durations = [m.get("average_duration", 0.0) for m in metrics if "average_duration" in m]
            success_rates = [m.get("success_rate", 0.0) for m in metrics if "success_rate" in m]
            
            return {
                "count": len(metrics),
                "average_duration": sum(durations) / len(durations) if durations else 0.0,
                "average_success_rate": sum(success_rates) / len(success_rates) if success_rates else 0.0,
            }
        
        else:
            return {"count": len(metrics)}

