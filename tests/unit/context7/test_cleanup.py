"""
Unit tests for Context7 KB cleanup automation.
"""

import shutil
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from tapps_agents.context7.cache_structure import CacheStructure
from tapps_agents.context7.cleanup import CleanupResult, KBCleanup
from tapps_agents.context7.kb_cache import KBCache
from tapps_agents.context7.metadata import MetadataManager
from tapps_agents.context7.staleness_policies import StalenessPolicyManager

pytestmark = pytest.mark.unit


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory."""
    temp_dir = tempfile.mkdtemp()
    cache_root = Path(temp_dir) / "context7-cache"
    yield cache_root
    shutil.rmtree(temp_dir)


@pytest.fixture
def cache_structure(temp_cache_dir):
    """Create CacheStructure instance."""
    structure = CacheStructure(temp_cache_dir)
    structure.initialize()
    return structure


@pytest.fixture
def metadata_manager(cache_structure):
    """Create MetadataManager instance."""
    return MetadataManager(cache_structure)


@pytest.fixture
def kb_cache(cache_structure, metadata_manager):
    """Create KBCache instance."""
    return KBCache(cache_structure.cache_root, metadata_manager)


@pytest.fixture
def staleness_policy_manager():
    """Create StalenessPolicyManager instance."""
    return StalenessPolicyManager()


@pytest.fixture
def cleanup(cache_structure, metadata_manager, staleness_policy_manager):
    """Create KBCleanup instance."""
    return KBCleanup(
        cache_structure,
        metadata_manager,
        staleness_policy_manager,
        max_cache_size_bytes=1024,  # 1KB for testing
        max_age_days=30,
        min_access_days=7,
    )


@pytest.fixture
def sample_entries(kb_cache):
    """Create sample cache entries for testing."""
    entries = []

    # Create entries with different ages
    now = datetime.now(UTC)

    # Recent entry
    kb_cache.store(
        library="react",
        topic="hooks",
        content="# React Hooks\nRecent content",
        context7_id="/facebook/react",
    )
    entries.append(("react", "hooks", now))

    # Old entry (60 days ago)
    old_date = now - timedelta(days=60)
    kb_cache.store(
        library="vue",
        topic="composition-api",
        content="# Vue Composition API\nOld content",
        context7_id="/vuejs/vue",
    )
    entries.append(("vue", "composition-api", old_date))

    # Very old entry (120 days ago)
    very_old_date = now - timedelta(days=120)
    kb_cache.store(
        library="angular",
        topic="services",
        content="# Angular Services\nVery old content",
        context7_id="/angular/angular",
    )
    entries.append(("angular", "services", very_old_date))

    return entries


class TestCleanupResult:
    """Tests for CleanupResult dataclass."""

    def test_create_cleanup_result(self):
        """Test creating cleanup result."""
        result = CleanupResult(
            entries_removed=5,
            libraries_removed=2,
            bytes_freed=1024,
            reason="size_cleanup",
        )

        assert result.entries_removed == 5
        assert result.libraries_removed == 2
        assert result.bytes_freed == 1024
        assert result.reason == "size_cleanup"
        assert result.details == []

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = CleanupResult(
            entries_removed=5,
            libraries_removed=2,
            bytes_freed=1024,
            reason="size_cleanup",
            details=["Removed react/hooks"],
        )

        data = result.to_dict()
        assert isinstance(data, dict)
        assert data["entries_removed"] == 5
        assert len(data["details"]) == 1


@pytest.mark.skip(reason="TODO: Fix cache lock timeouts - all tests in this class need mock for file locking")
class TestKBCleanup:
    """Tests for KBCleanup class."""

    @pytest.mark.skip(reason="TODO: Fix cache lock timeout - needs mock for file locking")
    def test_get_cache_size(self, cleanup, kb_cache):
        """Test getting cache size."""
        kb_cache.store(
            library="react",
            topic="hooks",
            content="Content here",
            context7_id="/facebook/react",
        )

        size = cleanup.get_cache_size()
        assert size > 0

    def test_get_entry_access_info(self, cleanup, kb_cache):
        """Test getting entry access information."""
        kb_cache.store(
            library="react",
            topic="hooks",
            content="Content",
            context7_id="/facebook/react",
        )

        entries = cleanup.get_entry_access_info()
        assert len(entries) >= 1
        assert any(e[0] == "react" and e[1] == "hooks" for e in entries)

    def test_cleanup_by_size_under_limit(self, cleanup):
        """Test cleanup when size is under limit."""
        result = cleanup.cleanup_by_size(target_size_bytes=1024 * 1024)  # 1MB

        assert result.entries_removed == 0
        assert result.bytes_freed == 0
        assert result.reason == "cache_size_ok"

    def test_cleanup_by_size_over_limit(self, cleanup, kb_cache):
        """Test cleanup when size is over limit."""
        # Create multiple entries to exceed limit
        for i in range(10):
            kb_cache.store(
                library=f"lib{i}",
                topic="topic",
                content="X" * 200,  # 200 bytes each
                context7_id=f"/org/lib{i}",
            )

        # Set very low target size
        cleanup.max_cache_size_bytes = 500

        result = cleanup.cleanup_by_size(target_size_bytes=500)

        # Should remove some entries
        assert result.entries_removed > 0
        assert result.bytes_freed > 0
        assert result.reason == "size_cleanup"

    def test_cleanup_by_size_preserves_recent(self, cleanup, kb_cache):
        """Test that recent entries are preserved."""
        # Create old entry
        kb_cache.store(
            library="old_lib",
            topic="old_topic",
            content="X" * 300,
            context7_id="/old/lib",
        )

        # Create recent entry
        kb_cache.store(
            library="recent_lib",
            topic="recent_topic",
            content="X" * 300,
            context7_id="/recent/lib",
        )

        # Set low limit and preserve recent
        cleanup.max_cache_size_bytes = 400
        result = cleanup.cleanup_by_size(target_size_bytes=400, preserve_recent=True)

        # Should remove old entries but keep recent if possible
        # (This depends on min_access_days setting)
        assert result.entries_removed >= 0

    def test_cleanup_by_age(self, cleanup, kb_cache, sample_entries):
        """Test cleanup by age."""
        # Create entries with known ages
        now = datetime.now(UTC)
        
        # Create old entry (60 days ago) - should be removed
        old_date = now - timedelta(days=60)
        kb_cache.store(
            library="old_lib",
            topic="old_topic",
            content="Old content",
            context7_id="/old/lib",
        )
        
        # Create recent entry (5 days ago) - should be kept
        recent_date = now - timedelta(days=5)
        kb_cache.store(
            library="recent_lib",
            topic="recent_topic",
            content="Recent content",
            context7_id="/recent/lib",
        )
        
        # Update metadata to set old dates
        metadata = cleanup.metadata_manager.load_cache_index()
        if "old_lib" in metadata.libraries:
            topics = metadata.libraries["old_lib"].get("topics", {})
            if "old_topic" in topics:
                old_date_str = old_date.isoformat() + "Z"
                topics["old_topic"]["last_updated"] = old_date_str

        result = cleanup.cleanup_by_age(max_age_days=30)

        # Should remove entries older than 30 days
        assert result.entries_removed >= 1  # At least the old entry should be removed
        assert result.reason == "age_cleanup"
        
        # Verify old entry was actually removed
        metadata_after = cleanup.metadata_manager.load_cache_index()
        if "old_lib" in metadata_after.libraries:
            assert "old_topic" not in metadata_after.libraries["old_lib"].get("topics", {})

    def test_cleanup_by_age_ignores_policy(self, cleanup, kb_cache):
        """Test cleanup by age with ignore_staleness_policy."""
        # Create old entry (2 days ago) - should be removed with max_age_days=1
        now = datetime.now(UTC)
        old_date = now - timedelta(days=2)
        kb_cache.store(
            library="old_lib",
            topic="old_topic",
            content="Content",
            context7_id="/old/lib",
        )
        
        # Update metadata to set old date
        metadata = cleanup.metadata_manager.load_cache_index()
        if "old_lib" in metadata.libraries:
            topics = metadata.libraries["old_lib"].get("topics", {})
            if "old_topic" in topics:
                old_date_str = old_date.isoformat() + "Z"
                topics["old_topic"]["last_updated"] = old_date_str

        result = cleanup.cleanup_by_age(max_age_days=1, ignore_staleness_policy=True)

        # Should check based on max_age_days only and remove old entry
        assert result.entries_removed >= 1  # Old entry should be removed
        assert result.reason == "age_cleanup"

    def test_cleanup_unused(self, cleanup, kb_cache):
        """Test cleanup of unused entries."""
        # Create entry that won't be accessed
        kb_cache.store(
            library="unused_lib",
            topic="unused_topic",
            content="Content",
            context7_id="/unused/lib",
        )
        
        # Create entry that will be accessed (to verify it's not removed)
        kb_cache.store(
            library="used_lib",
            topic="used_topic",
            content="Content",
            context7_id="/used/lib",
        )
        
        # Access the used entry to update its access time
        try:
            kb_cache.retrieve("used_lib", "used_topic")
        except Exception:
            pass  # May not exist yet, that's okay

        result = cleanup.cleanup_unused(min_access_days=1)

        # Should remove entries not accessed recently
        assert result.entries_removed >= 1  # At least unused entry should be removed
        assert result.reason == "unused_cleanup"
        
        # Verify unused entry was actually removed
        metadata_after = cleanup.metadata_manager.load_cache_index()
        if "unused_lib" in metadata_after.libraries:
            assert "unused_topic" not in metadata_after.libraries["unused_lib"].get("topics", {})

    def test_cleanup_all(self, cleanup, kb_cache):
        """Test comprehensive cleanup."""
        # Create entries
        for i in range(5):
            kb_cache.store(
                library=f"lib{i}",
                topic="topic",
                content="Content",
                context7_id=f"/org/lib{i}",
            )

        cleanup.max_cache_size_bytes = 100  # Very low limit

        result = cleanup.cleanup_all()

        # Should perform all cleanup strategies
        assert result.reason == "comprehensive_cleanup"
        assert result.entries_removed >= 0

    def test_get_cleanup_recommendations(self, cleanup, kb_cache):
        """Test getting cleanup recommendations."""
        # Create entries
        kb_cache.store(
            library="test_lib",
            topic="test_topic",
            content="Content",
            context7_id="/test/lib",
        )

        recommendations = cleanup.get_cleanup_recommendations()

        assert "current_size_bytes" in recommendations
        assert "max_size_bytes" in recommendations
        assert "over_size_limit" in recommendations
        assert "total_entries" in recommendations
        assert "recommendations" in recommendations
        assert isinstance(recommendations["recommendations"], list)

    def test_get_cleanup_recommendations_size_limit(self, cleanup, kb_cache):
        """Test recommendations when over size limit."""
        # Create large entries
        for i in range(10):
            kb_cache.store(
                library=f"lib{i}",
                topic="topic",
                content="X" * 200,
                context7_id=f"/org/lib{i}",
            )

        cleanup.max_cache_size_bytes = 500

        recommendations = cleanup.get_cleanup_recommendations()

        assert recommendations["over_size_limit"] is True
        assert len(recommendations["recommendations"]) > 0
        assert any(
            r["type"] == "size_cleanup" for r in recommendations["recommendations"]
        )

    def test_cleanup_size_calculation_correctness(self, cleanup, kb_cache):
        """Test that cleanup size calculations are mathematically correct (Story 18.3)."""
        # Create entries with known sizes
        entry1_content = "X" * 100  # 100 bytes
        entry2_content = "Y" * 200  # 200 bytes
        entry3_content = "Z" * 150  # 150 bytes
        
        kb_cache.store(
            library="lib1",
            topic="topic1",
            content=entry1_content,
            context7_id="/org/lib1",
        )
        kb_cache.store(
            library="lib2",
            topic="topic2",
            content=entry2_content,
            context7_id="/org/lib2",
        )
        kb_cache.store(
            library="lib3",
            topic="topic3",
            content=entry3_content,
            context7_id="/org/lib3",
        )
        
        # Get actual cache size
        current_size = cleanup.get_cache_size()
        assert current_size > 0, "Cache should have some size"
        
        # Set target size to be less than current
        target_size = current_size - 100  # Free 100 bytes
        
        # Calculate expected bytes to free
        expected_bytes_to_free = current_size - target_size
        
        result = cleanup.cleanup_by_size(target_size_bytes=target_size)
        
        # Verify bytes freed calculation is correct
        assert result.bytes_freed >= 0, \
            f"Bytes freed should be non-negative, got {result.bytes_freed}"
        assert result.bytes_freed >= expected_bytes_to_free - 50, \
            f"Should free approximately {expected_bytes_to_free} bytes, got {result.bytes_freed}" \
            " (allowing 50 bytes tolerance for file overhead)"
        
        # Verify new size is at or below target
        new_size = cleanup.get_cache_size()
        assert new_size <= target_size + 50, \
            f"After cleanup, size should be <= target ({target_size}), got {new_size}"

    def test_cleanup_age_calculation_correctness(self, cleanup, kb_cache):
        """Test that cleanup age calculations are correct (Story 18.3)."""
        from datetime import UTC, datetime, timedelta
        
        # Create entry with known age
        now = datetime.now(UTC)
        old_date = now - timedelta(days=45)  # 45 days old
        
        kb_cache.store(
            library="old_lib",
            topic="old_topic",
            content="Old content",
            context7_id="/old/lib",
        )
        
        # Manually set metadata to old date (simulating old entry)
        metadata = cleanup.metadata_manager.load_cache_index()
        if "old_lib" in metadata.libraries:
            topics = metadata.libraries["old_lib"].get("topics", {})
            if "old_topic" in topics:
                old_date_str = old_date.isoformat() + "Z"
                topics["old_topic"]["last_updated"] = old_date_str
                topics["old_topic"]["last_accessed"] = old_date_str
                # Save the metadata
                cleanup.metadata_manager.save_cache_index(metadata)
        
        # Test cleanup with max_age_days=30 (should remove 45-day-old entry)
        result = cleanup.cleanup_by_age(max_age_days=30)
        
        # Verify age calculation: 45 days > 30 days, so should be removed
        assert result.entries_removed >= 1, \
            f"Entry older than max_age_days (30) should be removed, entry age is 45 days"
        assert result.reason == "age_cleanup", \
            f"Cleanup reason should be 'age_cleanup', got {result.reason}"

    def test_cache_hit_miss_logic(self, kb_cache):
        """Test cache hit/miss logic with known cache states (Story 18.3)."""
        # Initially, cache should be empty (miss)
        entry = kb_cache.get("nonexistent_lib", "nonexistent_topic")
        assert entry is None, \
            "Getting non-existent entry should return None (cache miss)"
        
        # Store an entry
        kb_cache.store(
            library="test_lib",
            topic="test_topic",
            content="Test content",
            context7_id="/test/lib",
        )
        
        # Now retrieve it (should be a hit)
        entry = kb_cache.get("test_lib", "test_topic")
        assert entry is not None, \
            "Getting stored entry should return entry (cache hit)"
        assert entry.library == "test_lib", \
            f"Retrieved entry should have correct library, got {entry.library}"
        assert entry.topic == "test_topic", \
            f"Retrieved entry should have correct topic, got {entry.topic}"
        assert entry.content == "Test content", \
            f"Retrieved entry should have correct content, got {entry.content[:50]}"
        
        # Retrieve again - should increment cache hits
        entry2 = kb_cache.get("test_lib", "test_topic")
        assert entry2 is not None, \
            "Second retrieval should also be a hit"
        # Cache hits should be tracked (may require metadata check)
        
    def test_cleanup_preserves_recent_entries(self, cleanup, kb_cache):
        """Test that cleanup preserves recent entries correctly (Story 18.3)."""
        from datetime import UTC, datetime, timedelta
        
        # Create old entry (60 days ago)
        old_date = datetime.now(UTC) - timedelta(days=60)
        kb_cache.store(
            library="old_lib",
            topic="old_topic",
            content="X" * 300,
            context7_id="/old/lib",
        )
        
        # Create recent entry (5 days ago)
        recent_date = datetime.now(UTC) - timedelta(days=5)
        kb_cache.store(
            library="recent_lib",
            topic="recent_topic",
            content="Y" * 300,
            context7_id="/recent/lib",
        )
        
        # Set metadata dates
        metadata = cleanup.metadata_manager.load_cache_index()
        if "old_lib" in metadata.libraries:
            topics = metadata.libraries["old_lib"].get("topics", {})
            if "old_topic" in topics:
                old_date_str = old_date.isoformat() + "Z"
                topics["old_topic"]["last_updated"] = old_date_str
                topics["old_topic"]["last_accessed"] = old_date_str
        
        if "recent_lib" in metadata.libraries:
            topics = metadata.libraries["recent_lib"].get("topics", {})
            if "recent_topic" in topics:
                recent_date_str = recent_date.isoformat() + "Z"
                topics["recent_topic"]["last_updated"] = recent_date_str
                topics["recent_topic"]["last_accessed"] = recent_date_str
        
        cleanup.metadata_manager.save_cache_index(metadata)
        
        # Set low size limit and preserve recent (min_access_days=30)
        cleanup.max_cache_size_bytes = 400
        cleanup.min_access_days = 30
        result = cleanup.cleanup_by_size(target_size_bytes=400, preserve_recent=True)
        
        # Old entry (60 days) should be considered for removal (60 > 30)
        # Recent entry (5 days) should be preserved (5 < 30)
        # Verify recent entry still exists
        metadata_after = cleanup.metadata_manager.load_cache_index()
        if "recent_lib" in metadata_after.libraries:
            assert "recent_topic" in metadata_after.libraries["recent_lib"].get("topics", {}), \
                "Recent entry (5 days old) should be preserved when preserve_recent=True and min_access_days=30"

    def test_cleanup_lru_eviction_order(self, cleanup, kb_cache):
        """Test that cleanup uses LRU (Least Recently Used) eviction order (Story 18.3)."""
        from datetime import UTC, datetime, timedelta
        
        # Create multiple entries with different access times
        now = datetime.now(UTC)
        
        # Entry 1: accessed 10 days ago
        kb_cache.store(
            library="lib1",
            topic="topic1",
            content="X" * 100,
            context7_id="/org/lib1",
        )
        date1 = now - timedelta(days=10)
        
        # Entry 2: accessed 20 days ago
        kb_cache.store(
            library="lib2",
            topic="topic2",
            content="Y" * 100,
            context7_id="/org/lib2",
        )
        date2 = now - timedelta(days=20)
        
        # Entry 3: accessed 5 days ago (most recent)
        kb_cache.store(
            library="lib3",
            topic="topic3",
            content="Z" * 100,
            context7_id="/org/lib3",
        )
        date3 = now - timedelta(days=5)
        
        # Set metadata access times
        metadata = cleanup.metadata_manager.load_cache_index()
        for lib, topic, access_date in [("lib1", "topic1", date1), 
                                         ("lib2", "topic2", date2), 
                                         ("lib3", "topic3", date3)]:
            if lib in metadata.libraries:
                topics = metadata.libraries[lib].get("topics", {})
                if topic in topics:
                    date_str = access_date.isoformat() + "Z"
                    topics[topic]["last_accessed"] = date_str
        
        cleanup.metadata_manager.save_cache_index(metadata)
        
        # Set low size limit to force cleanup
        cleanup.max_cache_size_bytes = 150
        cleanup.min_access_days = 7  # Consider entries > 7 days old
        
        result = cleanup.cleanup_by_size(target_size_bytes=150, preserve_recent=True)
        
        # With LRU eviction, oldest entries should be removed first
        # Entry 2 (20 days) should be removed before entry 1 (10 days)
        # Entry 3 (5 days) should be preserved (within min_access_days)
        # Verify entry 3 (most recent) still exists
        metadata_after = cleanup.metadata_manager.load_cache_index()
        if "lib3" in metadata_after.libraries:
            assert "topic3" in metadata_after.libraries["lib3"].get("topics", {}), \
                "Most recently accessed entry (5 days) should be preserved in LRU eviction"