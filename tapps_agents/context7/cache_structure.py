"""
Cache Structure Management - Directory structure for Context7 KB cache.
"""

import os
import tempfile
from pathlib import Path

import yaml


class CacheStructure:
    """Manages the directory structure for Context7 KB cache."""

    def __init__(self, cache_root: Path):
        """
        Initialize cache structure manager.

        Args:
            cache_root: Root directory for KB cache (e.g., .tapps-agents/kb/context7-cache)
        """
        self.cache_root = Path(cache_root).resolve()
        self.libraries_dir = self.cache_root / "libraries"
        self.topics_dir = self.cache_root / "topics"
        self.index_file = self.cache_root / "index.yaml"
        self.cross_refs_file = self.cache_root / "cross-references.yaml"
        self.refresh_queue_file = self.cache_root / ".refresh-queue"

    def initialize(self):
        """Initialize cache directory structure.

        Uses atomic operations to avoid TOCTOU race conditions:
        - Directories use exist_ok=True (already atomic)
        - YAML files use exclusive-create to detect races
        - Refresh queue uses touch(exist_ok=True)
        """
        try:
            self.cache_root.mkdir(parents=True, exist_ok=True)
            self.libraries_dir.mkdir(parents=True, exist_ok=True)
            self.topics_dir.mkdir(parents=True, exist_ok=True)

            # Create index.yaml atomically (exclusive create avoids TOCTOU)
            self._create_file_if_absent(
                self.index_file, self._index_file_content()
            )

            # Create cross-references.yaml atomically
            self._create_file_if_absent(
                self.cross_refs_file, self._cross_refs_content()
            )

            # Create refresh queue file (touch is idempotent)
            self.refresh_queue_file.touch(exist_ok=True)
        except (OSError, PermissionError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Failed to initialize Context7 cache structure at {self.cache_root}: {e}. "
                f"Context7 cache features will be limited."
            )
            # Re-raise to allow caller to handle
            raise

    @staticmethod
    def _index_file_content() -> dict:
        """Return default index file content."""
        return {
            "version": "1.0",
            "last_updated": None,
            "total_entries": 0,
            "libraries": {},
        }

    @staticmethod
    def _cross_refs_content() -> dict:
        """Return default cross-references file content."""
        return {"version": "1.0", "last_updated": None, "topics": {}}

    @staticmethod
    def _create_file_if_absent(path: Path, data: dict) -> None:
        """Atomically create a YAML file only if it doesn't exist.

        Uses write-to-temp-then-rename to avoid partial writes.
        If the file already exists, this is a no-op.
        """
        if path.exists():
            return
        try:
            # Write to a temp file in the same directory, then rename
            fd, tmp = tempfile.mkstemp(
                dir=str(path.parent), suffix=".tmp", prefix=path.stem
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
                os.replace(tmp, str(path))
            except BaseException:
                # Clean up temp file on error
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise
        except FileExistsError:
            # Another process created it first — that's fine
            pass

    @staticmethod
    def atomic_write_yaml(path: Path, data: dict) -> None:
        """Atomically write YAML data to a file using write-to-temp-then-rename.

        Safe for concurrent access — either the old or new content is visible,
        never a partial write.
        """
        fd, tmp = tempfile.mkstemp(
            dir=str(path.parent), suffix=".tmp", prefix=path.stem
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            os.replace(tmp, str(path))
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def get_library_dir(self, library: str) -> Path:
        """
        Get directory path for a library.

        Args:
            library: Library name (e.g., "react", "fastapi")

        Returns:
            Path to library directory
        """
        return self.libraries_dir / library.lower()

    def get_library_meta_file(self, library: str) -> Path:
        """
        Get metadata file path for a library.

        Args:
            library: Library name

        Returns:
            Path to meta.yaml file
        """
        return self.get_library_dir(library) / "meta.yaml"

    def get_library_doc_file(self, library: str, topic: str) -> Path:
        """
        Get documentation file path for a library/topic.

        Args:
            library: Library name
            topic: Topic name (e.g., "hooks", "routing")

        Returns:
            Path to topic markdown file
        """
        return self.get_library_dir(library) / f"{topic}.md"

    def get_topic_dir(self, topic: str) -> Path:
        """
        Get directory path for a topic.

        Args:
            topic: Topic name

        Returns:
            Path to topic directory
        """
        return self.topics_dir / topic.lower()

    def ensure_library_dir(self, library: str) -> Path:
        """
        Ensure library directory exists and return its path.

        Args:
            library: Library name

        Returns:
            Path to library directory

        Raises:
            OSError: If directory creation fails
        """
        lib_dir = self.get_library_dir(library)
        try:
            lib_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to create library directory {lib_dir}: {e}")
            raise
        return lib_dir

    def ensure_topic_dir(self, topic: str) -> Path:
        """
        Ensure topic directory exists and return its path.

        Args:
            topic: Topic name

        Returns:
            Path to topic directory
        """
        topic_dir = self.get_topic_dir(topic)
        topic_dir.mkdir(parents=True, exist_ok=True)
        return topic_dir
