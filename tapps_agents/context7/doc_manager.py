"""
Context7 Documentation Manager for Auto-Save and Offline Access.

Provides automatic saving of fetched documentation and indexing for offline access.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Context7DocManager:
    """
    Manages Context7 documentation caching and indexing for offline access.
    
    Features:
    - Auto-save fetched documentation
    - Build documentation index
    - Offline access to cached docs
    """

    def __init__(self, cache_root: Path, project_root: Path | None = None):
        """
        Initialize documentation manager.
        
        Args:
            cache_root: Context7 cache root directory
            project_root: Project root directory (optional)
        """
        self.cache_root = cache_root
        self.project_root = project_root or Path.cwd()
        
        # Documentation save directory
        self.docs_dir = self.project_root / ".tapps-agents" / "context7-docs"
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        
        # Index file
        self.index_file = self.docs_dir / "index.json"
        self.index: dict[str, Any] = self._load_index()

    def save_documentation(
        self,
        library: str,
        topic: str | None,
        documentation: dict[str, Any],
        source: str | None = None,
    ) -> Path:
        """
        Save fetched documentation to disk for offline access.
        
        Args:
            library: Library name
            topic: Optional topic
            documentation: Documentation content
            source: Optional source identifier
            
        Returns:
            Path to saved documentation file
        """
        # Create safe filename
        safe_library = "".join(c if c.isalnum() or c in "-_" else "_" for c in library)
        safe_topic = f"_{topic}" if topic else ""
        safe_topic = "".join(c if c.isalnum() or c in "-_" else "_" for c in safe_topic)
        
        # Save documentation
        doc_file = self.docs_dir / f"{safe_library}{safe_topic}.json"
        doc_data = {
            "library": library,
            "topic": topic,
            "documentation": documentation,
            "source": source,
            "saved_at": datetime.now().isoformat(),
        }
        
        doc_file.write_text(json.dumps(doc_data, indent=2), encoding="utf-8")
        
        # Update index
        index_key = f"{library}:{topic}" if topic else library
        self.index[index_key] = {
            "library": library,
            "topic": topic,
            "file_path": str(doc_file.relative_to(self.docs_dir)),
            "saved_at": datetime.now().isoformat(),
            "source": source,
        }
        self._save_index()
        
        logger.debug(f"Saved Context7 documentation for {library} ({topic}) to {doc_file}")
        return doc_file

    def get_saved_documentation(
        self, library: str, topic: str | None = None
    ) -> dict[str, Any] | None:
        """
        Retrieve saved documentation from disk (offline access).
        
        Args:
            library: Library name
            topic: Optional topic
            
        Returns:
            Documentation dictionary or None if not found
        """
        index_key = f"{library}:{topic}" if topic else library
        
        if index_key not in self.index:
            return None
        
        doc_info = self.index[index_key]
        doc_file = self.docs_dir / doc_info["file_path"]
        
        if not doc_file.exists():
            # Index entry exists but file is missing - remove from index
            del self.index[index_key]
            self._save_index()
            return None
        
        try:
            doc_data = json.loads(doc_file.read_text(encoding="utf-8"))
            return doc_data.get("documentation")
        except Exception as e:
            logger.warning(f"Failed to load saved documentation from {doc_file}: {e}")
            return None

    def list_saved_documentation(self) -> list[dict[str, str]]:
        """
        List all saved documentation.
        
        Returns:
            List of documentation entries
        """
        return [
            {
                "library": info["library"],
                "topic": info.get("topic"),
                "file_path": info["file_path"],
                "saved_at": info["saved_at"],
            }
            for info in self.index.values()
        ]

    def build_index(self) -> dict[str, Any]:
        """
        Build comprehensive documentation index.
        
        Returns:
            Index dictionary with all available documentation
        """
        index = {
            "libraries": {},
            "topics": {},
            "total_entries": len(self.index),
            "last_updated": datetime.now().isoformat(),
        }
        
        for key, info in self.index.items():
            library = info["library"]
            topic = info.get("topic")
            
            # Add to libraries index
            if library not in index["libraries"]:
                index["libraries"][library] = {
                    "topics": [],
                    "total_docs": 0,
                }
            
            if topic:
                if topic not in index["libraries"][library]["topics"]:
                    index["libraries"][library]["topics"].append(topic)
            
            index["libraries"][library]["total_docs"] += 1
            
            # Add to topics index
            if topic:
                if topic not in index["topics"]:
                    index["topics"][topic] = []
                if library not in index["topics"][topic]:
                    index["topics"][topic].append(library)
        
        return index

    def save_index(self, output_file: Path | None = None) -> Path:
        """
        Save documentation index to file.
        
        Args:
            output_file: Optional output file path
            
        Returns:
            Path to saved index file
        """
        if not output_file:
            output_file = self.index_file
        
        index_data = {
            "entries": self.index,
            "comprehensive_index": self.build_index(),
            "last_updated": datetime.now().isoformat(),
        }
        
        output_file.write_text(json.dumps(index_data, indent=2), encoding="utf-8")
        logger.info(f"Saved documentation index to {output_file}")
        return output_file

    def _load_index(self) -> dict[str, Any]:
        """Load index from disk."""
        if self.index_file.exists():
            try:
                index_data = json.loads(self.index_file.read_text(encoding="utf-8"))
                return index_data.get("entries", {})
            except Exception as e:
                logger.warning(f"Failed to load documentation index: {e}")
        
        return {}

    def _save_index(self) -> None:
        """Save index to disk."""
        try:
            self.save_index()
        except Exception as e:
            logger.warning(f"Failed to save documentation index: {e}")
