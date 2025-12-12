"""
Tests for Context7 metadata management.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from tapps_agents.context7.cache_structure import CacheStructure
from tapps_agents.context7.metadata import CacheIndex, LibraryMetadata, MetadataManager


class TestMetadataModels:
    """Test metadata dataclasses."""

    def test_library_metadata_creation(self):
        """Test LibraryMetadata creation."""
        metadata = LibraryMetadata(library="react", context7_id="/facebook/react")

        assert metadata.library == "react"
        assert metadata.context7_id == "/facebook/react"
        assert metadata.cache_hits == 0
        assert metadata.total_docs == 0
        assert len(metadata.topics) == 0

    def test_library_metadata_with_topics(self):
        """Test LibraryMetadata with topics."""
        metadata = LibraryMetadata(
            library="react", topics=["hooks", "components"], total_docs=2
        )

        assert len(metadata.topics) == 2
        assert "hooks" in metadata.topics
        assert "components" in metadata.topics
        assert metadata.total_docs == 2

    def test_cache_index_creation(self):
        """Test CacheIndex creation."""
        index = CacheIndex()
        assert index.version == "1.0"
        assert index.total_entries == 0
        assert len(index.libraries) == 0


class TestMetadataManager:
    """Test MetadataManager functionality."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def cache_structure(self, temp_cache_dir):
        """Create cache structure."""
        structure = CacheStructure(temp_cache_dir)
        structure.initialize()
        return structure

    @pytest.fixture
    def metadata_manager(self, cache_structure):
        """Create metadata manager."""
        return MetadataManager(cache_structure)

    def test_load_library_metadata_nonexistent(self, metadata_manager):
        """Test loading non-existent library metadata."""
        metadata = metadata_manager.load_library_metadata("react")
        assert metadata is None

    def test_save_and_load_library_metadata(self, metadata_manager):
        """Test saving and loading library metadata."""
        original_metadata = LibraryMetadata(
            library="react",
            context7_id="/facebook/react",
            cache_hits=10,
            total_docs=2,
            topics=["hooks", "components"],
        )

        metadata_manager.save_library_metadata(original_metadata)

        loaded_metadata = metadata_manager.load_library_metadata("react")
        assert loaded_metadata is not None
        assert loaded_metadata.library == "react"
        assert loaded_metadata.context7_id == "/facebook/react"
        assert loaded_metadata.cache_hits == 10
        assert loaded_metadata.total_docs == 2
        assert len(loaded_metadata.topics) == 2

    def test_load_cache_index_nonexistent(self, metadata_manager):
        """Test loading non-existent cache index."""
        index = metadata_manager.load_cache_index()
        assert isinstance(index, CacheIndex)
        assert index.total_entries == 0
        assert len(index.libraries) == 0

    def test_save_and_load_cache_index(self, metadata_manager):
        """Test saving and loading cache index."""
        original_index = CacheIndex()
        original_index.libraries = {
            "react": {
                "context7_id": "/facebook/react",
                "topics": {"hooks": {"cached_at": "2024-01-01T00:00:00Z"}},
            },
            "vue": {
                "context7_id": "/vuejs/vue",
                "topics": {"components": {"cached_at": "2024-01-01T00:00:00Z"}},
            },
        }
        original_index.total_entries = 2

        metadata_manager.save_cache_index(original_index)

        loaded_index = metadata_manager.load_cache_index()
        assert loaded_index.total_entries == 2
        assert "react" in loaded_index.libraries
        assert "vue" in loaded_index.libraries

    def test_update_library_metadata(self, metadata_manager):
        """Test updating library metadata."""
        # Create initial metadata
        metadata_manager.save_library_metadata(LibraryMetadata(library="react"))

        # Update with context7_id and topic
        metadata_manager.update_library_metadata(
            "react", context7_id="/facebook/react", topic="hooks"
        )

        # Verify update
        updated_metadata = metadata_manager.load_library_metadata("react")
        assert updated_metadata.context7_id == "/facebook/react"
        assert "hooks" in updated_metadata.topics

    def test_update_library_metadata_increment_hits(self, metadata_manager):
        """Test incrementing cache hits."""
        metadata_manager.save_library_metadata(LibraryMetadata(library="react"))

        # Increment hits
        metadata_manager.update_library_metadata("react", increment_hits=True)
        metadata_manager.update_library_metadata("react", increment_hits=True)

        metadata = metadata_manager.load_library_metadata("react")
        assert metadata.cache_hits == 2

    def test_update_cache_index(self, metadata_manager):
        """Test updating cache index."""
        metadata_manager.update_cache_index(
            "react", "hooks", context7_id="/facebook/react"
        )

        index = metadata_manager.load_cache_index()
        assert index.total_entries == 1
        assert "react" in index.libraries
        assert "hooks" in index.libraries["react"]["topics"]

    def test_update_cache_index_remove(self, metadata_manager):
        """Test removing entry from cache index."""
        # Add entry
        metadata_manager.update_cache_index("react", "hooks")
        assert metadata_manager.load_cache_index().total_entries == 1

        # Remove entry
        metadata_manager.update_cache_index("react", "hooks", remove=True)
        index = metadata_manager.load_cache_index()
        assert index.total_entries == 0
        assert "react" not in index.libraries or "hooks" not in index.libraries.get(
            "react", {}
        ).get("topics", {})
