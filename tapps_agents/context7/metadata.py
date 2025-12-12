"""
Metadata Management - Handles metadata files for Context7 KB cache.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from .cache_structure import CacheStructure


@dataclass
class LibraryMetadata:
    """Metadata for a library."""

    library: str
    context7_id: str | None = None
    trust_score: float | None = None
    topics: list[str] = field(default_factory=list)
    total_docs: int = 0
    total_size_bytes: int = 0
    total_tokens: int = 0
    last_updated: str | None = None
    last_accessed: str | None = None
    cache_hits: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LibraryMetadata:
        """Create from dictionary."""
        return cls(**data)


@dataclass
class CacheIndex:
    """Master index of all cached entries."""

    version: str = "1.0"
    last_updated: str | None = None
    total_entries: int = 0
    libraries: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "version": self.version,
            "last_updated": self.last_updated,
            "total_entries": self.total_entries,
            "libraries": self.libraries,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CacheIndex:
        """Create from dictionary."""
        return cls(
            version=data.get("version", "1.0"),
            last_updated=data.get("last_updated"),
            total_entries=data.get("total_entries", 0),
            libraries=data.get("libraries", {}),
        )


class MetadataManager:
    """Manages metadata files for Context7 KB cache."""

    def __init__(self, cache_structure: CacheStructure):
        """
        Initialize metadata manager.

        Args:
            cache_structure: CacheStructure instance
        """
        self.cache_structure = cache_structure

    def load_library_metadata(self, library: str) -> LibraryMetadata | None:
        """
        Load library metadata from meta.yaml.

        Args:
            library: Library name

        Returns:
            LibraryMetadata instance or None if not found
        """
        meta_file = self.cache_structure.get_library_meta_file(library)
        if not meta_file.exists():
            return None

        try:
            with open(meta_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return LibraryMetadata.from_dict(data)
        except (OSError, yaml.YAMLError):
            return None

    def save_library_metadata(self, metadata: LibraryMetadata):
        """
        Save library metadata to meta.yaml.

        Args:
            metadata: LibraryMetadata instance
        """
        # Ensure library directory exists
        self.cache_structure.ensure_library_dir(metadata.library)

        meta_file = self.cache_structure.get_library_meta_file(metadata.library)
        with open(meta_file, "w", encoding="utf-8") as f:
            yaml.dump(metadata.to_dict(), f, default_flow_style=False, sort_keys=False)

    def update_library_metadata(
        self,
        library: str,
        context7_id: str | None = None,
        topic: str | None = None,
        increment_hits: bool = False,
    ):
        """
        Update library metadata.

        Args:
            library: Library name
            context7_id: Optional Context7 ID to set
            topic: Optional topic to add
            increment_hits: Whether to increment cache hits
        """
        metadata = self.load_library_metadata(library)
        if metadata is None:
            metadata = LibraryMetadata(library=library)

        if context7_id is not None:
            metadata.context7_id = context7_id

        if topic is not None and topic not in metadata.topics:
            metadata.topics.append(topic)

        if increment_hits:
            metadata.cache_hits += 1

        metadata.last_accessed = datetime.utcnow().isoformat() + "Z"
        self.save_library_metadata(metadata)

    def load_cache_index(self) -> CacheIndex:
        """
        Load master cache index.

        Returns:
            CacheIndex instance
        """
        if not self.cache_structure.index_file.exists():
            return CacheIndex()

        try:
            with open(self.cache_structure.index_file, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return CacheIndex.from_dict(data)
        except (OSError, yaml.YAMLError):
            return CacheIndex()

    def save_cache_index(self, index: CacheIndex):
        """
        Save master cache index.

        Args:
            index: CacheIndex instance
        """
        index.last_updated = datetime.utcnow().isoformat() + "Z"
        with open(self.cache_structure.index_file, "w", encoding="utf-8") as f:
            yaml.dump(index.to_dict(), f, default_flow_style=False, sort_keys=False)

    def update_cache_index(
        self,
        library: str,
        topic: str,
        context7_id: str | None = None,
        remove: bool = False,
    ):
        """
        Update master cache index.

        Args:
            library: Library name
            topic: Topic name
            context7_id: Optional Context7 ID
            remove: If True, remove entry instead of adding
        """
        index = self.load_cache_index()

        if remove:
            if library in index.libraries:
                if topic in index.libraries[library].get("topics", {}):
                    del index.libraries[library]["topics"][topic]
                    index.total_entries = max(0, index.total_entries - 1)
        else:
            if library not in index.libraries:
                index.libraries[library] = {"context7_id": context7_id, "topics": {}}

            if context7_id is not None:
                index.libraries[library]["context7_id"] = context7_id

            if topic not in index.libraries[library]["topics"]:
                index.libraries[library]["topics"][topic] = {
                    "cached_at": datetime.utcnow().isoformat() + "Z"
                }
                index.total_entries += 1

        self.save_cache_index(index)

    def remove_from_cache_index(self, library: str, topic: str):
        """
        Remove an entry from the cache index.

        Args:
            library: Library name
            topic: Topic name
        """
        self.update_cache_index(library, topic, remove=True)
