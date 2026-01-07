"""
Tests for AgentResultCache - agent_cache.py

Tests for the generic agent result caching system that provides 90%+ speedup
for unchanged files by caching results based on file content hash.
"""

import json
import tempfile
from pathlib import Path

import pytest

from tapps_agents.core.agent_cache import (
    AgentResultCache,
    get_agent_cache,
    reset_agent_cache,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("# Test file\nprint('hello')\n")
        f.flush()
        yield Path(f.name)
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def temp_files(temp_cache_dir):
    """Create multiple temporary files for testing."""
    files = []
    for i in range(3):
        file_path = temp_cache_dir / f"file_{i}.py"
        file_path.write_text(f"# File {i}\nprint({i})\n")
        files.append(file_path)
    return files


@pytest.fixture
def cache(temp_cache_dir):
    """Create a cache instance with temporary directory."""
    return AgentResultCache("test_agent", cache_dir=temp_cache_dir, ttl_seconds=3600)


class TestAgentResultCache:
    """Tests for AgentResultCache class."""

    def test_init_creates_cache_dir(self, temp_cache_dir):
        """Test that __init__ creates the cache directory."""
        cache_dir = temp_cache_dir / "new_cache"
        cache = AgentResultCache("test", cache_dir=cache_dir)
        assert cache_dir.exists()

    def test_init_with_disabled_cache(self, temp_cache_dir):
        """Test that disabled cache doesn't create directory."""
        cache_dir = temp_cache_dir / "disabled_cache"
        cache = AgentResultCache("test", cache_dir=cache_dir, enabled=False)
        assert not cache_dir.exists()

    def test_init_default_ttl(self, cache):
        """Test default TTL value."""
        assert cache.ttl_seconds == 3600

    def test_agent_name(self, cache):
        """Test agent name is stored."""
        assert cache.agent_name == "test_agent"

    @pytest.mark.asyncio
    async def test_save_and_get_cached_result(self, cache, temp_file):
        """Test saving and retrieving cached results."""
        test_result = {"score": 85.0, "issues": []}
        
        # Save result
        await cache.save_result(temp_file, "test-command", "1.0", test_result)
        
        # Retrieve result
        cached = await cache.get_cached_result(temp_file, "test-command", "1.0")
        
        assert cached is not None
        assert cached["score"] == 85.0
        assert cached["issues"] == []

    @pytest.mark.asyncio
    async def test_cache_miss_on_nonexistent_file(self, cache, temp_cache_dir):
        """Test cache miss for non-existent file."""
        nonexistent = temp_cache_dir / "nonexistent.py"
        result = await cache.get_cached_result(nonexistent, "command", "1.0")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_miss_on_disabled_cache(self, temp_cache_dir, temp_file):
        """Test cache miss when cache is disabled."""
        cache = AgentResultCache("test", cache_dir=temp_cache_dir, enabled=False)
        
        # Save should be a no-op
        await cache.save_result(temp_file, "command", "1.0", {"score": 85.0})
        
        # Get should return None
        result = await cache.get_cached_result(temp_file, "command", "1.0")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_file_change(self, cache, temp_file):
        """Test that cache invalidates when file content changes."""
        test_result = {"score": 85.0}
        
        # Save result
        await cache.save_result(temp_file, "command", "1.0", test_result)
        
        # Modify file
        temp_file.write_text("# Modified content\nprint('world')\n")
        
        # Cache should miss due to content change
        cached = await cache.get_cached_result(temp_file, "command", "1.0")
        assert cached is None

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_version_change(self, cache, temp_file):
        """Test that cache invalidates when version changes."""
        test_result = {"score": 85.0}
        
        # Save with version 1.0
        await cache.save_result(temp_file, "command", "1.0", test_result)
        
        # Query with version 2.0 should miss
        cached = await cache.get_cached_result(temp_file, "command", "2.0")
        assert cached is None

    @pytest.mark.asyncio
    async def test_different_commands_have_separate_caches(self, cache, temp_file):
        """Test that different commands have separate cache entries."""
        result1 = {"type": "test"}
        result2 = {"type": "document"}
        
        # Save results for different commands
        await cache.save_result(temp_file, "test", "1.0", result1)
        await cache.save_result(temp_file, "document", "1.0", result2)
        
        # Retrieve each
        cached1 = await cache.get_cached_result(temp_file, "test", "1.0")
        cached2 = await cache.get_cached_result(temp_file, "document", "1.0")
        
        assert cached1["type"] == "test"
        assert cached2["type"] == "document"

    def test_invalidate_file(self, cache, temp_file):
        """Test invalidating all cache entries for a file."""
        count = cache.invalidate_file(temp_file)
        # Should return 0 since nothing was cached
        assert count == 0

    def test_clear_cache(self, cache):
        """Test clearing all cache entries."""
        count = cache.clear()
        assert count == 0  # Empty cache

    def test_get_stats(self, cache):
        """Test getting cache statistics."""
        stats = cache.get_stats()
        
        assert stats["agent"] == "test_agent"
        assert stats["enabled"] is True
        assert stats["ttl_seconds"] == 3600
        assert stats["entries"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == "0.0%"

    @pytest.mark.asyncio
    async def test_stats_update_on_hit_miss(self, cache, temp_file):
        """Test that stats update on cache hits and misses."""
        # Miss
        await cache.get_cached_result(temp_file, "command", "1.0")
        assert cache.get_stats()["misses"] == 1
        
        # Save and hit
        await cache.save_result(temp_file, "command", "1.0", {"score": 85.0})
        await cache.get_cached_result(temp_file, "command", "1.0")
        
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_prune_expired(self, cache):
        """Test pruning expired cache entries."""
        count = cache.prune_expired()
        assert count == 0  # Nothing to prune


class TestMultiFileCache:
    """Tests for multi-file caching."""

    @pytest.mark.asyncio
    async def test_multi_file_cache(self, cache, temp_files):
        """Test caching with multiple files."""
        test_result = {"files": [str(f) for f in temp_files]}
        
        # Save result for multiple files
        await cache.save_result(temp_files, "analyze", "1.0", test_result)
        
        # Retrieve result
        cached = await cache.get_cached_result(temp_files, "analyze", "1.0")
        
        assert cached is not None
        assert len(cached["files"]) == 3

    @pytest.mark.asyncio
    async def test_multi_file_invalidation_on_any_change(self, cache, temp_files):
        """Test that multi-file cache invalidates if any file changes."""
        test_result = {"result": "test"}
        
        # Save result
        await cache.save_result(temp_files, "analyze", "1.0", test_result)
        
        # Modify one file
        temp_files[1].write_text("# Modified\n")
        
        # Cache should miss
        cached = await cache.get_cached_result(temp_files, "analyze", "1.0")
        assert cached is None


class TestGlobalCache:
    """Tests for global cache functions."""

    def test_get_agent_cache_returns_singleton(self):
        """Test that get_agent_cache returns the same instance."""
        reset_agent_cache("singleton_test")
        cache1 = get_agent_cache("singleton_test")
        cache2 = get_agent_cache("singleton_test")
        assert cache1 is cache2

    def test_different_agents_have_different_caches(self):
        """Test that different agents have separate caches."""
        cache1 = get_agent_cache("agent1")
        cache2 = get_agent_cache("agent2")
        assert cache1.agent_name == "agent1"
        assert cache2.agent_name == "agent2"
        assert cache1 is not cache2

    def test_reset_agent_cache(self):
        """Test that reset clears the global instance."""
        cache1 = get_agent_cache("reset_test")
        reset_agent_cache("reset_test")
        cache2 = get_agent_cache("reset_test")
        assert cache1 is not cache2


class TestFileHash:
    """Tests for file hashing functionality."""

    def test_file_hash_consistency(self, cache, temp_file):
        """Test that file hash is consistent for same content."""
        hash1 = cache._file_hash(temp_file)
        hash2 = cache._file_hash(temp_file)
        assert hash1 == hash2

    def test_file_hash_changes_with_content(self, cache, temp_file):
        """Test that file hash changes when content changes."""
        hash1 = cache._file_hash(temp_file)
        temp_file.write_text("# Different content\n")
        hash2 = cache._file_hash(temp_file)
        assert hash1 != hash2

    def test_file_hash_length(self, cache, temp_file):
        """Test that file hash is truncated to 16 characters."""
        hash_value = cache._file_hash(temp_file)
        assert len(hash_value) == 16

    def test_multi_file_hash_order_independent(self, cache, temp_files):
        """Test that multi-file hash is order-independent."""
        hash1 = cache._multi_file_hash(temp_files)
        hash2 = cache._multi_file_hash(list(reversed(temp_files)))
        assert hash1 == hash2
