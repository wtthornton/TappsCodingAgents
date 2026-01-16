"""
Knowledge Base Freshness Tracking

Tracks when knowledge base files were last updated, versions, and deprecation status.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class KnowledgeFileMetadata:
    """Metadata for a knowledge base file."""

    file_path: str
    last_updated: str  # ISO format datetime
    version: str | None = None
    deprecated: bool = False
    deprecation_date: str | None = None
    replacement_file: str | None = None
    author: str | None = None
    tags: list[str] = None
    description: str | None = None

    def __post_init__(self):
        """Initialize default values."""
        if self.tags is None:
            self.tags = []


class KnowledgeFreshnessTracker:
    """Tracks knowledge base file freshness and metadata."""

    def __init__(self, metadata_file: Path | None = None):
        """
        Initialize freshness tracker.

        Args:
            metadata_file: Path to metadata JSON file
        """
        if metadata_file is None:
            project_root = Path.cwd()
            metadata_file = project_root / ".tapps-agents" / "knowledge_metadata.json"

        self.metadata_file = Path(metadata_file)
        self.metadata: dict[str, KnowledgeFileMetadata] = {}
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load metadata from file."""
        if not self.metadata_file.exists():
            return

        try:
            content = self.metadata_file.read_text(encoding="utf-8")
            data = json.loads(content)

            for file_path, meta_dict in data.items():
                self.metadata[file_path] = KnowledgeFileMetadata(**meta_dict)
        except Exception:
            # If metadata file is corrupted, start fresh
            self.metadata = {}

    def _save_metadata(self) -> None:
        """Save metadata to file."""
        try:
            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                file_path: asdict(meta) for file_path, meta in self.metadata.items()
            }

            self.metadata_file.write_text(
                json.dumps(data, indent=2, sort_keys=True), encoding="utf-8"
            )
        except Exception:
            # Silently fail if save fails (non-critical)
            pass

    def update_file_metadata(
        self,
        file_path: Path,
        version: str | None = None,
        author: str | None = None,
        tags: list[str] | None = None,
        description: str | None = None,
    ) -> None:
        """
        Update metadata for a knowledge file.

        Args:
            file_path: Path to knowledge file
            version: Optional version string
            author: Optional author name
            tags: Optional list of tags
            description: Optional description
        """
        file_path_str = str(file_path)

        # Get file modification time
        if file_path.exists():
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            last_updated = mtime.isoformat()
        else:
            last_updated = datetime.now().isoformat()

        # Update or create metadata
        if file_path_str in self.metadata:
            meta = self.metadata[file_path_str]
            meta.last_updated = last_updated
            if version:
                meta.version = version
            if author:
                meta.author = author
            if tags:
                meta.tags = tags
            if description:
                meta.description = description
        else:
            self.metadata[file_path_str] = KnowledgeFileMetadata(
                file_path=file_path_str,
                last_updated=last_updated,
                version=version,
                author=author,
                tags=tags or [],
                description=description,
            )

        self._save_metadata()

    def mark_deprecated(
        self,
        file_path: Path,
        replacement_file: Path | None = None,
        deprecation_date: str | None = None,
    ) -> None:
        """
        Mark a knowledge file as deprecated.

        Args:
            file_path: Path to deprecated file
            replacement_file: Optional path to replacement file
            deprecation_date: Optional deprecation date (ISO format)
        """
        file_path_str = str(file_path)

        if file_path_str not in self.metadata:
            self.update_file_metadata(file_path)

        meta = self.metadata[file_path_str]
        meta.deprecated = True
        meta.deprecation_date = deprecation_date or datetime.now().isoformat()
        if replacement_file:
            meta.replacement_file = str(replacement_file)

        self._save_metadata()

    def get_file_metadata(self, file_path: Path) -> KnowledgeFileMetadata | None:
        """
        Get metadata for a file.

        Args:
            file_path: Path to knowledge file

        Returns:
            KnowledgeFileMetadata or None if not found
        """
        file_path_str = str(file_path)
        return self.metadata.get(file_path_str)

    def get_stale_files(
        self, knowledge_dir: Path, max_age_days: int = 365
    ) -> list[tuple[Path, KnowledgeFileMetadata]]:
        """
        Get files that haven't been updated in specified days.

        Args:
            knowledge_dir: Knowledge base directory
            max_age_days: Maximum age in days

        Returns:
            List of (file_path, metadata) tuples for stale files
        """
        stale_files: list[tuple[Path, KnowledgeFileMetadata]] = []
        cutoff_date = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)

        for md_file in knowledge_dir.rglob("*.md"):
            if md_file.name == "README.md":
                continue

            meta = self.get_file_metadata(md_file)
            if meta:
                try:
                    last_updated = datetime.fromisoformat(meta.last_updated).timestamp()
                    if last_updated < cutoff_date:
                        stale_files.append((md_file, meta))
                except Exception:
                    # If date parsing fails, check file mtime
                    if md_file.exists():
                        file_mtime = md_file.stat().st_mtime
                        if file_mtime < cutoff_date:
                            stale_files.append((md_file, meta))
            else:
                # No metadata, check file mtime
                if md_file.exists():
                    file_mtime = md_file.stat().st_mtime
                    if file_mtime < cutoff_date:
                        stale_files.append((md_file, meta))

        return stale_files

    def get_deprecated_files(self, knowledge_dir: Path) -> list[tuple[Path, KnowledgeFileMetadata]]:
        """
        Get all deprecated files.

        Args:
            knowledge_dir: Knowledge base directory

        Returns:
            List of (file_path, metadata) tuples for deprecated files
        """
        deprecated_files: list[tuple[Path, KnowledgeFileMetadata]] = []

        for md_file in knowledge_dir.rglob("*.md"):
            meta = self.get_file_metadata(md_file)
            if meta and meta.deprecated:
                deprecated_files.append((md_file, meta))

        return deprecated_files

    def scan_and_update(self, knowledge_dir: Path) -> dict[str, Any]:
        """
        Scan knowledge directory and update metadata for all files.

        Args:
            knowledge_dir: Knowledge base directory

        Returns:
            Summary of scan results
        """
        scanned = 0
        updated = 0
        new_files = 0

        for md_file in knowledge_dir.rglob("*.md"):
            if md_file.name == "README.md":
                continue

            scanned += 1
            file_path_str = str(md_file)

            if file_path_str not in self.metadata:
                new_files += 1
                self.update_file_metadata(md_file)
            else:
                # Check if file was modified
                if md_file.exists():
                    file_mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
                    meta = self.metadata[file_path_str]
                    meta_last_updated = datetime.fromisoformat(meta.last_updated)

                    if file_mtime > meta_last_updated:
                        updated += 1
                        self.update_file_metadata(md_file)

        self._save_metadata()

        return {
            "scanned": scanned,
            "updated": updated,
            "new_files": new_files,
            "total_tracked": len(self.metadata),
        }

    def get_summary(self, knowledge_dir: Path) -> dict[str, Any]:
        """
        Get freshness summary.

        Args:
            knowledge_dir: Knowledge base directory

        Returns:
            Summary dictionary
        """
        total_files = len(list(knowledge_dir.rglob("*.md")))
        tracked_files = len(self.metadata)
        deprecated_count = len(self.get_deprecated_files(knowledge_dir))
        stale_count = len(self.get_stale_files(knowledge_dir, max_age_days=365))

        return {
            "total_files": total_files,
            "tracked_files": tracked_files,
            "deprecated_files": deprecated_count,
            "stale_files": stale_count,
            "coverage": round(tracked_files / total_files * 100, 1) if total_files > 0 else 0.0,
        }


# Global freshness tracker instance
_global_freshness_tracker: KnowledgeFreshnessTracker | None = None


def get_freshness_tracker(metadata_file: Path | None = None) -> KnowledgeFreshnessTracker:
    """
    Get or create global freshness tracker.

    Args:
        metadata_file: Optional path to metadata file

    Returns:
        KnowledgeFreshnessTracker instance
    """
    global _global_freshness_tracker

    if _global_freshness_tracker is None:
        _global_freshness_tracker = KnowledgeFreshnessTracker(metadata_file=metadata_file)

    return _global_freshness_tracker
