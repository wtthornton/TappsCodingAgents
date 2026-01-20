"""
Context7 Cache Health Check.

Checks Context7 knowledge base cache effectiveness and performance.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from ...context7.analytics import Analytics
from ...context7.cache_structure import CacheStructure
from ...context7.metadata import MetadataManager
from ...core.config import load_config
from ..base import HealthCheck, HealthCheckResult


class Context7CacheHealthCheck(HealthCheck):
    """Health check for Context7 cache effectiveness."""

    def __init__(self, project_root: Path | None = None, cache_root: Path | None = None):
        """
        Initialize Context7 cache health check.

        Args:
            project_root: Project root directory
            cache_root: Cache root directory (defaults to .tapps-agents/kb/context7-cache)
        """
        super().__init__(name="context7_cache", dependencies=["environment"])
        self.project_root = project_root or Path.cwd()
        self.config = load_config()

        # Determine cache root
        # Defensive: if knowledge_base.location is not a string (e.g. MagicMock in tests),
        # use default to avoid creating directories with mock reprs (e.g. "MagicMock/").
        if cache_root:
            self.cache_root = Path(cache_root)
        elif self.config.context7 and self.config.context7.knowledge_base:
            loc = getattr(self.config.context7.knowledge_base, "location", None)
            if isinstance(loc, str):
                self.cache_root = self.project_root / loc
            else:
                self.cache_root = self.project_root / ".tapps-agents" / "kb" / "context7-cache"
        else:
            self.cache_root = self.project_root / ".tapps-agents" / "kb" / "context7-cache"

        # Initialize cache structure and analytics
        self.cache_structure = CacheStructure(self.cache_root)
        self.metadata_manager = MetadataManager(self.cache_structure)
        self.analytics = Analytics(self.cache_structure, self.metadata_manager)

    def run(self) -> HealthCheckResult:
        """
        Run Context7 cache health check.

        Returns:
            HealthCheckResult with cache status
        """
        try:
            # Check if Context7 is enabled
            if not (self.config.context7 and self.config.context7.enabled):
                return HealthCheckResult(
                    name=self.name,
                    status="degraded",
                    score=50.0,
                    message="Context7 integration is disabled",
                    details={"enabled": False},
                    remediation=["Enable Context7 in .tapps-agents/config.yaml"],
                )

            # Check cache directory existence and permissions
            cache_exists = self.cache_root.exists()
            cache_writable = False
            if cache_exists:
                try:
                    test_file = self.cache_root / ".health_check_test"
                    test_file.write_text("test")
                    test_file.unlink()
                    cache_writable = True
                except Exception:
                    cache_writable = False

            if not cache_exists or not cache_writable:
                return HealthCheckResult(
                    name=self.name,
                    status="unhealthy",
                    score=0.0,
                    message=f"Cache directory not accessible: {self.cache_root}",
                    details={
                        "cache_root": str(self.cache_root),
                        "exists": cache_exists,
                        "writable": cache_writable,
                    },
                    remediation=[
                        f"Create cache directory: mkdir -p {self.cache_root}",
                        f"Fix permissions: chmod 755 {self.cache_root}",
                    ],
                )

            # Get cache metrics
            cache_metrics = self.analytics.get_cache_metrics()

            # Check if cache is empty
            if cache_metrics.total_entries == 0:
                return HealthCheckResult(
                    name=self.name,
                    status="degraded",
                    score=30.0,
                    message="Cache is empty - no entries found",
                    details={
                        "total_entries": 0,
                        "total_libraries": 0,
                        "cache_root": str(self.cache_root),
                    },
                    remediation=[
                        "Run cache pre-population: python scripts/prepopulate_context7_cache.py",
                        "Or wait for automatic cache population during agent execution",
                    ],
                )

            # Calculate health score based on metrics
            score = 100.0
            issues = []
            remediation = []

            # Check hit rate (target: ≥95%)
            hit_rate = cache_metrics.hit_rate
            if hit_rate < 95.0:
                if hit_rate < 70.0:
                    score -= 30.0
                    issues.append(f"Very low hit rate: {hit_rate:.1f}%")
                else:
                    score -= 15.0
                    issues.append(f"Low hit rate: {hit_rate:.1f}% (target: ≥95%)")
                remediation.append(
                    "Pre-populate cache: python scripts/prepopulate_context7_cache.py"
                )

            # Check response time (target: <150ms)
            avg_response_time = cache_metrics.avg_response_time_ms
            if avg_response_time > 150.0:
                if avg_response_time > 1000.0:
                    score -= 20.0
                    issues.append(f"Very slow response time: {avg_response_time:.1f}ms")
                else:
                    score -= 10.0
                    issues.append(f"Slow response time: {avg_response_time:.1f}ms (target: <150ms)")

            # Check cache size growth (should be stable or growing slowly)
            # This is a proxy check - in production would track over time
            if cache_metrics.total_size_bytes == 0:
                score -= 10.0
                issues.append("Cache size is zero")

            # Check for stale entries (entries older than 30 days)
            # This requires checking metadata - simplified check here
            stale_ratio = 0.0  # Would calculate from metadata in production
            if stale_ratio > 0.5:
                score -= 10.0
                issues.append(f"High stale entry ratio: {stale_ratio:.1%}")
                remediation.append("Run cache refresh: tapps-agents context7 refresh")

            # Determine status
            if score >= 85.0:
                status = "healthy"
            elif score >= 70.0:
                status = "degraded"
            else:
                status = "unhealthy"

            # Build message
            message_parts = [
                f"Hit rate: {hit_rate:.1f}%",
                f"Response time: {avg_response_time:.0f}ms",
                f"Entries: {cache_metrics.total_entries}",
            ]
            message = " | ".join(message_parts)

            return HealthCheckResult(
                name=self.name,
                status=status,
                score=max(0.0, score),
                message=message,
                details={
                    "hit_rate": hit_rate,
                    "avg_response_time_ms": avg_response_time,
                    "total_entries": cache_metrics.total_entries,
                    "total_libraries": cache_metrics.total_libraries,
                    "total_topics": cache_metrics.total_topics,
                    "total_size_bytes": cache_metrics.total_size_bytes,
                    "cache_hits": cache_metrics.cache_hits,
                    "cache_misses": cache_metrics.cache_misses,
                    "api_calls": cache_metrics.api_calls,
                    "cache_root": str(self.cache_root),
                    "issues": issues,
                },
                remediation=remediation if remediation else None,
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status="unhealthy",
                score=0.0,
                message=f"Context7 cache check failed: {e}",
                details={"error": str(e), "cache_root": str(self.cache_root)},
                remediation=["Check cache directory permissions and configuration"],
            )

