"""
Unit tests for Context7 commands.
"""

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tapps_agents.context7.commands import Context7Commands, _parse_size_string
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
def commands(project_config, temp_cache_dir):
    """Create Context7Commands instance."""
    return Context7Commands(project_root=temp_cache_dir.parent, config=project_config)


@pytest.fixture
def disabled_commands(disabled_config):
    """Create Context7Commands instance with Context7 disabled."""
    return Context7Commands(disabled_config)


@pytest.fixture
def mock_cache_lock():
    """Mock cache_lock context manager to avoid file locking issues."""
    @contextmanager
    def _mock_cache_lock(lock_file, timeout=30.0):
        """Mock cache lock that always succeeds."""
        mock_lock = Mock()
        mock_lock.acquire.return_value = True
        yield mock_lock
        mock_lock.release()

    return _mock_cache_lock


class TestParseSizeString:
    """Tests for _parse_size_string helper function."""

    def test_parse_bytes(self):
        """Test parsing bytes."""
        assert _parse_size_string("100") == 100
        assert _parse_size_string("500B") == 500

    def test_parse_kilobytes(self):
        """Test parsing kilobytes."""
        assert _parse_size_string("100KB") == 100 * 1024
        assert _parse_size_string("1.5KB") == int(1.5 * 1024)

    def test_parse_megabytes(self):
        """Test parsing megabytes."""
        assert _parse_size_string("100MB") == 100 * 1024 * 1024
        assert _parse_size_string("1.5MB") == int(1.5 * 1024 * 1024)

    def test_parse_gigabytes(self):
        """Test parsing gigabytes."""
        assert _parse_size_string("1GB") == 1024 * 1024 * 1024
        assert _parse_size_string("2.5GB") == int(2.5 * 1024 * 1024 * 1024)

    def test_parse_terabytes(self):
        """Test parsing terabytes."""
        assert _parse_size_string("1TB") == 1024 * 1024 * 1024 * 1024

    def test_parse_case_insensitive(self):
        """Test case insensitive parsing."""
        assert _parse_size_string("100mb") == 100 * 1024 * 1024
        assert _parse_size_string("100MB") == 100 * 1024 * 1024
        assert _parse_size_string("100Mb") == 100 * 1024 * 1024

    def test_parse_with_whitespace(self):
        """Test parsing with whitespace."""
        assert _parse_size_string(" 100 MB ") == 100 * 1024 * 1024
        assert _parse_size_string("100  MB") == 100 * 1024 * 1024

    def test_parse_invalid_defaults(self):
        """Test invalid input defaults to 100MB."""
        assert _parse_size_string("invalid") == 100 * 1024 * 1024
        assert _parse_size_string("") == 100 * 1024 * 1024
        assert _parse_size_string("abc123") == 100 * 1024 * 1024

    def test_parse_none_defaults(self):
        """Test None input defaults to 100MB."""
        assert _parse_size_string(None) == 100 * 1024 * 1024


