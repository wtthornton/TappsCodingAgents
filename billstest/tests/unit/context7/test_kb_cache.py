"""
Tests for Context7 KB Cache module.

Tests cache operations, entry management, and cache policies.
"""

from unittest.mock import patch

from tapps_agents.context7.kb_cache import CacheEntry, KBCache


class TestCacheEntry:
    """Tests for CacheEntry."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            library="test-lib",
            topic="test-topic",
            content="test content",
        )
        
        assert entry.library == "test-lib"
        assert entry.topic == "test-topic"
        assert entry.content == "test content"

    def test_cache_entry_to_dict(self):
        """Test converting cache entry to dictionary."""
        entry = CacheEntry(
            library="test-lib",
            topic="test-topic",
            content="test content",
        )
        
        data = entry.to_dict()
        assert isinstance(data, dict)
        assert data["library"] == "test-lib"
        assert data["topic"] == "test-topic"
        assert data["content"] == "test content"


class TestKBCache:
    """Tests for KBCache."""

    def test_kb_cache_init(self, tmp_path):
        """Test KBCache initialization."""
        cache_dir = tmp_path / "cache"
        cache = KBCache(cache_dir=cache_dir)
        
        assert cache.cache_dir == cache_dir
        assert cache.cache_dir.exists()

    def test_kb_cache_init_default(self, tmp_path):
        """Test KBCache initialization with default directory."""
        with patch("tapps_agents.context7.kb_cache.Path.cwd", return_value=tmp_path):
            cache = KBCache()
            
            # Should create default cache directory
            assert cache.cache_dir.exists()

    def test_store_entry(self, tmp_path):
        """Test storing a cache entry."""
        cache = KBCache(cache_dir=tmp_path / "cache")
        entry = CacheEntry(
            library="test-lib",
            topic="test-topic",
            content="test content",
        )
        
        cache.store(entry)
        
        # Entry should be stored
        retrieved = cache.get("test-lib", "test-topic")
        assert retrieved is not None
        assert retrieved.content == "test content"

    def test_get_entry_exists(self, tmp_path):
        """Test retrieving an existing cache entry."""
        cache = KBCache(cache_dir=tmp_path / "cache")
        entry = CacheEntry(
            library="test-lib",
            topic="test-topic",
            content="test content",
        )
        
        cache.store(entry)
        retrieved = cache.get("test-lib", "test-topic")
        
        assert retrieved is not None
        assert retrieved.content == "test content"

    def test_get_entry_not_found(self, tmp_path):
        """Test retrieving a non-existent cache entry."""
        cache = KBCache(cache_dir=tmp_path / "cache")
        
        retrieved = cache.get("nonexistent-lib", "nonexistent-topic")
        
        assert retrieved is None

    def test_delete_entry(self, tmp_path):
        """Test deleting a cache entry."""
        cache = KBCache(cache_dir=tmp_path / "cache")
        entry = CacheEntry(
            library="test-lib",
            topic="test-topic",
            content="test content",
        )
        
        cache.store(entry)
        cache.delete("test-lib", "test-topic")
        
        retrieved = cache.get("test-lib", "test-topic")
        assert retrieved is None

    def test_list_entries(self, tmp_path):
        """Test listing cache entries."""
        cache = KBCache(cache_dir=tmp_path / "cache")
        
        # Store multiple entries
        entry1 = CacheEntry(library="lib1", topic="topic1", content="content1")
        entry2 = CacheEntry(library="lib2", topic="topic2", content="content2")
        
        cache.store(entry1)
        cache.store(entry2)
        
        entries = cache.list_entries()
        
        assert isinstance(entries, list)
        assert len(entries) >= 2

    def test_clear_cache(self, tmp_path):
        """Test clearing all cache entries."""
        cache = KBCache(cache_dir=tmp_path / "cache")
        
        entry = CacheEntry(library="test-lib", topic="test-topic", content="content")
        cache.store(entry)
        
        cache.clear()
        
        retrieved = cache.get("test-lib", "test-topic")
        assert retrieved is None
