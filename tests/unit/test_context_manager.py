"""
Unit tests for ContextManager.
"""

from pathlib import Path

import pytest

from tapps_agents.core.context_manager import ContextCache, ContextManager
from tapps_agents.core.tiered_context import ContextTier


@pytest.mark.unit
class TestContextCache:
    """Test cases for ContextCache."""

    @pytest.fixture
    def cache(self):
        """Create a ContextCache instance."""
        return ContextCache(max_size=10)

    def test_cache_get_miss(self, cache):
        """Test cache miss."""
        result = cache.get("missing_key", ttl=60)
        assert result is None

    def test_cache_put_get(self, cache):
        """Test cache put and get."""
        value = {"key": "value"}
        cache.put("test_key", value)

        result = cache.get("test_key", ttl=60)
        assert result == value

    def test_cache_ttl_expiry(self, cache):
        """Test TTL expiry."""
        from datetime import datetime, timedelta

        value = {"key": "value"}
        cache.put("test_key", value)

        # Simulate expiry by setting old timestamp
        cache.timestamps["test_key"] = datetime.now() - timedelta(seconds=120)

        result = cache.get("test_key", ttl=60)
        assert result is None

    def test_cache_max_size(self, cache):
        """Test cache max size enforcement."""
        # Fill cache beyond max_size
        for i in range(15):
            cache.put(f"key_{i}", {"value": i})

        # Oldest keys should be evicted
        assert cache.size() <= cache.max_size
        assert cache.get("key_0", ttl=60) is None  # Should be evicted
        assert cache.get("key_14", ttl=60) is not None  # Should still be there

    def test_cache_clear(self, cache):
        """Test cache clearing."""
        cache.put("key1", {"value": 1})
        cache.put("key2", {"value": 2})

        assert cache.size() == 2
        cache.clear()
        assert cache.size() == 0


@pytest.mark.unit
class TestContextManager:
    """Test cases for ContextManager."""

    @pytest.fixture
    def manager(self):
        """Create a ContextManager instance."""
        return ContextManager()

    @pytest.fixture
    def sample_python_file(self, tmp_path: Path):
        """Create a sample Python file."""
        code_file = tmp_path / "test_module.py"
        code_file.write_text(
            """
def func1(param: str) -> str:
    \"\"\"Test function.\"\"\"
    return param

class MyClass:
    \"\"\"Test class.\"\"\"
    pass
"""
        )
        return code_file

    @pytest.mark.asyncio
    async def test_get_context_tier1(self, manager, sample_python_file):
        """Test getting Tier 1 context."""
        context = manager.get_context(sample_python_file, ContextTier.TIER1)

        assert context["tier"] == "tier1"
        assert "file" in context
        assert "content" in context
        assert "token_estimate" in context

    @pytest.mark.asyncio
    async def test_get_context_tier2(self, manager, sample_python_file):
        """Test getting Tier 2 context."""
        context = manager.get_context(sample_python_file, ContextTier.TIER2)

        assert context["tier"] == "tier2"
        assert "content" in context
        # Tier 2 should have more content than Tier 1
        assert len(context["content"]) > 0

    @pytest.mark.asyncio
    async def test_get_context_caching(self, manager, sample_python_file):
        """Test context caching."""
        # Clear cache first
        manager.clear_cache(ContextTier.TIER1)

        manager.get_context(sample_python_file, ContextTier.TIER1, use_cache=True)
        context2 = manager.get_context(
            sample_python_file, ContextTier.TIER1, use_cache=True
        )

        # Second call should be cached
        assert context2.get("cached") is True
        # First call might also be cached if cache_key is same and file hasn't changed
        # So we just verify second is cached
        assert "cached" in context2

    def test_get_context_text_text_format(self, manager, sample_python_file):
        """Test getting context as text."""
        text = manager.get_context_text(
            sample_python_file, ContextTier.TIER1, format="text"
        )

        assert isinstance(text, str)
        assert len(text) > 0
        assert "Context for" in text or "tier1" in text.lower()

    def test_get_context_text_markdown_format(self, manager, sample_python_file):
        """Test getting context as markdown."""
        text = manager.get_context_text(
            sample_python_file, ContextTier.TIER1, format="markdown"
        )

        assert isinstance(text, str)
        assert "#" in text or "Context" in text

    def test_get_context_text_json_format(self, manager, sample_python_file):
        """Test getting context as JSON."""
        import json

        text = manager.get_context_text(
            sample_python_file, ContextTier.TIER1, format="json"
        )

        # Should be valid JSON
        parsed = json.loads(text)
        assert "tier" in parsed
        assert parsed["tier"] == "tier1"

    def test_clear_cache(self, manager, sample_python_file):
        """Test cache clearing."""
        manager.get_context(sample_python_file, ContextTier.TIER1)

        stats_before = manager.get_cache_stats()
        assert stats_before["tier1"]["size"] > 0

        manager.clear_cache(ContextTier.TIER1)

        stats_after = manager.get_cache_stats()
        assert stats_after["tier1"]["size"] == 0

    def test_get_cache_stats(self, manager, sample_python_file):
        """Test cache statistics."""
        manager.get_context(sample_python_file, ContextTier.TIER1)

        stats = manager.get_cache_stats()

        assert "tier1" in stats
        assert "size" in stats["tier1"]
        assert "max_size" in stats["tier1"]
