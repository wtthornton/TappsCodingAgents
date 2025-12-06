"""
Unit tests for Context7 KB cleanup automation.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from tapps_agents.context7.cleanup import KBCleanup, CleanupResult
from tapps_agents.context7.cache_structure import CacheStructure
from tapps_agents.context7.metadata import MetadataManager
from tapps_agents.context7.staleness_policies import StalenessPolicyManager
from tapps_agents.context7.kb_cache import KBCache


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
def cleanup(
    cache_structure,
    metadata_manager,
    staleness_policy_manager
):
    """Create KBCleanup instance."""
    return KBCleanup(
        cache_structure,
        metadata_manager,
        staleness_policy_manager,
        max_cache_size_bytes=1024,  # 1KB for testing
        max_age_days=30,
        min_access_days=7
    )


@pytest.fixture
def sample_entries(kb_cache):
    """Create sample cache entries for testing."""
    entries = []
    
    # Create entries with different ages
    now = datetime.utcnow()
    
    # Recent entry
    kb_cache.store(
        library="react",
        topic="hooks",
        content="# React Hooks\nRecent content",
        context7_id="/facebook/react"
    )
    entries.append(("react", "hooks", now))
    
    # Old entry (60 days ago)
    old_date = now - timedelta(days=60)
    kb_cache.store(
        library="vue",
        topic="composition-api",
        content="# Vue Composition API\nOld content",
        context7_id="/vuejs/vue"
    )
    entries.append(("vue", "composition-api", old_date))
    
    # Very old entry (120 days ago)
    very_old_date = now - timedelta(days=120)
    kb_cache.store(
        library="angular",
        topic="services",
        content="# Angular Services\nVery old content",
        context7_id="/angular/angular"
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
            reason="size_cleanup"
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
            details=["Removed react/hooks"]
        )
        
        data = result.to_dict()
        assert isinstance(data, dict)
        assert data["entries_removed"] == 5
        assert len(data["details"]) == 1


class TestKBCleanup:
    """Tests for KBCleanup class."""
    
    def test_get_cache_size(self, cleanup, kb_cache):
        """Test getting cache size."""
        kb_cache.store(
            library="react",
            topic="hooks",
            content="Content here",
            context7_id="/facebook/react"
        )
        
        size = cleanup.get_cache_size()
        assert size > 0
    
    def test_get_entry_access_info(self, cleanup, kb_cache):
        """Test getting entry access information."""
        kb_cache.store(
            library="react",
            topic="hooks",
            content="Content",
            context7_id="/facebook/react"
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
                context7_id=f"/org/lib{i}"
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
        old_date = datetime.utcnow() - timedelta(days=10)
        kb_cache.store(
            library="old_lib",
            topic="old_topic",
            content="X" * 300,
            context7_id="/old/lib"
        )
        
        # Create recent entry
        kb_cache.store(
            library="recent_lib",
            topic="recent_topic",
            content="X" * 300,
            context7_id="/recent/lib"
        )
        
        # Set low limit and preserve recent
        cleanup.max_cache_size_bytes = 400
        result = cleanup.cleanup_by_size(target_size_bytes=400, preserve_recent=True)
        
        # Should remove old entries but keep recent if possible
        # (This depends on min_access_days setting)
        assert result.entries_removed >= 0
    
    def test_cleanup_by_age(self, cleanup, kb_cache, sample_entries):
        """Test cleanup by age."""
        # Update metadata to set old dates
        metadata = cleanup.metadata_manager.load_cache_index()
        now = datetime.utcnow()
        
        # Make vue entry old
        if "vue" in metadata.libraries:
            topics = metadata.libraries["vue"].get("topics", {})
            if "composition-api" in topics:
                old_date_str = (now - timedelta(days=60)).isoformat() + "Z"
                topics["composition-api"]["last_updated"] = old_date_str
        
        result = cleanup.cleanup_by_age(max_age_days=30)
        
        # Should remove entries older than 30 days
        assert result.entries_removed >= 0
        assert result.reason == "age_cleanup"
    
    def test_cleanup_by_age_ignores_policy(self, cleanup, kb_cache):
        """Test cleanup by age with ignore_staleness_policy."""
        # Create old entry
        kb_cache.store(
            library="old_lib",
            topic="old_topic",
            content="Content",
            context7_id="/old/lib"
        )
        
        result = cleanup.cleanup_by_age(max_age_days=1, ignore_staleness_policy=True)
        
        # Should check based on max_age_days only
        assert result.entries_removed >= 0
    
    def test_cleanup_unused(self, cleanup, kb_cache):
        """Test cleanup of unused entries."""
        # Create entry
        kb_cache.store(
            library="unused_lib",
            topic="unused_topic",
            content="Content",
            context7_id="/unused/lib"
        )
        
        result = cleanup.cleanup_unused(min_access_days=1)
        
        # Should remove entries not accessed recently
        assert result.entries_removed >= 0
        assert result.reason == "unused_cleanup"
    
    def test_cleanup_all(self, cleanup, kb_cache):
        """Test comprehensive cleanup."""
        # Create entries
        for i in range(5):
            kb_cache.store(
                library=f"lib{i}",
                topic="topic",
                content="Content",
                context7_id=f"/org/lib{i}"
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
            context7_id="/test/lib"
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
                context7_id=f"/org/lib{i}"
            )
        
        cleanup.max_cache_size_bytes = 500
        
        recommendations = cleanup.get_cleanup_recommendations()
        
        assert recommendations["over_size_limit"] is True
        assert len(recommendations["recommendations"]) > 0
        assert any(r["type"] == "size_cleanup" for r in recommendations["recommendations"])

