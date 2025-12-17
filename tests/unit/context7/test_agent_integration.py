"""
Unit tests for Context7 agent integration.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from tapps_agents.context7.agent_integration import (
    Context7AgentHelper,
    get_context7_helper,
)
from tapps_agents.core.config import (
    Context7Config,
    Context7KnowledgeBaseConfig,
    ProjectConfig,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory."""
    temp_dir = tempfile.mkdtemp()
    cache_root = Path(temp_dir) / "context7-cache"
    yield cache_root
    shutil.rmtree(temp_dir)


@pytest.fixture
def project_config(temp_cache_dir):
    """Create ProjectConfig with Context7 enabled."""
    config = ProjectConfig()
    config.context7 = Context7Config(
        enabled=True,
        knowledge_base=Context7KnowledgeBaseConfig(location=str(temp_cache_dir)),
    )
    return config


@pytest.fixture
def disabled_config():
    """Create ProjectConfig with Context7 disabled."""
    config = ProjectConfig()
    config.context7 = Context7Config(enabled=False)
    return config


@pytest.fixture
def helper(project_config, temp_cache_dir):
    """Create Context7AgentHelper instance."""
    return Context7AgentHelper(
        config=project_config, project_root=temp_cache_dir.parent
    )


@pytest.fixture
def disabled_helper(disabled_config):
    """Create Context7AgentHelper instance with Context7 disabled."""
    return Context7AgentHelper(config=disabled_config)


