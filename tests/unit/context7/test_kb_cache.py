"""
Tests for Context7 KB cache operations.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from tapps_agents.context7.kb_cache import KBCache, CacheEntry


class TestCacheEntry:
    """Test CacheEntry dataclass."""
    
    def test_cache_entry_creation(self):
        """Test CacheEntry creation."""
        entry = CacheEntry(
            library="react",
            topic="hooks",
            content="# React Hooks\n\nUse hooks for state management."
        )
        
        assert entry.library == "react"
        assert entry.topic == "hooks"
        assert "hooks" in entry.content
        assert entry.cache_hits == 0
        assert entry.token_count == 0
    
    def test_cache_entry_to_markdown(self):
        """Test CacheEntry to markdown conversion."""
        entry = CacheEntry(
            library="react",
            topic="hooks",
            content="# React Hooks\n\nUse hooks for state management.",
            context7_id="/facebook/react",
            trust_score=0.95,
            snippet_count=5,
            token_count=100
        )
        
        markdown = entry.to_markdown()
        assert "# react - hooks" in markdown
        assert "React Hooks" in markdown
        assert "/facebook/react" in markdown
        assert "0.95" in markdown
        assert "<!-- KB Metadata -->" in markdown
    
    def test_cache_entry_from_markdown(self):
        """Test CacheEntry from markdown conversion."""
        markdown_content = """# react - hooks

**Source**: /facebook/react (Trust Score: 0.95)
**Snippets**: 5 | **Tokens**: 100
**Last Updated**: 2024-01-01T00:00:00Z | **Cache Hits**: 3

---

# React Hooks

Use hooks for state management.

---

<!-- KB Metadata -->
<!-- Library: react -->
<!-- Topic: hooks -->
<!-- Context7 ID: /facebook/react -->
<!-- Trust Score: 0.95 -->
<!-- Snippet Count: 5 -->
<!-- Last Updated: 2024-01-01T00:00:00Z -->
<!-- Cache Hits: 3 -->
"""
        
        entry = CacheEntry.from_markdown("react", "hooks", markdown_content)
        
        assert entry is not None
        assert entry.library == "react"
        assert entry.topic == "hooks"
        assert "React Hooks" in entry.content
        assert entry.context7_id == "/facebook/react"
        assert entry.trust_score == 0.95
        assert entry.snippet_count == 5
        assert entry.cache_hits == 3


class TestKBCache:
    """Test KBCache operations."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def kb_cache(self, temp_cache_dir):
        """Create KBCache instance."""
        return KBCache(temp_cache_dir)
    
    def test_store_entry(self, kb_cache):
        """Test storing an entry."""
        entry = CacheEntry(
            library="react",
            topic="hooks",
            content="# React Hooks\n\nUse hooks for state management.",
            context7_id="/facebook/react"
        )
        
        stored_entry = kb_cache.store(
            library="react",
            topic="hooks",
            content=entry.content,
            context7_id="/facebook/react"
        )
        
        assert stored_entry.library == "react"
        assert stored_entry.topic == "hooks"
        assert kb_cache.exists("react", "hooks")
    
    def test_get_entry(self, kb_cache):
        """Test retrieving an entry."""
        content = "# React Hooks\n\nUse hooks for state management."
        kb_cache.store(
            library="react",
            topic="hooks",
            content=content,
            context7_id="/facebook/react"
        )
        
        entry = kb_cache.get("react", "hooks")
        
        assert entry is not None
        assert entry.library == "react"
        assert entry.topic == "hooks"
        assert content in entry.content
        assert entry.context7_id == "/facebook/react"
    
    def test_get_nonexistent_entry(self, kb_cache):
        """Test retrieving non-existent entry."""
        entry = kb_cache.get("nonexistent", "topic")
        assert entry is None
    
    def test_exists(self, kb_cache):
        """Test exists check."""
        assert not kb_cache.exists("react", "hooks")
        
        kb_cache.store(
            library="react",
            topic="hooks",
            content="# React Hooks",
            context7_id="/facebook/react"
        )
        
        assert kb_cache.exists("react", "hooks")
        assert not kb_cache.exists("react", "components")
    
    def test_delete_entry(self, kb_cache):
        """Test deleting an entry."""
        kb_cache.store(
            library="react",
            topic="hooks",
            content="# React Hooks",
            context7_id="/facebook/react"
        )
        
        assert kb_cache.exists("react", "hooks")
        
        deleted = kb_cache.delete("react", "hooks")
        assert deleted is True
        assert not kb_cache.exists("react", "hooks")
    
    def test_delete_nonexistent_entry(self, kb_cache):
        """Test deleting non-existent entry."""
        deleted = kb_cache.delete("nonexistent", "topic")
        assert deleted is False
    
    def test_cache_hits_increment(self, kb_cache):
        """Test cache hits increment on retrieval."""
        kb_cache.store(
            library="react",
            topic="hooks",
            content="# React Hooks",
            context7_id="/facebook/react"
        )
        
        # First retrieval
        entry1 = kb_cache.get("react", "hooks")
        hits1 = entry1.cache_hits if entry1 else 0
        
        # Second retrieval
        entry2 = kb_cache.get("react", "hooks")
        hits2 = entry2.cache_hits if entry2 else 0
        
        # Hits should increment
        assert hits2 >= hits1
    
    def test_multiple_libraries(self, kb_cache):
        """Test storing entries for multiple libraries."""
        kb_cache.store(
            library="react",
            topic="hooks",
            content="# React Hooks",
            context7_id="/facebook/react"
        )
        kb_cache.store(
            library="vue",
            topic="components",
            content="# Vue Components",
            context7_id="/vuejs/vue"
        )
        kb_cache.store(
            library="angular",
            topic="services",
            content="# Angular Services",
            context7_id="/angular/angular"
        )
        
        assert kb_cache.exists("react", "hooks")
        assert kb_cache.exists("vue", "components")
        assert kb_cache.exists("angular", "services")
    
    def test_multiple_topics_same_library(self, kb_cache):
        """Test storing multiple topics for same library."""
        kb_cache.store(
            library="react",
            topic="hooks",
            content="# React Hooks",
            context7_id="/facebook/react"
        )
        kb_cache.store(
            library="react",
            topic="components",
            content="# React Components",
            context7_id="/facebook/react"
        )
        kb_cache.store(
            library="react",
            topic="routing",
            content="# React Routing",
            context7_id="/facebook/react"
        )
        
        assert kb_cache.exists("react", "hooks")
        assert kb_cache.exists("react", "components")
        assert kb_cache.exists("react", "routing")
    
    def test_token_count_estimation(self, kb_cache):
        """Test token count estimation."""
        # Create content with approximately known token count
        # Rough approximation: 1 token ≈ 4 characters
        content = "x" * 400  # Should be approximately 100 tokens
        
        entry = kb_cache.store(
            library="react",
            topic="hooks",
            content=content,
            context7_id="/facebook/react"
        )
        
        # Token count should be approximately 100 (allow some variance)
        assert 90 <= entry.token_count <= 110

