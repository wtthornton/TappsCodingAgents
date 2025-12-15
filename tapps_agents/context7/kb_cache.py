"""
KB Cache - Main cache manager for Context7 knowledge base.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .cache_locking import cache_lock, get_cache_lock_file
from .cache_structure import CacheStructure
from .metadata import MetadataManager


@dataclass
class CacheEntry:
    """Represents a cached documentation entry."""

    library: str
    topic: str
    content: str
    context7_id: str | None = None
    trust_score: float | None = None
    snippet_count: int = 0
    token_count: int = 0
    cached_at: str | None = None
    cache_hits: int = 0

    def to_dict(self) -> dict:
        """Convert cache entry to dictionary."""
        return {
            "library": self.library,
            "topic": self.topic,
            "content": self.content,
            "context7_id": self.context7_id,
            "trust_score": self.trust_score,
            "snippet_count": self.snippet_count,
            "token_count": self.token_count,
            "cached_at": self.cached_at,
            "cache_hits": self.cache_hits,
        }

    def to_markdown(self) -> str:
        """Convert cache entry to markdown format."""
        lines = [
            f"# {self.library} - {self.topic}",
            "",
            f"**Source**: {self.context7_id or 'Unknown'} (Trust Score: {self.trust_score or 'N/A'})",
            f"**Snippets**: {self.snippet_count} | **Tokens**: {self.token_count}",
            f"**Last Updated**: {self.cached_at or datetime.utcnow().isoformat() + 'Z'} | **Cache Hits**: {self.cache_hits}",
            "",
            "---",
            "",
            self.content,
            "",
            "---",
            "",
            "<!-- KB Metadata -->",
            f"<!-- Library: {self.library} -->",
            f"<!-- Topic: {self.topic} -->",
            f"<!-- Context7 ID: {self.context7_id or 'Unknown'} -->",
            f"<!-- Trust Score: {self.trust_score or 'N/A'} -->",
            f"<!-- Snippet Count: {self.snippet_count} -->",
            f"<!-- Last Updated: {self.cached_at or datetime.utcnow().isoformat() + 'Z'} -->",
            f"<!-- Cache Hits: {self.cache_hits} -->",
            f"<!-- Token Count: {self.token_count} -->",
        ]
        return "\n".join(lines)

    @classmethod
    def from_markdown(
        cls, library: str, topic: str, markdown_content: str
    ) -> CacheEntry:
        """Parse cache entry from markdown file."""
        lines = markdown_content.split("\n")

        # Extract metadata from HTML comments
        metadata = {}
        for line in lines:
            if line.strip().startswith("<!--") and "-->" in line:
                comment = line.strip()[4:-3].strip()
                if ": " in comment:
                    key, value = comment.split(": ", 1)
                    # Normalize key (e.g., "Context7 ID" -> "context7_id")
                    key_normalized = key.lower().replace(" ", "_")
                    metadata[key_normalized] = value

        # Extract header information
        # Match "**Source**: /path/to/lib (Trust Score: 0.95)" or "**Source**: /path/to/lib"
        # Use more explicit pattern that stops before " (" or end of line
        source_line_match = re.search(r"\*\*Source\*\*: ([^\n]+)", markdown_content)
        if source_line_match:
            source_line = source_line_match.group(1).strip()
            # Split on " (" to separate context7_id from trust score
            if " (Trust Score:" in source_line:
                parts = source_line.split(" (Trust Score:", 1)
                context7_id = parts[0].strip()
                trust_score_match = re.search(r"([\d.]+)\)", parts[1])
                trust_score = (
                    float(trust_score_match.group(1)) if trust_score_match else None
                )
            else:
                context7_id = source_line
                trust_score = None
        else:
            context7_id = None
            trust_score = None

        snippets_match = re.search(r"\*\*Snippets\*\*: (\d+)", markdown_content)
        snippet_count = int(snippets_match.group(1)) if snippets_match else 0

        tokens_match = re.search(r"\*\*Tokens\*\*: (\d+)", markdown_content)
        token_count = int(tokens_match.group(1)) if tokens_match else 0

        hits_match = re.search(r"\*\*Cache Hits\*\*: (\d+)", markdown_content)
        cache_hits = int(hits_match.group(1)) if hits_match else 0

        # Extract content (between header and metadata comments)
        content_start = markdown_content.find("---\n\n") + 5
        content_end = markdown_content.rfind("\n---\n\n<!-- KB Metadata -->")
        if content_end == -1:
            content_end = markdown_content.rfind("<!-- KB Metadata -->")
        content = (
            markdown_content[content_start:content_end].strip()
            if content_end > content_start
            else markdown_content
        )

        return cls(
            library=library,
            topic=topic,
            content=content,
            context7_id=context7_id or metadata.get("context7_id"),
            trust_score=trust_score
            or (
                float(metadata.get("trust score", 0))
                if metadata.get("trust score") and metadata.get("trust score") != "N/A"
                else None
            ),
            snippet_count=snippet_count or int(metadata.get("snippet count", 0)),
            token_count=token_count or int(metadata.get("token count", 0)),
            cached_at=metadata.get("last updated")
            or datetime.utcnow().isoformat() + "Z",
            cache_hits=cache_hits or int(metadata.get("cache hits", 0)),
        )


class KBCache:
    """Main KB cache manager for Context7 documentation."""

    def __init__(
        self,
        cache_root: Path | None = None,
        cache_dir: Path | None = None,
        metadata_manager: MetadataManager | None = None,
    ):
        """
        Initialize KB cache manager.

        Args:
            cache_root: Root directory for KB cache (preferred parameter name)
            cache_dir: Alternative parameter name for cache_root (for backward compatibility)
            metadata_manager: Optional MetadataManager instance (creates new one if not provided)
        """
        # Support both cache_root and cache_dir for backward compatibility
        root = cache_root or cache_dir
        if root is None:
            # Default to current directory if neither provided
            from pathlib import Path as P
            root = P.cwd() / ".tapps-agents" / "kb" / "context7-cache"
        else:
            root = Path(root)

        self.cache_root = root
        self.cache_dir = root  # Alias for backward compatibility
        self.cache_structure = CacheStructure(root)
        self.metadata_manager = metadata_manager or MetadataManager(
            self.cache_structure
        )
        self.cache_structure.initialize()

    def get(self, library: str, topic: str) -> CacheEntry | None:
        """
        Retrieve cached entry.

        Args:
            library: Library name
            topic: Topic name

        Returns:
            CacheEntry if found, None otherwise
        """
        doc_file = self.cache_structure.get_library_doc_file(library, topic)
        if not doc_file.exists():
            return None

        try:
            content = doc_file.read_text(encoding="utf-8")
            entry = CacheEntry.from_markdown(library, topic, content)

            # Update metadata (increment hits, update last accessed)
            self.metadata_manager.update_library_metadata(
                library, topic=topic, increment_hits=True
            )

            return entry
        except Exception:
            return None

    def store(
        self,
        library: str | CacheEntry,
        topic: str | None = None,
        content: str | None = None,
        context7_id: str | None = None,
        trust_score: float | None = None,
        snippet_count: int | None = None,
    ) -> CacheEntry:
        """
        Store entry in cache.

        Args:
            library: Library name, or CacheEntry instance (if entry is provided, other params ignored)
            topic: Topic name (required if library is a string)
            content: Documentation content (required if library is a string)
            context7_id: Optional Context7 ID
            trust_score: Optional trust score
            snippet_count: Optional snippet count

        Returns:
            CacheEntry instance
        """
        # Support both CacheEntry object and individual parameters
        if isinstance(library, CacheEntry):
            entry = library
            library = entry.library
            topic = entry.topic
            content = entry.content
            context7_id = entry.context7_id or context7_id
            trust_score = entry.trust_score if entry.trust_score is not None else trust_score
            snippet_count = entry.snippet_count if entry.snippet_count else snippet_count
        else:
            if topic is None or content is None:
                raise ValueError("topic and content are required when library is a string")
            # Estimate token count (rough approximation: 1 token ≈ 4 characters)
            token_count = len(content) // 4

            entry = CacheEntry(
                library=library,
                topic=topic,
                content=content,
                context7_id=context7_id,
                trust_score=trust_score,
                snippet_count=snippet_count or 0,
                token_count=token_count,
                cached_at=datetime.utcnow().isoformat() + "Z",
                cache_hits=0,
            )

        # Update cached_at if not set
        if not entry.cached_at:
            entry.cached_at = datetime.utcnow().isoformat() + "Z"

        # Use file locking for atomic writes
        lock_file = get_cache_lock_file(self.cache_root, library=library)
        with cache_lock(lock_file):
            # Ensure library directory exists
            self.cache_structure.ensure_library_dir(library)

            # Write markdown file
            doc_file = self.cache_structure.get_library_doc_file(library, topic)
            doc_file.write_text(entry.to_markdown(), encoding="utf-8")

            # Update metadata
            self.metadata_manager.update_library_metadata(
                library, context7_id=context7_id, topic=topic
            )

            # Update cache index
            self.metadata_manager.update_cache_index(
                library, topic, context7_id=context7_id
            )

        return entry

    def exists(self, library: str, topic: str) -> bool:
        """
        Check if entry exists in cache.

        Args:
            library: Library name
            topic: Topic name

        Returns:
            True if entry exists
        """
        doc_file = self.cache_structure.get_library_doc_file(library, topic)
        return doc_file.exists()

    def delete(self, library: str, topic: str | None = None) -> bool:
        """
        Delete entry or entire library from cache.

        Args:
            library: Library name
            topic: Optional topic name (if None, deletes entire library)

        Returns:
            True if deletion was successful, False otherwise
        """
        if topic:
            doc_file = self.cache_structure.get_library_doc_file(library, topic)
            if doc_file.exists():
                doc_file.unlink()
                self.metadata_manager.update_cache_index(library, topic, remove=True)
                return True
            return False
        else:
            lib_dir = self.cache_structure.get_library_dir(library)
            if lib_dir.exists():
                import shutil

                shutil.rmtree(lib_dir)

                # Remove from index
                index = self.metadata_manager.load_cache_index()
                if library in index.libraries:
                    del index.libraries[library]
                    self.metadata_manager.save_cache_index(index)
                return True
            return False

    def list_entries(self) -> list[CacheEntry]:
        """
        List all cache entries.

        Returns:
            List of CacheEntry instances
        """
        entries = []
        index = self.metadata_manager.load_cache_index()
        for library_name, library_info in index.libraries.items():
            for topic_name in library_info.get("topics", {}):
                entry = self.get(library_name, topic_name)
                if entry:
                    entries.append(entry)
        return entries

    def clear(self) -> None:
        """
        Clear all cache entries.
        """
        import shutil

        # Delete all library directories
        for library_dir in self.cache_structure.cache_root.iterdir():
            if library_dir.is_dir() and library_dir.name != "metadata":
                shutil.rmtree(library_dir)

        # Reset index
        from .cache_structure import CacheIndex

        index = CacheIndex(version="1.0", last_updated=None, total_entries=0, libraries={})
        self.metadata_manager.save_cache_index(index)
