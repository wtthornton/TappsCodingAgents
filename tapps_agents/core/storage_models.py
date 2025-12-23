"""
Storage models for Tier 1 Enhancement infrastructure.

Provides abstractions for file-based storage of feedback, learned prompts, and evaluation results.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class StorageType(str, Enum):
    """Types of storage managed by storage manager."""

    FEEDBACK = "feedback"
    LEARNED_PROMPTS = "learned-prompts"
    EVALUATION = "evaluation"


@dataclass
class StoragePath:
    """Path configuration for storage directories."""

    base_dir: Path
    feedback_dir: Path
    learned_prompts_dir: Path
    evaluation_dir: Path

    @classmethod
    def from_project_root(cls, project_root: Path) -> "StoragePath":
        """Create storage paths from project root."""
        base = project_root / ".tapps-agents"
        return cls(
            base_dir=base,
            feedback_dir=base / "feedback",
            learned_prompts_dir=base / "learned-prompts",
            evaluation_dir=base / "evaluation",
        )

    def ensure_directories(self) -> None:
        """Create all storage directories if they don't exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.learned_prompts_dir.mkdir(parents=True, exist_ok=True)
        self.evaluation_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class StorageMetadata:
    """Metadata for stored items."""

    created_at: datetime
    updated_at: datetime
    version: str
    size_bytes: int
    checksum: str | None = None
    tags: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "tags": self.tags or [],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StorageMetadata":
        """Create from dictionary."""
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if isinstance(data["created_at"], str)
            else data.get("created_at", datetime.now())
        )
        updated_at = (
            datetime.fromisoformat(data["updated_at"])
            if isinstance(data["updated_at"], str)
            else data.get("updated_at", datetime.now())
        )
        return cls(
            created_at=created_at,
            updated_at=updated_at,
            version=data["version"],
            size_bytes=data["size_bytes"],
            checksum=data.get("checksum"),
            tags=data.get("tags"),
        )


@dataclass
class CleanupPolicy:
    """Policy for cleaning up old storage items."""

    max_age_days: int = 30
    max_items_per_type: int = 100
    retain_latest: bool = True
    enabled: bool = True

    def should_cleanup(self, item_age_days: float, item_count: int) -> bool:
        """Determine if cleanup should occur based on policy."""
        if not self.enabled:
            return False
        if item_age_days > self.max_age_days:
            return True
        if item_count > self.max_items_per_type and not self.retain_latest:
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "max_age_days": self.max_age_days,
            "max_items_per_type": self.max_items_per_type,
            "retain_latest": self.retain_latest,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CleanupPolicy":
        """Create from dictionary."""
        return cls(
            max_age_days=data.get("max_age_days", 30),
            max_items_per_type=data.get("max_items_per_type", 100),
            retain_latest=data.get("retain_latest", True),
            enabled=data.get("enabled", True),
        )


@dataclass
class VersionInfo:
    """Version information for stored items."""

    version: str
    created_at: datetime
    parent_version: str | None = None
    changes: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "parent_version": self.parent_version,
            "changes": self.changes or [],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VersionInfo":
        """Create from dictionary."""
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if isinstance(data["created_at"], str)
            else data.get("created_at", datetime.now())
        )
        return cls(
            version=data["version"],
            created_at=created_at,
            parent_version=data.get("parent_version"),
            changes=data.get("changes"),
        )

