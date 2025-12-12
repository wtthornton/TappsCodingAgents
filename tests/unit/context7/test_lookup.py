"""
Tests for Context7 KB-first lookup workflow.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from tapps_agents.context7.kb_cache import KBCache
from tapps_agents.context7.lookup import KBLookup, LookupResult


class TestLookupResult:
    """Test LookupResult dataclass."""

    def test_lookup_result_creation(self):
        """Test LookupResult creation."""
        result = LookupResult(
            success=True,
            content="# React Hooks",
            source="cache",
            library="react",
            topic="hooks",
        )

        assert result.success is True
        assert result.content == "# React Hooks"
        assert result.source == "cache"
        assert result.library == "react"
        assert result.topic == "hooks"

    def test_lookup_result_to_dict(self):
        """Test LookupResult to_dict conversion."""
        result = LookupResult(
            success=True,
            content="# React Hooks",
            source="cache",
            library="react",
            topic="hooks",
            context7_id="/facebook/react",
            response_time_ms=12.5,
        )

        result_dict = result.to_dict()
        assert result_dict["success"] is True
        assert result_dict["content"] == "# React Hooks"
        assert result_dict["source"] == "cache"
        assert result_dict["library"] == "react"
        assert result_dict["topic"] == "hooks"
        assert result_dict["context7_id"] == "/facebook/react"
        assert result_dict["response_time_ms"] == 12.5


class TestKBLookup:
    """Test KBLookup workflow."""

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

    @pytest.fixture
    def kb_lookup(self, kb_cache):
        """Create KBLookup instance without MCP gateway."""
        return KBLookup(kb_cache)

    @pytest.mark.asyncio
    async def test_lookup_from_cache(self, kb_lookup, kb_cache):
        """Test lookup from cache (cache hit)."""
        # Pre-populate cache
        kb_cache.store(
            library="react",
            topic="hooks",
            content="# React Hooks\n\nUse hooks for state management.",
            context7_id="/facebook/react",
        )

        result = await kb_lookup.lookup("react", "hooks")

        assert result.success is True
        assert result.source == "cache"
        assert "React Hooks" in result.content
        assert result.library == "react"
        assert result.topic == "hooks"
        assert result.response_time_ms > 0

    @pytest.mark.asyncio
    async def test_lookup_cache_miss_no_client(self, kb_lookup):
        """Test lookup with cache miss and no API client."""
        result = await kb_lookup.lookup("react", "hooks")

        assert result.success is False
        assert "No documentation found" in result.error or "unavailable" in result.error

    @pytest.mark.asyncio
    async def test_lookup_with_resolve_func(self, kb_cache):
        """Test lookup with resolve library function."""

        def resolve_func(library: str):
            return {
                "library": library,
                "matches": [{"id": "/facebook/react", "name": "React"}],
            }

        def get_docs_func(library_id: str, topic: str = None):
            return {
                "content": "# React Hooks\n\nUse hooks for state management.",
                "library_id": library_id,
                "topic": topic,
            }

        kb_lookup = KBLookup(
            kb_cache, resolve_library_func=resolve_func, get_docs_func=get_docs_func
        )

        result = await kb_lookup.lookup("react", "hooks")

        assert result.success is True
        assert result.source == "api"
        assert "React Hooks" in result.content
        assert result.context7_id == "/facebook/react"

    @pytest.mark.asyncio
    async def test_lookup_with_mcp_gateway(self, kb_cache):
        """Test lookup with MCP Gateway."""
        # Mock MCP Gateway
        mock_gateway = Mock()
        mock_gateway.call_tool = Mock(
            side_effect=[
                # Resolve library ID call
                {
                    "success": True,
                    "result": {"matches": [{"id": "/facebook/react", "name": "React"}]},
                },
                # Get docs call
                {
                    "success": True,
                    "result": {
                        "content": "# React Hooks\n\nUse hooks for state management.",
                        "library_id": "/facebook/react",
                        "topic": "hooks",
                    },
                },
            ]
        )

        kb_lookup = KBLookup(kb_cache, mcp_gateway=mock_gateway)

        result = await kb_lookup.lookup("react", "hooks")

        assert result.success is True
        assert result.source == "api"
        assert "React Hooks" in result.content
        assert result.context7_id == "/facebook/react"
        assert mock_gateway.call_tool.call_count == 2

    @pytest.mark.asyncio
    async def test_lookup_default_topic(self, kb_cache):
        """Test lookup with default topic when not provided."""
        # Pre-populate cache with default topic
        kb_cache.store(
            library="react",
            topic="overview",
            content="# React Overview",
            context7_id="/facebook/react",
        )

        kb_lookup = KBLookup(kb_cache)
        result = await kb_lookup.lookup("react")

        assert result.success is True
        assert result.topic == "overview"

    @pytest.mark.asyncio
    async def test_lookup_resolve_failure(self, kb_cache):
        """Test lookup when library resolution fails."""

        def resolve_func(library: str):
            return {"library": library, "matches": []}

        kb_lookup = KBLookup(kb_cache, resolve_library_func=resolve_func)

        result = await kb_lookup.lookup("nonexistent", "topic")

        assert result.success is False

    @pytest.mark.asyncio
    async def test_lookup_api_failure(self, kb_cache):
        """Test lookup when API call fails."""

        def resolve_func(library: str):
            return {
                "library": library,
                "matches": [{"id": "/facebook/react", "name": "React"}],
            }

        def get_docs_func(library_id: str, topic: str = None):
            raise Exception("API call failed")

        kb_lookup = KBLookup(
            kb_cache, resolve_library_func=resolve_func, get_docs_func=get_docs_func
        )

        result = await kb_lookup.lookup("react", "hooks")

        assert result.success is False
        assert "API call failed" in result.error

    @pytest.mark.asyncio
    async def test_lookup_caches_api_result(self, kb_cache):
        """Test that API results are cached."""

        def resolve_func(library: str):
            return {
                "library": library,
                "matches": [{"id": "/facebook/react", "name": "React"}],
            }

        call_count = {"count": 0}

        def get_docs_func(library_id: str, topic: str = None):
            call_count["count"] += 1
            return {
                "content": f"# React Hooks (call {call_count['count']})",
                "library_id": library_id,
                "topic": topic,
            }

        kb_lookup = KBLookup(
            kb_cache, resolve_library_func=resolve_func, get_docs_func=get_docs_func
        )

        # First lookup - should call API
        result1 = await kb_lookup.lookup("react", "hooks")
        assert result1.success is True
        assert result1.source == "api"
        assert call_count["count"] == 1

        # Second lookup - should use cache
        result2 = await kb_lookup.lookup("react", "hooks")
        assert result2.success is True
        assert result2.source == "cache"
        assert call_count["count"] == 1  # Should not increment
