"""
Context7 Cache Metadata

Metadata for Context7 cache entries to track language, version, and freshness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class CacheMetadata:
    """
    Metadata for Context7 cache entry.

    Tracks language, creation time, library details, and validation status.
    """

    library_name: str
    language: str  # "python", "javascript", etc.
    created_at: datetime = field(default_factory=datetime.now)
    last_validated: datetime | None = None
    version: str | None = None
    source_url: str | None = None
    content_hash: str | None = None
    validated: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary for JSON serialization."""
        return {
            "library_name": self.library_name,
            "language": self.language,
            "created_at": self.created_at.isoformat(),
            "last_validated": self.last_validated.isoformat()
            if self.last_validated
            else None,
            "version": self.version,
            "source_url": self.source_url,
            "content_hash": self.content_hash,
            "validated": self.validated,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CacheMetadata:
        """Create metadata from dictionary (JSON deserialization)."""
        return cls(
            library_name=data["library_name"],
            language=data["language"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_validated=datetime.fromisoformat(data["last_validated"])
            if data.get("last_validated")
            else None,
            version=data.get("version"),
            source_url=data.get("source_url"),
            content_hash=data.get("content_hash"),
            validated=data.get("validated", False),
        )

    def is_language_match(self, expected_language: str) -> bool:
        """
        Check if cache language matches expected language.

        Args:
            expected_language: Expected language (e.g., "python")

        Returns:
            True if language matches, False otherwise
        """
        return self.language.lower() == expected_language.lower()

    def needs_validation(self, max_age_days: int = 30) -> bool:
        """
        Check if cache entry needs validation.

        Args:
            max_age_days: Maximum age in days before validation needed

        Returns:
            True if validation needed, False otherwise
        """
        if not self.validated or self.last_validated is None:
            return True

        age_days = (datetime.now() - self.last_validated).days
        return age_days > max_age_days


class CacheMetadataManager:
    """
    Manage Context7 cache metadata.

    Reads and writes metadata files alongside cache content.
    """

    METADATA_SUFFIX = ".metadata.json"

    def __init__(self, cache_dir: Path):
        """
        Initialize metadata manager.

        Args:
            cache_dir: Context7 cache directory
        """
        self.cache_dir = cache_dir

    def get_metadata_path(self, cache_file: Path) -> Path:
        """
        Get metadata file path for cache file.

        Args:
            cache_file: Path to cache content file

        Returns:
            Path to metadata file
        """
        return cache_file.parent / f"{cache_file.name}{self.METADATA_SUFFIX}"

    def load_metadata(self, cache_file: Path) -> CacheMetadata | None:
        """
        Load metadata for cache file.

        Args:
            cache_file: Path to cache content file

        Returns:
            Metadata if exists, None otherwise
        """
        metadata_path = self.get_metadata_path(cache_file)
        if not metadata_path.exists():
            return None

        try:
            import json

            with open(metadata_path) as f:
                data = json.load(f)
            return CacheMetadata.from_dict(data)
        except Exception:
            return None

    def save_metadata(self, cache_file: Path, metadata: CacheMetadata):
        """
        Save metadata for cache file.

        Args:
            cache_file: Path to cache content file
            metadata: Metadata to save
        """
        metadata_path = self.get_metadata_path(cache_file)

        import json

        with open(metadata_path, "w") as f:
            json.dump(metadata.to_dict(), f, indent=2)

    def validate_language(
        self, cache_file: Path, expected_language: str
    ) -> tuple[bool, CacheMetadata | None]:
        """
        Validate cache file language matches expected.

        Args:
            cache_file: Path to cache content file
            expected_language: Expected language (e.g., "python")

        Returns:
            Tuple of (is_valid, metadata)
            - is_valid: True if language matches or no metadata exists
            - metadata: Metadata if exists, None otherwise
        """
        metadata = self.load_metadata(cache_file)

        # If no metadata, assume valid (backward compatibility)
        if metadata is None:
            return (True, None)

        # Check language match
        is_valid = metadata.is_language_match(expected_language)
        return (is_valid, metadata)

    def get_language_mismatch_warning(
        self, library_name: str, expected: str, actual: str
    ) -> str:
        """
        Generate warning message for language mismatch.

        Args:
            library_name: Library name
            expected: Expected language
            actual: Actual cached language

        Returns:
            Warning message
        """
        return f"""
⚠️  Language Mismatch Warning

Library: {library_name}
Expected Language: {expected}
Cached Language: {actual}

The cached documentation may contain examples in the wrong language.

To fix:
1. Clear cache: rm -rf .tapps-agents/kb/context7-cache/{library_name}
2. Specify language: tapps-agents reviewer docs {library_name} --language {expected}
3. Or update config:
   context7:
     language: {expected}
""".strip()
