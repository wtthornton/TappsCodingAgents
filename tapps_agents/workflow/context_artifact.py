"""
Context & Knowledge Analysis Artifact Schema.

Defines versioned JSON schema for context management results from Background Agents.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LibraryCacheEntry:
    """Library cache entry information."""

    library_name: str
    library_id: str | None = None  # Context7 library ID
    status: str = "pending"  # "pending", "cached", "failed", "not_found"
    cache_size_bytes: int = 0
    cache_hit_count: int = 0
    last_accessed: str | None = None
    error_message: str | None = None


@dataclass
class ContextQuery:
    """Context query result."""

    query: str
    library: str | None = None
    results_count: int = 0
    cache_hit: bool = False
    execution_time_seconds: float | None = None
    error_message: str | None = None


@dataclass
class ProjectProfile:
    """Project profiling information."""

    deployment_type: str | None = None  # "cloud_native", "on_premise", "hybrid"
    tenancy: str | None = None  # "single_tenant", "multi_tenant"
    user_scale: str | None = None  # "small", "medium", "large", "enterprise"
    compliance: list[str] = field(default_factory=list)  # e.g., ["HIPAA", "SOC2"]
    security_posture: str | None = None  # "low", "medium", "high"
    relevant_experts: list[str] = field(default_factory=list)


@dataclass
class ContextArtifact:
    """
    Versioned context & knowledge artifact.

    Schema version: 1.0
    """

    schema_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # "pending", "running", "completed", "failed", "cancelled", "timeout"
    worktree_path: str | None = None
    correlation_id: str | None = None

    # Operation type
    operation_type: str | None = None  # "cache_population", "query", "profiling", "cache_optimization"

    # Cache management
    libraries_cached: list[LibraryCacheEntry] = field(default_factory=list)
    cache_population_success: int = 0
    cache_population_failed: int = 0
    total_cache_size_bytes: int = 0
    cache_hit_rate: float = 0.0

    # Query results
    queries_executed: list[ContextQuery] = field(default_factory=list)
    total_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    # Project profiling
    project_profile: ProjectProfile | None = None

    # Cache optimization
    cache_cleanup_performed: bool = False
    files_removed: int = 0
    space_freed_bytes: int = 0

    # Error information
    error: str | None = None
    cancelled: bool = False
    timeout: bool = False

    # Metadata
    execution_time_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert nested objects to dicts
        data["libraries_cached"] = [asdict(lc) for lc in self.libraries_cached]
        data["queries_executed"] = [asdict(cq) for cq in self.queries_executed]
        if self.project_profile:
            data["project_profile"] = asdict(self.project_profile)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextArtifact:
        """Create from dictionary."""
        # Convert nested dicts back to objects
        if "libraries_cached" in data:
            data["libraries_cached"] = [
                LibraryCacheEntry(**lc) for lc in data["libraries_cached"]
            ]
        if "queries_executed" in data:
            data["queries_executed"] = [
                ContextQuery(**cq) for cq in data["queries_executed"]
            ]
        if "project_profile" in data and data["project_profile"]:
            data["project_profile"] = ProjectProfile(**data["project_profile"])
        return cls(**data)

    def add_library_cache_entry(self, entry: LibraryCacheEntry) -> None:
        """Add a library cache entry."""
        self.libraries_cached.append(entry)
        if entry.status == "cached":
            self.cache_population_success += 1
            self.total_cache_size_bytes += entry.cache_size_bytes
        elif entry.status == "failed":
            self.cache_population_failed += 1

    def add_query(self, query: ContextQuery) -> None:
        """Add a query result."""
        self.queries_executed.append(query)
        self.total_queries += 1
        if query.cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

        # Update cache hit rate
        if self.total_queries > 0:
            self.cache_hit_rate = (self.cache_hits / self.total_queries) * 100.0

    def set_project_profile(self, profile: ProjectProfile) -> None:
        """Set project profile."""
        self.project_profile = profile

    def mark_completed(self) -> None:
        """Mark operation as completed."""
        self.status = "completed"

    def mark_failed(self, error: str) -> None:
        """Mark operation as failed."""
        self.status = "failed"
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark operation as cancelled."""
        self.status = "cancelled"
        self.cancelled = True

    def mark_timeout(self) -> None:
        """Mark operation as timed out."""
        self.status = "timeout"
        self.timeout = True
