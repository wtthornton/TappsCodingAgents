"""
Documentation Analysis Artifact Schema.

Defines versioned JSON schema for documentation results from Background Agents.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DocFileResult:
    """Result from documenting a single file."""

    file_path: str
    doc_type: str  # "api_docs", "readme", "docstrings", "architecture"
    status: str  # "success", "error", "skipped"
    output_file: str | None = None
    lines_added: int = 0
    lines_updated: int = 0
    error_message: str | None = None
    execution_time_seconds: float | None = None


@dataclass
class DocumentationArtifact:
    """
    Versioned documentation artifact.

    Schema version: 1.0
    """

    schema_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # "pending", "running", "completed", "failed", "cancelled", "timeout"
    worktree_path: str | None = None
    correlation_id: str | None = None

    # Documentation results
    files_documented: list[DocFileResult] = field(default_factory=list)

    # Summary statistics
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_lines_added: int = 0
    total_lines_updated: int = 0

    # Documentation types generated
    doc_types: list[str] = field(default_factory=list)  # e.g., ["api_docs", "readme"]

    # Output files created
    output_files: list[str] = field(default_factory=list)

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
        # Convert DocFileResult objects to dicts
        data["files_documented"] = [asdict(fr) for fr in self.files_documented]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentationArtifact:
        """Create from dictionary."""
        # Convert file result dicts back to DocFileResult objects
        files_documented = []
        if "files_documented" in data:
            files_documented = [DocFileResult(**fr) for fr in data["files_documented"]]
        data["files_documented"] = files_documented
        return cls(**data)

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
        self.status = "completed"

    def mark_failed(self, error: str) -> None:
        """Mark documentation as failed."""
        self.status = "failed"
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark documentation as cancelled."""
        self.status = "cancelled"
        self.cancelled = True

    def mark_timeout(self) -> None:
        """Mark documentation as timed out."""
        self.status = "timeout"
        self.timeout = True
