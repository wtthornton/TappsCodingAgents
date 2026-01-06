"""
Cache Structure Management - Directory structure for Context7 KB cache.
"""

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
        self.cache_root = Path(cache_root)
        self.libraries_dir = self.cache_root / "libraries"
        self.topics_dir = self.cache_root / "topics"
        self.index_file = self.cache_root / "index.yaml"
        self.cross_refs_file = self.cache_root / "cross-references.yaml"
        self.refresh_queue_file = self.cache_root / ".refresh-queue"

    def initialize(self):
        """Initialize cache directory structure."""
        try:
            self.cache_root.mkdir(parents=True, exist_ok=True)
            self.libraries_dir.mkdir(parents=True, exist_ok=True)
            self.topics_dir.mkdir(parents=True, exist_ok=True)

            # Create index.yaml if it doesn't exist
            if not self.index_file.exists():
                self._create_index_file()

            # Create cross-references.yaml if it doesn't exist
            if not self.cross_refs_file.exists():
                self._create_cross_refs_file()

            # Create refresh queue file if it doesn't exist
            if not self.refresh_queue_file.exists():
                self.refresh_queue_file.touch()
        except (OSError, PermissionError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Failed to initialize Context7 cache structure at {self.cache_root}: {e}. "
                f"Context7 cache features will be limited."
            )
            # Re-raise to allow caller to handle
            raise

    def _create_index_file(self):
        """Create initial index.yaml file."""
        try:
            index_data = {
                "version": "1.0",
                "last_updated": None,
                "total_entries": 0,
                "libraries": {},
            }
            with open(self.index_file, "w", encoding="utf-8") as f:
                yaml.dump(index_data, f, default_flow_style=False, sort_keys=False)
        except (OSError, yaml.YAMLError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to create index file {self.index_file}: {e}")
            raise

    def _create_cross_refs_file(self):
        """Create initial cross-references.yaml file."""
        try:
            cross_refs_data = {"version": "1.0", "last_updated": None, "topics": {}}
            with open(self.cross_refs_file, "w", encoding="utf-8") as f:
                yaml.dump(cross_refs_data, f, default_flow_style=False, sort_keys=False)
        except (OSError, yaml.YAMLError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to create cross-refs file {self.cross_refs_file}: {e}")
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