class TestContext7AgentHelper:
    """Tests for Context7AgentHelper class."""

    def test_init_enabled(self, helper):
        """Test initialization with Context7 enabled."""
        assert helper.enabled is True
        assert helper.kb_cache is not None
        assert helper.kb_lookup is not None

    def test_init_disabled(self, disabled_helper):
        """Test initialization with Context7 disabled."""
        assert disabled_helper.enabled is False

    @pytest.mark.asyncio
    async def test_get_documentation_disabled(self, disabled_helper):
        """Test get_documentation when Context7 is disabled."""
        result = await disabled_helper.get_documentation("react", "hooks")

        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="TODO: Fix cache lock timeout - needs mock for file locking")
    async def test_get_documentation_cache_hit(self, helper):
        """Test get_documentation with cache hit."""
        # Store entry in cache
        helper.kb_cache.store(
            library="react",
            topic="hooks",
            content="# React Hooks Documentation",
            context7_id="/facebook/react",
        )

        result = await helper.get_documentation("react", "hooks")

        assert result is not None
        assert result["library"] == "react"
        assert result["topic"] == "hooks"
        assert "React Hooks" in result["content"]
        assert result["source"] == "cache"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="TODO: Fix cache lock timeout - needs mock for file locking")
    async def test_get_documentation_with_fuzzy_match(self, helper):
        """Test get_documentation with fuzzy matching."""
        # Store entry
        helper.kb_cache.store(
            library="react",
            topic="hooks",
            content="Content",
            context7_id="/facebook/react",
        )

        # Search with slight variation (typo: "reakt" instead of "react")
        result = await helper.get_documentation("reakt", "hook", use_fuzzy_match=True)

        # Fuzzy match should find the entry despite typo
        assert result is not None
        assert result["library"] == "react"  # Should match to correct library
        assert result["topic"] == "hooks"  # Should match to correct topic
        assert result["source"] == "cache"

    @pytest.mark.asyncio
    async def test_search_libraries_disabled(self, disabled_helper):
        """Test search_libraries when Context7 is disabled."""
        result = await disabled_helper.search_libraries("react")

        assert result == []

    @pytest.mark.asyncio
    async def test_search_libraries_no_gateway(self, helper):
        """Test search_libraries without MCP Gateway."""
        result = await helper.search_libraries("react")

        # Should return empty list if no gateway
        assert result == []

    @pytest.mark.asyncio
    async def test_search_libraries_with_gateway(self, helper):
        """Test search_libraries with MCP Gateway."""
        mock_gateway = AsyncMock()
        mock_gateway.call_tool = AsyncMock(
            return_value={
                "success": True,
                "result": {"matches": [{"id": "/facebook/react", "name": "react"}]},
            }
        )
        helper.mcp_gateway = mock_gateway
        helper.kb_lookup.mcp_gateway = mock_gateway

        result = await helper.search_libraries("react")

        assert len(result) > 0

    def test_is_library_cached_disabled(self, disabled_helper):
        """Test is_library_cached when Context7 is disabled."""
        result = disabled_helper.is_library_cached("react", "hooks")

        assert result is False

    @pytest.mark.skip(reason="TODO: Fix cache lock timeout - needs mock for file locking")
    def test_is_library_cached_true(self, helper):
        """Test is_library_cached when entry exists."""
        helper.kb_cache.store(
            library="react",
            topic="hooks",
            content="Content",
            context7_id="/facebook/react",
        )

        result = helper.is_library_cached("react", "hooks")

        assert result is True

    def test_is_library_cached_false(self, helper):
        """Test is_library_cached when entry doesn't exist."""
        result = helper.is_library_cached("nonexistent", "topic")

        assert result is False

    def test_get_cache_statistics_disabled(self, disabled_helper):
        """Test get_cache_statistics when Context7 is disabled."""
        result = disabled_helper.get_cache_statistics()

        assert result["enabled"] is False

    @pytest.mark.skip(reason="TODO: Fix cache lock timeout - needs mock for file locking")
    def test_get_cache_statistics_enabled(self, helper):
        """Test get_cache_statistics with Context7 enabled."""
        helper.kb_cache.store(
            library="react",
            topic="hooks",
            content="Content",
            context7_id="/facebook/react",
        )

        result = helper.get_cache_statistics()

        assert result["enabled"] is True
        # Result should contain either success data or error, but not both
        # Validate specific expected structure based on operation success
        assert "total_entries" in result or "error" in result, \
            f"Result should contain either 'total_entries' (success) or 'error' (failure), " \
            f"got keys: {list(result.keys())}"
        # If successful, should have total_entries; if failed, should have error
        if "error" in result:
            assert result["success"] is False, \
                f"When error is present, success should be False, got {result.get('success')}"
            assert len(result["error"]) > 0, \
                "Error message should not be empty"
        else:
            assert "total_entries" in result, \
                "When no error, result should contain 'total_entries'"
            assert isinstance(result["total_entries"], int), \
                f"total_entries should be an integer, got {type(result['total_entries'])}"
            assert result["total_entries"] >= 0, \
                f"total_entries should be non-negative, got {result['total_entries']}"

    def test_should_use_context7_disabled(self, disabled_helper):
        """Test should_use_context7 when Context7 is disabled."""
        result = disabled_helper.should_use_context7(
            "I need react library documentation"
        )

        assert result is False

    def test_should_use_context7_with_keywords(self, helper):
        """Test should_use_context7 with library keywords."""
        # Test with various keywords
        assert helper.should_use_context7("I need react library") is True
        assert helper.should_use_context7("Check the framework documentation") is True
        assert helper.should_use_context7("What's the API for this package?") is True
        assert helper.should_use_context7("How do I use the SDK?") is True

    def test_should_use_context7_without_keywords(self, helper):
        """Test should_use_context7 without library keywords."""
        result = helper.should_use_context7("What's the weather today?")

        assert result is False


class TestGetContext7Helper:
    """Tests for get_context7_helper function."""

    def test_get_context7_helper_with_config(self, project_config, temp_cache_dir):
        """Test get_context7_helper with valid config."""
        mock_agent = Mock()
        mock_agent.config = project_config
        mock_agent.mcp_gateway = None

        helper = get_context7_helper(mock_agent, project_root=temp_cache_dir.parent)

        assert helper is not None
        assert helper.enabled is True

    def test_get_context7_helper_disabled_config(self, disabled_config):
        """Test get_context7_helper with disabled config."""
        mock_agent = Mock()
        mock_agent.config = disabled_config
        mock_agent.mcp_gateway = None

        helper = get_context7_helper(mock_agent)

        assert helper is None

    def test_get_context7_helper_no_config(self):
        """Test get_context7_helper with no config."""
        mock_agent = Mock()
        mock_agent.config = None

        helper = get_context7_helper(mock_agent)

        assert helper is None

    def test_get_context7_helper_with_mcp_gateway(self, project_config, temp_cache_dir):
        """Test get_context7_helper with MCP Gateway."""
        mock_agent = Mock()
        mock_agent.config = project_config
        mock_gateway = Mock()
        mock_agent.mcp_gateway = mock_gateway

        helper = get_context7_helper(mock_agent, project_root=temp_cache_dir.parent)

        assert helper is not None
        assert helper.kb_lookup.mcp_gateway == mock_gateway
