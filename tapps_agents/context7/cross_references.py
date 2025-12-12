"""
Cross-References System - Topic-based cross-referencing for Context7 KB.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import yaml


@dataclass
class CrossReference:
    """Represents a cross-reference between topics."""

    source_library: str
    source_topic: str
    target_library: str
    target_topic: str
    relationship_type: str = "related"  # "related", "depends_on", "similar", "part_of"
    confidence: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "source_library": self.source_library,
            "source_topic": self.source_topic,
            "target_library": self.target_library,
            "target_topic": self.target_topic,
            "relationship_type": self.relationship_type,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CrossReference:
        """Create from dictionary."""
        if not isinstance(data, dict):
            # Handle case where data is not a dict
            raise ValueError(f"Expected dict, got {type(data)}: {data}")
        return cls(**data)


@dataclass
class TopicIndex:
    """Index of libraries/topics for a specific topic."""

    topic: str
    libraries: dict[str, list[str]] = field(default_factory=dict)  # library -> [topics]
    relationships: list[CrossReference] = field(default_factory=list)
    last_updated: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "topic": self.topic,
            "libraries": self.libraries,
            "relationships": [ref.to_dict() for ref in self.relationships],
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TopicIndex:
        """Create from dictionary."""
        relationships = []
        for r in data.get("relationships", []):
            if isinstance(r, dict):
                try:
                    relationships.append(CrossReference.from_dict(r))
                except (ValueError, TypeError):
                    # Skip invalid entries
                    continue
        return cls(
            topic=data["topic"],
            libraries=data.get("libraries", {}),
            relationships=relationships,
            last_updated=data.get("last_updated", datetime.utcnow().isoformat() + "Z"),
        )


class CrossReferenceManager:
    """
    Manages cross-references between topics across libraries.
    """

    def __init__(self, cache_structure):
        """
        Initialize CrossReferenceManager.

        Args:
            cache_structure: CacheStructure instance
        """
        self.cache_structure = cache_structure
        self.cross_refs_file = cache_structure.cache_root / "cross-references.yaml"
        self.topic_index_dir = cache_structure.cache_root / "topics"
        self.topic_index_dir.mkdir(exist_ok=True)

        # In-memory cache of cross-references
        self._cross_refs: dict[
            str, list[CrossReference]
        ] = {}  # "library/topic" -> [refs]
        self._topic_indices: dict[str, TopicIndex] = {}

        self._load_cross_references()

    def _load_cross_references(self):
        """Load cross-references from file."""
        if not self.cross_refs_file.exists():
            return

        try:
            with open(self.cross_refs_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data:
                for key, refs_data in data.items():
                    if not isinstance(refs_data, list):
                        continue
                    self._cross_refs[key] = []
                    for ref_data in refs_data:
                        if isinstance(ref_data, dict):
                            try:
                                self._cross_refs[key].append(
                                    CrossReference.from_dict(ref_data)
                                )
                            except (ValueError, TypeError):
                                # Skip invalid entries
                                continue
        except (OSError, yaml.YAMLError):
            # Start with empty cross-references on error
            self._cross_refs = {}

    def _save_cross_references(self):
        """Save cross-references to file."""
        data = {
            key: [ref.to_dict() for ref in refs]
            for key, refs in self._cross_refs.items()
        }

        with open(self.cross_refs_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=True)

    def _load_topic_index(self, topic: str) -> TopicIndex | None:
        """Load topic index from file."""
        topic_dir = self.topic_index_dir / topic
        index_file = topic_dir / "index.yaml"

        if not index_file.exists():
            return None

        try:
            with open(index_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return TopicIndex.from_dict(data) if data else None
        except (OSError, yaml.YAMLError):
            return None

    def _save_topic_index(self, topic_index: TopicIndex):
        """Save topic index to file."""
        topic_dir = self.topic_index_dir / topic_index.topic
        topic_dir.mkdir(exist_ok=True)

        index_file = topic_dir / "index.yaml"
        with open(index_file, "w", encoding="utf-8") as f:
            yaml.dump(
                topic_index.to_dict(), f, default_flow_style=False, sort_keys=False
            )

    def add_cross_reference(
        self,
        source_library: str,
        source_topic: str,
        target_library: str,
        target_topic: str,
        relationship_type: str = "related",
        confidence: float = 1.0,
    ):
        """
        Add a cross-reference between two topics.

        Args:
            source_library: Source library name
            source_topic: Source topic name
            target_library: Target library name
            target_topic: Target topic name
            relationship_type: Type of relationship ("related", "depends_on", "similar", "part_of")
            confidence: Confidence score (0.0-1.0)
        """
        key = f"{source_library}/{source_topic}"

        # Check if reference already exists
        if key not in self._cross_refs:
            self._cross_refs[key] = []

        # Check for duplicate
        existing = next(
            (
                ref
                for ref in self._cross_refs[key]
                if ref.target_library == target_library
                and ref.target_topic == target_topic
            ),
            None,
        )

        if existing:
            # Update existing reference
            existing.relationship_type = relationship_type
            existing.confidence = confidence
        else:
            # Add new reference
            ref = CrossReference(
                source_library=source_library,
                source_topic=source_topic,
                target_library=target_library,
                target_topic=target_topic,
                relationship_type=relationship_type,
                confidence=confidence,
            )
            self._cross_refs[key].append(ref)

        # Update topic indices
        self._update_topic_index(source_topic, source_library, source_topic)
        self._update_topic_index(target_topic, target_library, target_topic)

        # Save to file
        self._save_cross_references()

    def _update_topic_index(self, topic: str, library: str, topic_name: str):
        """Update topic index with library/topic information."""
        topic_index = self._topic_indices.get(topic)
        if topic_index is None:
            topic_index = self._load_topic_index(topic) or TopicIndex(topic=topic)
            self._topic_indices[topic] = topic_index

        if library not in topic_index.libraries:
            topic_index.libraries[library] = []

        if topic_name not in topic_index.libraries[library]:
            topic_index.libraries[library].append(topic_name)

        topic_index.last_updated = datetime.utcnow().isoformat() + "Z"
        self._save_topic_index(topic_index)

    def get_cross_references(
        self, library: str, topic: str, relationship_type: str | None = None
    ) -> list[CrossReference]:
        """
        Get cross-references for a specific library/topic.

        Args:
            library: Library name
            topic: Topic name
            relationship_type: Optional filter by relationship type

        Returns:
            List of CrossReference objects
        """
        key = f"{library}/{topic}"
        refs = self._cross_refs.get(key, [])

        if relationship_type:
            refs = [ref for ref in refs if ref.relationship_type == relationship_type]

        # Sort by confidence (descending)
        refs.sort(key=lambda r: r.confidence, reverse=True)
        return refs

    def get_related_topics(self, topic: str) -> list[dict[str, Any]]:
        """
        Get all related topics across libraries for a given topic name.

        Args:
            topic: Topic name to search for

        Returns:
            List of dictionaries with library, topic, and relationship info
        """
        topic_index = self._topic_indices.get(topic)
        if topic_index is None:
            topic_index = self._load_topic_index(topic)
            if topic_index:
                self._topic_indices[topic] = topic_index

        if not topic_index:
            return []

        results: list[dict[str, Any]] = []
        for ref in topic_index.relationships:
            results.append(
                {
                    "library": ref.target_library,
                    "topic": ref.target_topic,
                    "relationship": ref.relationship_type,
                    "confidence": ref.confidence,
                }
            )

        return results

    def find_similar_topics(
        self, library: str, topic: str, min_confidence: float = 0.7
    ) -> list[CrossReference]:
        """
        Find similar topics across libraries.

        Args:
            library: Library name
            topic: Topic name
            min_confidence: Minimum confidence threshold

        Returns:
            List of CrossReference objects with "similar" relationship
        """
        refs = self.get_cross_references(library, topic, relationship_type="similar")
        return [ref for ref in refs if ref.confidence >= min_confidence]

    def auto_discover_cross_references(self, library: str, topic: str, content: str):
        """
        Automatically discover cross-references from content.

        This is a basic implementation - can be enhanced with NLP or keyword matching.

        Args:
            library: Library name
            topic: Topic name
            content: Content text to analyze
        """
        # Basic keyword-based discovery
        # Look for common patterns like "see also", "related to", "similar to"

        content_lower = content.lower()

        # Check for mentions of other libraries/topics in the content
        # This is a placeholder - in production, you'd use more sophisticated NLP

        # Example: Look for patterns like "React Router" or "similar to Vue Router"
        if "similar to" in content_lower or "see also" in content_lower:
            # Would need more sophisticated parsing to extract actual references
            pass

    def get_topic_index(self, topic: str) -> TopicIndex | None:
        """
        Get topic index for a specific topic.

        Args:
            topic: Topic name

        Returns:
            TopicIndex or None if not found
        """
        if topic in self._topic_indices:
            return self._topic_indices[topic]

        topic_index = self._load_topic_index(topic)
        if topic_index:
            self._topic_indices[topic] = topic_index

        return topic_index

    def remove_cross_reference(
        self,
        source_library: str,
        source_topic: str,
        target_library: str,
        target_topic: str,
    ) -> bool:
        """
        Remove a cross-reference.

        Args:
            source_library: Source library name
            source_topic: Source topic name
            target_library: Target library name
            target_topic: Target topic name

        Returns:
            True if removed, False if not found
        """
        key = f"{source_library}/{source_topic}"

        if key not in self._cross_refs:
            return False

        refs = self._cross_refs[key]
        original_len = len(refs)

        self._cross_refs[key] = [
            ref
            for ref in refs
            if not (
                ref.target_library == target_library
                and ref.target_topic == target_topic
            )
        ]

        if len(self._cross_refs[key]) == 0:
            del self._cross_refs[key]

        removed = len(self._cross_refs[key]) < original_len

        if removed:
            self._save_cross_references()

        return removed

    def get_all_cross_references(self) -> dict[str, list[CrossReference]]:
        """Get all cross-references."""
        return self._cross_refs.copy()

    def clear_cross_references(self):
        """Clear all cross-references (use with caution)."""
        self._cross_refs = {}
        if self.cross_refs_file.exists():
            self.cross_refs_file.unlink()

        # Clear topic indices
        for topic_index_file in self.topic_index_dir.rglob("index.yaml"):
            topic_index_file.unlink()
