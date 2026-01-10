"""
Documentation Analysis Artifact Schema.

Defines versioned JSON schema for documentation results from Background Agents.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common_enums import ArtifactStatus
from .metadata_models import ArtifactMetadata


class DocFileResult(BaseModel):
    """Result from documenting a single file."""

    file_path: str
    doc_type: str  # "api_docs", "readme", "docstrings", "architecture"
    status: str  # "success", "error", "skipped"
    output_file: str | None = None
    lines_added: int = 0
    lines_updated: int = 0
    error_message: str | None = None
    execution_time_seconds: float | None = None

    model_config = {"extra": "forbid"}


class DocumentationArtifact(BaseModel):
    """
    Versioned documentation artifact.

    Schema version: 1.0
    Migrated to Pydantic BaseModel for runtime validation and type safety.
    """

    schema_version: str = "1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: ArtifactStatus = ArtifactStatus.PENDING
    worktree_path: str | None = None
    correlation_id: str | None = None

    # Documentation results
    files_documented: list[DocFileResult] = Field(default_factory=list)

    # Summary statistics
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_lines_added: int = 0
    total_lines_updated: int = 0

    # Documentation types generated
    doc_types: list[str] = Field(default_factory=list)  # e.g., ["api_docs", "readme"]

    # Output files created
    output_files: list[str] = Field(default_factory=list)

    # Error information
    error: str | None = None
    cancelled: bool = False
    timeout: bool = False

    # Metadata
    execution_time_seconds: float | None = None
    metadata: ArtifactMetadata = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    def add_file_result(self, result: DocFileResult) -> None:
        """Add a file documentation result."""
        self.files_documented.append(result)
        self.total_files += 1

        if result.status == "success":
            self.successful_files += 1
            self.total_lines_added += result.lines_added
            self.total_lines_updated += result.lines_updated
            if result.output_file:
                self.output_files.append(result.output_file)
            if result.doc_type not in self.doc_types:
                self.doc_types.append(result.doc_type)
        elif result.status == "error":
            self.failed_files += 1
        elif result.status == "skipped":
            self.skipped_files += 1

    def mark_completed(self) -> None:
        """Mark documentation as completed."""
        self.status = ArtifactStatus.COMPLETED

    def mark_failed(self, error: str) -> None:
        """Mark documentation as failed."""
        self.status = ArtifactStatus.FAILED
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark documentation as cancelled."""
        self.status = ArtifactStatus.CANCELLED
        self.cancelled = True

    def mark_timeout(self) -> None:
        """Mark documentation as timed out."""
        self.status = ArtifactStatus.TIMEOUT
        self.timeout = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentationArtifact:
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
    def _from_dict_legacy(cls, data: dict[str, Any]) -> DocumentationArtifact:
        """Convert from legacy dataclass format."""
        # Convert files_documented from list of dicts to list of DocFileResult objects
        files_documented = []
        if "files_documented" in data:
            for fr_data in data["files_documented"]:
                if isinstance(fr_data, dict):
                    files_documented.append(DocFileResult(**fr_data))
                else:
                    files_documented.append(fr_data)

        # Convert status string to enum
        status = ArtifactStatus.PENDING
        if "status" in data and data["status"]:
            try:
                status = ArtifactStatus(data["status"].lower())
            except ValueError:
                pass

        # Build new artifact
        artifact_data = data.copy()
        artifact_data["files_documented"] = files_documented
        artifact_data["status"] = status

        # Remove methods that might cause issues
        artifact_data.pop("to_dict", None)
        artifact_data.pop("from_dict", None)
        artifact_data.pop("add_file_result", None)
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
