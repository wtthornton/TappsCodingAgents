"""
Context & Knowledge Analysis Artifact Schema.

Defines versioned JSON schema for context management results from Background Agents.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common_enums import ArtifactStatus
from .metadata_models import ArtifactMetadata


class LibraryCacheEntry(BaseModel):
    """Library cache entry information."""

    library_name: str
    library_id: str | None = None  # Context7 library ID
    status: str = "pending"  # "pending", "cached", "failed", "not_found"
    cache_size_bytes: int = 0
    cache_hit_count: int = 0
    last_accessed: str | None = None
    error_message: str | None = None

    model_config = {"extra": "forbid"}


class ContextQuery(BaseModel):
    """Context query result."""

    query: str
    library: str | None = None
    results_count: int = 0
    cache_hit: bool = False
    execution_time_seconds: float | None = None
    error_message: str | None = None

    model_config = {"extra": "forbid"}


class ProjectProfile(BaseModel):
    """Project profiling information."""

    deployment_type: str | None = None  # "cloud_native", "on_premise", "hybrid"
    tenancy: str | None = None  # "single_tenant", "multi_tenant"
    user_scale: str | None = None  # "small", "medium", "large", "enterprise"
    compliance: list[str] = Field(default_factory=list)  # e.g., ["HIPAA", "SOC2"]
    security_posture: str | None = None  # "low", "medium", "high"
    relevant_experts: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ContextArtifact(BaseModel):
    """
    Versioned context & knowledge artifact.

    Schema version: 1.0
    Migrated to Pydantic BaseModel for runtime validation and type safety.
    """

    schema_version: str = "1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: ArtifactStatus = ArtifactStatus.PENDING
    worktree_path: str | None = None
    correlation_id: str | None = None

    # Operation type
    operation_type: str | None = None  # "cache_population", "query", "profiling", "cache_optimization"

    # Cache management
    libraries_cached: list[LibraryCacheEntry] = Field(default_factory=list)
    cache_population_success: int = 0
    cache_population_failed: int = 0
    total_cache_size_bytes: int = 0
    cache_hit_rate: float = 0.0

    # Query results
    queries_executed: list[ContextQuery] = Field(default_factory=list)
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
    metadata: ArtifactMetadata = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

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
        """Mark context operation as completed."""
        self.status = ArtifactStatus.COMPLETED

    def mark_failed(self, error: str) -> None:
        """Mark context operation as failed."""
        self.status = ArtifactStatus.FAILED
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark context operation as cancelled."""
        self.status = ArtifactStatus.CANCELLED
        self.cancelled = True

    def mark_timeout(self) -> None:
        """Mark context operation as timed out."""
        self.status = ArtifactStatus.TIMEOUT
        self.timeout = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextArtifact:
        """
        Create from dictionary (backward compatibility with old dataclass format).

        This method supports both old dataclass format and new Pydantic format.
        """
        # Try Pydantic validation first (new format)
        try:
            return cls.model_validate(data)
        except Exception:
            # Fall back to manual conversion (old dataclass format)
            return cls._from_dict_legacy(data)

    @classmethod
    def _from_dict_legacy(cls, data: dict[str, Any]) -> ContextArtifact:
        """Convert from legacy dataclass format."""
        # Convert libraries_cached from list of dicts to list of LibraryCacheEntry objects
        libraries_cached = []
        if "libraries_cached" in data:
            for lce_data in data["libraries_cached"]:
                if isinstance(lce_data, dict):
                    libraries_cached.append(LibraryCacheEntry(**lce_data))
                else:
                    libraries_cached.append(lce_data)

        # Convert queries_executed from list of dicts to list of ContextQuery objects
        queries_executed = []
        if "queries_executed" in data:
            for cq_data in data["queries_executed"]:
                if isinstance(cq_data, dict):
                    queries_executed.append(ContextQuery(**cq_data))
                else:
                    queries_executed.append(cq_data)

        # Convert project_profile from dict to ProjectProfile object
        project_profile = None
        if data.get("project_profile"):
            profile_data = data["project_profile"]
            if isinstance(profile_data, dict):
                project_profile = ProjectProfile(**profile_data)
            elif isinstance(profile_data, ProjectProfile):
                project_profile = profile_data

        # Convert status string to enum
        status = ArtifactStatus.PENDING
        if data.get("status"):
            try:
                status = ArtifactStatus(data["status"].lower())
            except ValueError:
                pass

        # Build new artifact
        artifact_data = data.copy()
        artifact_data["libraries_cached"] = libraries_cached
        artifact_data["queries_executed"] = queries_executed
        artifact_data["project_profile"] = project_profile
        artifact_data["status"] = status

        # Remove methods that might cause issues
        artifact_data.pop("to_dict", None)
        artifact_data.pop("from_dict", None)
        artifact_data.pop("add_library_cache_entry", None)
        artifact_data.pop("add_query", None)
        artifact_data.pop("set_project_profile", None)
        artifact_data.pop("mark_completed", None)
        artifact_data.pop("mark_failed", None)
        artifact_data.pop("mark_cancelled", None)
        artifact_data.pop("mark_timeout", None)

        return cls(**artifact_data)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary (backward compatibility method).

        For new code, use model_dump(mode="json") instead.
        """
        return self.model_dump(mode="json", exclude_none=False)