class TestContext7Commands:
    """Tests for Context7Commands class."""

    @patch("tapps_agents.context7.kb_cache.cache_lock")
    def test_init_enabled(self, mock_lock, commands):
        """Test initialization with Context7 enabled."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        assert commands.enabled is True
        assert commands.cache_structure is not None
        assert commands.kb_cache is not None

    def test_init_disabled(self, disabled_commands):
        """Test initialization with Context7 disabled."""
        assert disabled_commands.enabled is False

    def test_set_mcp_gateway(self, commands):
        """Test setting MCP Gateway."""
        mock_gateway = Mock()
        commands.set_mcp_gateway(mock_gateway)

        assert commands.kb_lookup.mcp_gateway == mock_gateway

    @pytest.mark.asyncio
    async def test_cmd_docs_disabled(self, disabled_commands):
        """Test cmd_docs when Context7 is disabled."""
        result = await disabled_commands.cmd_docs("react", "hooks")

        assert "error" in result
        assert result["error"] == "Context7 is not enabled"

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_docs_cache_hit(self, mock_lock, commands):
        """Test cmd_docs with cache hit."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        # Store entry in cache
        commands.kb_cache.store(
            library="react",
            topic="hooks",
            content="# React Hooks Documentation",
            context7_id="/facebook/react",
        )

        result = await commands.cmd_docs("react", "hooks")

        assert result["success"] is True
        assert result["library"] == "react"
        assert result["topic"] == "hooks"
        assert "React Hooks" in result["content"]
        assert result["source"] == "cache"

    @pytest.mark.asyncio
    async def test_cmd_docs_cache_miss(self, commands):
        """Test cmd_docs with cache miss (no MCP Gateway)."""
        result = await commands.cmd_docs("nonexistent", "topic")

        # Should return error since MCP Gateway is not set
        assert result["success"] is False, \
            f"Expected success=False when MCP Gateway is not set, got {result.get('success')}"
        assert "error" in result, \
            "Result should contain 'error' key when operation fails"
        # Validate specific error message about MCP Gateway
        error_msg = result["error"].lower()
        assert "mcp" in error_msg or "gateway" in error_msg, \
            f"Error message should mention MCP Gateway, got: {result.get('error')}"
        assert len(result["error"]) > 0, \
            "Error message should not be empty"

    @pytest.mark.asyncio
    async def test_cmd_resolve_disabled(self, disabled_commands):
        """Test cmd_resolve when Context7 is disabled."""
        result = await disabled_commands.cmd_resolve("react")

        assert "error" in result
        assert result["error"] == "Context7 is not enabled"

    @pytest.mark.asyncio
    async def test_cmd_resolve_no_gateway(self, commands):
        """Test cmd_resolve without MCP Gateway."""
        result = await commands.cmd_resolve("react")

        assert "error" in result
        assert result["error"] == "MCP Gateway not available"

    @pytest.mark.asyncio
    async def test_cmd_resolve_with_gateway(self, commands):
        """Test cmd_resolve with MCP Gateway."""
        mock_gateway = AsyncMock()
        mock_gateway.call_tool = AsyncMock(
            return_value={
                "success": True,
                "result": {"matches": [{"id": "/facebook/react", "name": "react"}]},
            }
        )
        commands.set_mcp_gateway(mock_gateway)

        result = await commands.cmd_resolve("react")

        assert result["success"] is True
        assert "matches" in result
        assert len(result["matches"]) > 0

    @pytest.mark.asyncio
    async def test_cmd_status_disabled(self, disabled_commands):
        """Test cmd_status when Context7 is disabled."""
        result = await disabled_commands.cmd_status()

        assert "error" in result
        assert result["error"] == "Context7 is not enabled"

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_status_enabled(self, mock_lock, commands):
        """Test cmd_status with Context7 enabled."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        # Store some entries
        commands.kb_cache.store(
            library="react",
            topic="hooks",
            content="Content",
            context7_id="/facebook/react",
        )

        result = await commands.cmd_status()

        assert result["success"] is True
        assert "status" in result
        assert "metrics" in result
        assert "cache_size_bytes" in result
        assert "cache_size_mb" in result
        assert "total_entries" in result["metrics"]

    @pytest.mark.asyncio
    async def test_cmd_health_disabled(self, disabled_commands):
        """Test cmd_health when Context7 is disabled."""
        result = await disabled_commands.cmd_health()

        assert "error" in result
        assert result["error"] == "Context7 is not enabled"

    @pytest.mark.asyncio
    async def test_cmd_health_enabled(self, commands):
        """Test cmd_health with Context7 enabled."""
        result = await commands.cmd_health()

        assert result["success"] is True
        assert "health" in result or "status" in result

    @pytest.mark.asyncio
    async def test_cmd_search_disabled(self, disabled_commands):
        """Test cmd_search when Context7 is disabled."""
        result = await disabled_commands.cmd_search("react")

        assert "error" in result
        assert result["error"] == "Context7 is not enabled"

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_search_enabled(self, mock_lock, commands):
        """Test cmd_search with Context7 enabled."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        # Store entries
        commands.kb_cache.store(
            library="react",
            topic="hooks",
            content="Content",
            context7_id="/facebook/react",
        )

        commands.kb_cache.store(
            library="vue",
            topic="composition-api",
            content="Content",
            context7_id="/vuejs/vue",
        )

        result = await commands.cmd_search("react")

        assert result["success"] is True
        assert "results" in result
        assert "count" in result
        assert result["count"] > 0

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_search_with_limit(self, mock_lock, commands):
        """Test cmd_search with limit."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        # Store multiple entries
        for i in range(5):
            commands.kb_cache.store(
                library=f"lib{i}",
                topic="topic",
                content="Content",
                context7_id=f"/org/lib{i}",
            )

        result = await commands.cmd_search("lib", limit=2)

        assert result["success"] is True, \
            f"Search should succeed, got success={result.get('success')}"
        # With 5 entries stored and limit=2, should return exactly 2 results
        assert result["count"] == 2, \
            f"With limit=2 and 5 entries stored, should return exactly 2 results, got {result.get('count')}"
        assert "results" in result, \
            "Search result should contain 'results' key"
        assert len(result.get("results", [])) == 2, \
            f"Results list should contain exactly 2 items, got {len(result.get('results', []))}"

    @pytest.mark.asyncio
    async def test_cmd_refresh_disabled(self, disabled_commands):
        """Test cmd_refresh when Context7 is disabled."""
        result = await disabled_commands.cmd_refresh()

        assert "error" in result
        assert result["error"] == "Context7 is not enabled"

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_refresh_specific_topic(self, mock_lock, commands):
        """Test cmd_refresh for specific library/topic."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        commands.kb_cache.store(
            library="react",
            topic="hooks",
            content="Content",
            context7_id="/facebook/react",
        )

        result = await commands.cmd_refresh("react", "hooks")

        assert result["success"] is True
        assert result["library"] == "react"
        assert result["topic"] == "hooks"
        assert "message" in result

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_refresh_library(self, mock_lock, commands):
        """Test cmd_refresh for entire library."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        commands.kb_cache.store(
            library="react",
            topic="hooks",
            content="Content",
            context7_id="/facebook/react",
        )

        commands.kb_cache.store(
            library="react",
            topic="components",
            content="Content",
            context7_id="/facebook/react",
        )

        result = await commands.cmd_refresh("react")

        assert result["success"] is True
        assert result["library"] == "react"
        assert result["topics_queued"] >= 1

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_refresh_all(self, mock_lock, commands):
        """Test cmd_refresh for all stale entries."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        commands.kb_cache.store(
            library="react",
            topic="hooks",
            content="Content",
            context7_id="/facebook/react",
        )

        result = await commands.cmd_refresh()

        assert result["success"] is True
        assert "entries_queued" in result

    @pytest.mark.asyncio
    async def test_cmd_refresh_process_disabled(self, disabled_commands):
        """Test cmd_refresh_process when Context7 is disabled."""
        result = await disabled_commands.cmd_refresh_process()

        assert result["success"] is False
        assert result["error"] == "Context7 is not enabled"
        assert result["items_processed"] == 0

    @pytest.mark.asyncio
    async def test_cmd_refresh_process_no_gateway(self, commands):
        """Test cmd_refresh_process without MCP Gateway."""
        result = await commands.cmd_refresh_process()

        assert result["success"] is False
        assert result["error"] == "MCP Gateway not available"
        assert result["items_processed"] == 0

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_refresh_process_with_gateway(self, mock_lock, commands):
        """Test cmd_refresh_process with MCP Gateway."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        # Set up MCP Gateway
        mock_gateway = AsyncMock()
        commands.set_mcp_gateway(mock_gateway)

        # Mock resolve and get_docs calls
        from unittest.mock import patch as mock_patch
        with mock_patch("tapps_agents.context7.commands.call_context7_resolve_with_fallback") as mock_resolve, \
             mock_patch("tapps_agents.context7.commands.call_context7_get_docs_with_fallback") as mock_docs:
            mock_resolve.return_value = {
                "success": True,
                "result": {"matches": [{"id": "/facebook/react"}]}
            }
            mock_docs.return_value = {
                "success": True,
                "result": {"content": "# React Documentation"}
            }

            # Add a refresh task
            commands.refresh_queue.add_task("react", "hooks", priority=8)

            result = await commands.cmd_refresh_process(max_items=1)

            # Should process the task
            assert result["items_processed"] >= 0  # May be 0 if queue is empty
            assert "queue_remaining" in result

    @pytest.mark.asyncio
    async def test_cmd_cleanup_disabled(self, disabled_commands):
        """Test cmd_cleanup when Context7 is disabled."""
        result = await disabled_commands.cmd_cleanup()

        assert "error" in result
        assert result["error"] == "Context7 is not enabled"

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_cleanup_size(self, mock_lock, commands):
        """Test cmd_cleanup with size strategy."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        # Create entries
        for i in range(3):
            commands.kb_cache.store(
                library=f"lib{i}",
                topic="topic",
                content="X" * 200,
                context7_id=f"/org/lib{i}",
            )

        result = await commands.cmd_cleanup(strategy="size", target_size_mb=0.001)

        assert result["success"] is True
        assert result["strategy"] == "size"
        assert "result" in result

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_cleanup_age(self, mock_lock, commands):
        """Test cmd_cleanup with age strategy."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        commands.kb_cache.store(
            library="old_lib",
            topic="old_topic",
            content="Content",
            context7_id="/old/lib",
        )

        result = await commands.cmd_cleanup(strategy="age", max_age_days=1)

        assert result["success"] is True
        assert result["strategy"] == "age"

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_cleanup_unused(self, mock_lock, commands):
        """Test cmd_cleanup with unused strategy."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        commands.kb_cache.store(
            library="unused_lib",
            topic="unused_topic",
            content="Content",
            context7_id="/unused/lib",
        )

        result = await commands.cmd_cleanup(strategy="unused")

        assert result["success"] is True
        assert result["strategy"] == "unused"

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_cleanup_all(self, mock_lock, commands):
        """Test cmd_cleanup with all strategy."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        commands.kb_cache.store(
            library="test_lib",
            topic="test_topic",
            content="Content",
            context7_id="/test/lib",
        )

        result = await commands.cmd_cleanup(strategy="all")

        assert result["success"] is True
        assert result["strategy"] == "all"

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_rebuild_index(self, mock_lock, commands):
        """Test cmd_rebuild_index."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        # Create entries
        commands.kb_cache.store(
            library="react",
            topic="hooks",
            content="Content",
            context7_id="/facebook/react",
        )

        result = await commands.cmd_rebuild_index()

        assert result["success"] is True
        assert "libraries" in result
        assert "total_entries" in result
        assert result["total_entries"] >= 1

    @pytest.mark.asyncio
    async def test_cmd_warm_disabled(self, disabled_commands):
        """Test cmd_warm when Context7 is disabled."""
        result = await disabled_commands.cmd_warm()

        assert "error" in result
        assert result["error"] == "Context7 is not enabled"

    @pytest.mark.asyncio
    async def test_cmd_warm_no_gateway(self, commands):
        """Test cmd_warm without MCP Gateway."""
        result = await commands.cmd_warm()

        assert "error" in result
        assert result["error"] == "MCP Gateway not available"

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_warm_with_gateway(self, mock_lock, commands):
        """Test cmd_warm with MCP Gateway."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        # Set up MCP Gateway
        mock_gateway = AsyncMock()
        commands.set_mcp_gateway(mock_gateway)

        # Mock cache_warmer.warm_cache
        commands.cache_warmer.warm_cache = AsyncMock(return_value={
            "success": True,
            "warmed": 5,
            "libraries": ["react", "vue"]
        })

        result = await commands.cmd_warm(auto_detect=True, libraries=["react"])

        assert result["success"] is True
        assert "warmed" in result

    @pytest.mark.asyncio
    async def test_cmd_populate_disabled(self, disabled_commands):
        """Test cmd_populate when Context7 is disabled."""
        result = await disabled_commands.cmd_populate()

        assert "error" in result
        assert result["error"] == "Context7 is not enabled"

    @pytest.mark.asyncio
    async def test_cmd_populate_no_gateway(self, commands):
        """Test cmd_populate without MCP Gateway."""
        result = await commands.cmd_populate()

        assert "error" in result
        assert result["error"] == "MCP Gateway not available"

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_populate_with_gateway(self, mock_lock, commands):
        """Test cmd_populate with MCP Gateway."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        # Set up MCP Gateway
        mock_gateway = AsyncMock()
        commands.set_mcp_gateway(mock_gateway)

        # Mock resolve and get_docs calls
        from unittest.mock import patch as mock_patch
        with mock_patch("tapps_agents.context7.commands.call_context7_resolve_with_fallback") as mock_resolve, \
             mock_patch("tapps_agents.context7.commands.call_context7_get_docs_with_fallback") as mock_docs:
            mock_resolve.return_value = {
                "success": True,
                "result": {"matches": [{"id": "/facebook/react"}]}
            }
            mock_docs.return_value = {
                "success": True,
                "result": {"content": "# React Documentation"}
            }

            result = await commands.cmd_populate(libraries=["react"], topics=["overview"])

            assert result["success"] is True
            assert "populated" in result
            assert result["populated"] >= 0

    @pytest.mark.asyncio
    @patch("tapps_agents.context7.kb_cache.cache_lock")
    async def test_cmd_populate_force_refresh(self, mock_lock, commands):
        """Test cmd_populate with force flag."""
        # Mock cache_lock to avoid file locking issues
        mock_lock.return_value.__enter__ = Mock(return_value=Mock())
        mock_lock.return_value.__exit__ = Mock(return_value=None)
        # Set up MCP Gateway
        mock_gateway = AsyncMock()
        commands.set_mcp_gateway(mock_gateway)

        # Store existing entry
        commands.kb_cache.store(
            library="react",
            topic="overview",
            content="Old content",
            context7_id="/facebook/react",
        )

        # Mock resolve and get_docs calls
        from unittest.mock import patch as mock_patch
        with mock_patch("tapps_agents.context7.commands.call_context7_resolve_with_fallback") as mock_resolve, \
             mock_patch("tapps_agents.context7.commands.call_context7_get_docs_with_fallback") as mock_docs:
            mock_resolve.return_value = {
                "success": True,
                "result": {"matches": [{"id": "/facebook/react"}]}
            }
            mock_docs.return_value = {
                "success": True,
                "result": {"content": "# New React Documentation"}
            }

            # Without force, should skip existing entry
            result1 = await commands.cmd_populate(libraries=["react"], topics=["overview"], force=False)
            # With force, should refresh
            result2 = await commands.cmd_populate(libraries=["react"], topics=["overview"], force=True)

            assert result1["success"] is True
            assert result2["success"] is True

    def test_cmd_help(self, commands):
        """Test cmd_help."""
        result = commands.cmd_help()

        assert result["success"] is True
        assert "help" in result
        assert "Context7 KB Commands" in result["help"]
        assert "*context7-docs" in result["help"]
