"""
Design & Architecture Artifact Schema.

Defines versioned JSON schema for design and architecture results from Foreground Agents.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Component:
    """Represents a system component."""

    name: str
    component_type: str  # "service", "database", "api", "frontend", etc.
    technology: str | None = None
    description: str | None = None
    dependencies: list[str] = field(default_factory=list)
    expert_recommendations: dict[str, str] = field(default_factory=dict)


@dataclass
class DesignArtifact:
    """
    Versioned design and architecture artifact.

    Schema version: 1.0
    """

    schema_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # "pending", "running", "completed", "failed", "cancelled"
    worktree_path: str | None = None
    correlation_id: str | None = None
    operation_type: str | None = None  # "design-system", "create-diagram", "select-technology", "design-security", "define-boundaries"

    # Architecture
    architecture_style: str | None = None  # "microservices", "monolith", "serverless", etc.
    components: list[Component] = field(default_factory=list)
    technology_stack: list[str] = field(default_factory=list)

    # Design outputs
    system_design: dict[str, Any] = field(default_factory=dict)
    database_schema: dict[str, Any] = field(default_factory=dict)
    api_design: dict[str, Any] = field(default_factory=dict)
    security_design: dict[str, Any] = field(default_factory=dict)
    boundaries: dict[str, Any] = field(default_factory=dict)

    # Diagrams
    diagrams: list[dict[str, Any]] = field(default_factory=list)  # List of diagram definitions

    # Expert guidance
    expert_guidance: dict[str, Any] = field(default_factory=dict)

    # Error information
    error: str | None = None
    cancelled: bool = False

    # Metadata
    execution_time_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert Component objects to dicts
        data["components"] = [asdict(component) for component in self.components]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DesignArtifact:
        """Create from dictionary."""
        # Convert component dicts back to Component objects
        components = []
        if "components" in data:
            for component_data in data["components"]:
                components.append(Component(**component_data))
        data["components"] = components
        return cls(**data)

    def add_component(self, component: Component) -> None:
        """Add a system component."""
        self.components.append(component)

    def mark_completed(self) -> None:
        """Mark design as completed."""
        self.status = "completed"

    def mark_failed(self, error: str) -> None:
        """Mark design as failed."""
        self.status = "failed"
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark design as cancelled."""
        self.status = "cancelled"
        self.cancelled = True
