"""
Design & Architecture Artifact Schema.

Defines versioned JSON schema for design and architecture results from Foreground Agents.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common_enums import ArtifactStatus, OperationType
from .metadata_models import ArtifactMetadata


class Component(BaseModel):
    """Represents a system component."""

    name: str
    component_type: str  # "service", "database", "api", "frontend", etc.
    technology: str | None = None
    description: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    expert_recommendations: dict[str, str] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class DesignArtifact(BaseModel):
    """
    Versioned design and architecture artifact.

    Schema version: 1.0
    Migrated to Pydantic BaseModel for runtime validation and type safety.
    """

    schema_version: str = "1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: ArtifactStatus = ArtifactStatus.PENDING
    worktree_path: str | None = None
    correlation_id: str | None = None
    operation_type: OperationType | None = None

    # Architecture
    architecture_style: str | None = None  # "microservices", "monolith", "serverless", etc.
    components: list[Component] = Field(default_factory=list)
    technology_stack: list[str] = Field(default_factory=list)

    # Design outputs (kept as dict for flexibility - can be structured later)
    system_design: dict[str, Any] = Field(default_factory=dict)
    database_schema: dict[str, Any] = Field(default_factory=dict)
    api_design: dict[str, Any] = Field(default_factory=dict)
    security_design: dict[str, Any] = Field(default_factory=dict)
    boundaries: dict[str, Any] = Field(default_factory=dict)

    # Diagrams
    diagrams: list[dict[str, Any]] = Field(default_factory=list)  # List of diagram definitions

    # Expert guidance
    expert_guidance: dict[str, Any] = Field(default_factory=dict)

    # Error information
    error: str | None = None
    cancelled: bool = False

    # Metadata
    execution_time_seconds: float | None = None
    metadata: ArtifactMetadata = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    def add_component(self, component: Component) -> None:
        """Add a system component."""
        self.components.append(component)

    def mark_completed(self) -> None:
        """Mark design as completed."""
        self.status = ArtifactStatus.COMPLETED

    def mark_failed(self, error: str) -> None:
        """Mark design as failed."""
        self.status = ArtifactStatus.FAILED
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark design as cancelled."""
        self.status = ArtifactStatus.CANCELLED
        self.cancelled = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DesignArtifact:
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
    def _from_dict_legacy(cls, data: dict[str, Any]) -> DesignArtifact:
        """Convert from legacy dataclass format."""
        # Convert components from dict to Component objects
        components = []
        if "components" in data:
            for component_data in data["components"]:
                if isinstance(component_data, dict):
                    components.append(Component(**component_data))
                else:
                    components.append(component_data)

        # Convert status string to enum
        status = ArtifactStatus.PENDING
        if data.get("status"):
            try:
                status = ArtifactStatus(data["status"].lower())
            except ValueError:
                pass

        # Convert operation_type string to enum
        operation_type = None
        if data.get("operation_type"):
            try:
                operation_type = OperationType(data["operation_type"].lower().replace("-", "_"))
            except ValueError:
                pass

        # Build new artifact
        artifact_data = data.copy()
        artifact_data["components"] = components
        artifact_data["status"] = status
        artifact_data["operation_type"] = operation_type

        # Remove methods that might cause issues
        artifact_data.pop("to_dict", None)
        artifact_data.pop("from_dict", None)
        artifact_data.pop("add_component", None)
        artifact_data.pop("mark_completed", None)
        artifact_data.pop("mark_failed", None)
        artifact_data.pop("mark_cancelled", None)

        return cls(**artifact_data)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary (backward compatibility method).

        For new code, use model_dump(mode="json") instead.
        """
        return self.model_dump(mode="json", exclude_none=False)
