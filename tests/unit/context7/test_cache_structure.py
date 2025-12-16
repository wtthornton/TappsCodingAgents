"""
Tests for Context7 cache structure management.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from tapps_agents.context7.cache_structure import CacheStructure

pytestmark = pytest.mark.unit


class TestCacheStructure:
    """Test CacheStructure functionality."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_initialize_cache_dirs(self, temp_cache_dir):
        """Test cache directory initialization."""
        structure = CacheStructure(temp_cache_dir)
        structure.initialize()

        assert temp_cache_dir.exists()
        assert structure.libraries_dir.exists()
        assert structure.topics_dir.exists()
        assert structure.index_file.exists()
        assert structure.cross_refs_file.exists()
        assert structure.refresh_queue_file.exists()

    def test_get_library_dir(self, temp_cache_dir):
        """Test library directory path generation."""
        structure = CacheStructure(temp_cache_dir)
        lib_dir = structure.get_library_dir("react")

        assert lib_dir == temp_cache_dir / "libraries" / "react"

    def test_get_library_meta_file(self, temp_cache_dir):
        """Test library metadata file path generation."""
        structure = CacheStructure(temp_cache_dir)
        meta_file = structure.get_library_meta_file("react")

        assert meta_file == temp_cache_dir / "libraries" / "react" / "meta.yaml"

    def test_get_library_doc_file(self, temp_cache_dir):
        """Test library documentation file path generation."""
        structure = CacheStructure(temp_cache_dir)
        doc_file = structure.get_library_doc_file("react", "hooks")

        assert doc_file == temp_cache_dir / "libraries" / "react" / "hooks.md"

    def test_get_topic_dir(self, temp_cache_dir):
        """Test topic directory path generation."""
        structure = CacheStructure(temp_cache_dir)
        topic_dir = structure.get_topic_dir("hooks")

        assert topic_dir == temp_cache_dir / "topics" / "hooks"

    def test_ensure_library_dir(self, temp_cache_dir):
        """Test library directory creation."""
        structure = CacheStructure(temp_cache_dir)
        structure.ensure_library_dir("react")

        assert structure.get_library_dir("react").exists()

    def test_ensure_topic_dir(self, temp_cache_dir):
        """Test topic directory creation."""
        structure = CacheStructure(temp_cache_dir)
        structure.ensure_topic_dir("hooks")

        assert (structure.topics_dir / "hooks").exists()

    def test_multiple_libraries(self, temp_cache_dir):
        """Test handling multiple libraries."""
        structure = CacheStructure(temp_cache_dir)
        structure.initialize()

        structure.ensure_library_dir("react")
        structure.ensure_library_dir("vue")
        structure.ensure_library_dir("angular")

        assert structure.get_library_dir("react").exists()
        assert structure.get_library_dir("vue").exists()
        assert structure.get_library_dir("angular").exists()

    def test_library_with_topics(self, temp_cache_dir):
        """Test library with multiple topics."""
        structure = CacheStructure(temp_cache_dir)
        structure.initialize()
        structure.ensure_library_dir("react")

        # Create multiple topic files
        topics = ["hooks", "components", "routing"]
        for topic in topics:
            doc_file = structure.get_library_doc_file("react", topic)
            doc_file.write_text(f"# {topic}\n\nContent for {topic}")

        assert all(structure.get_library_doc_file("react", t).exists() for t in topics)
