"""Tests for Context7CacheManager module.

Module: Phase 2.1 - Context7 Cache Manager Tests
Target Coverage: ≥90%
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import yaml

from tapps_agents.core.context7.cache_manager import (
    Context7CacheManager,
    FetchResult,
    QueueStatus,
)

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


@pytest.fixture
def temp_project():
    """Create temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        tapps_dir = project_root / ".tapps-agents"
        tapps_dir.mkdir(parents=True, exist_ok=True)

        # Create config
        config_file = tapps_dir / "config.yaml"
        config_data = {
            "version": "3.5.39",
            "context7": {
                "enabled": True,
                "knowledge_base": {
                    "location": ".tapps-agents/kb/context7-cache",
                    "max_cache_size": "100MB"
                }
            }
        }
        config_file.write_text(yaml.dump(config_data))

        # Create cache directory
        cache_dir = project_root / ".tapps-agents" / "kb" / "context7-cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        yield project_root


@pytest.fixture
def mock_context7_commands():
    """Create mock Context7Commands."""
    mock = MagicMock()
    mock.enabled = True
    mock.kb_cache = MagicMock()
    mock.refresh_queue = MagicMock()
    mock.refresh_queue.size.return_value = 0
    mock.refresh_queue.tasks = []
    mock.refresh_queue.add_task = MagicMock()

    # Mock async methods
    mock.cmd_populate = AsyncMock(return_value={"success": True})

    return mock


@pytest.fixture
def mock_config():
    """Create mock ProjectConfig."""
    mock = MagicMock()
    mock.context7 = MagicMock()
    mock.context7.enabled = True
    mock.context7.knowledge_base = MagicMock()
    mock.context7.knowledge_base.location = ".tapps-agents/kb/context7-cache"
    mock.context7.knowledge_base.max_cache_size = "100MB"
    return mock


@pytest.fixture
def cache_manager(temp_project, mock_context7_commands, mock_config):
    """Create Context7CacheManager instance with mocked dependencies."""
    return Context7CacheManager(
        project_root=temp_project,
        config=mock_config,
        context7_commands=mock_context7_commands
    )


class TestFetchResult:
    """Test FetchResult dataclass."""

    def test_fetch_result_creation(self):
        """Test FetchResult dataclass creation."""
        result = FetchResult(
            library="pytest",
            success=True,
            duration_ms=150.5
        )
        assert result.library == "pytest"
        assert result.success is True
        assert result.error is None
        assert result.duration_ms == 150.5

    def test_fetch_result_with_error(self):
        """Test FetchResult with error."""
        result = FetchResult(
            library="nonexistent",
            success=False,
            error="Library not found",
            duration_ms=50.0
        )
        assert result.library == "nonexistent"
        assert result.success is False
        assert result.error == "Library not found"


class TestCacheManagerInitialization:
    """Test Context7CacheManager initialization."""

    def test_init_with_enabled_context7(self, temp_project, mock_context7_commands, mock_config):
        """Test initialization with Context7 enabled."""
        manager = Context7CacheManager(
            project_root=temp_project,
            config=mock_config,
            context7_commands=mock_context7_commands
        )
        assert manager.enabled is True
        assert manager.kb_cache is not None
        assert manager.refresh_queue is not None

    def test_init_with_disabled_context7(self, temp_project, mock_config):
        """Test initialization with Context7 disabled."""
        mock_disabled = MagicMock()
        mock_disabled.enabled = False

        manager = Context7CacheManager(
            project_root=temp_project,
            config=mock_config,
            context7_commands=mock_disabled
        )
        assert manager.enabled is False
        assert manager.kb_cache is None
        assert manager.refresh_queue is None

    def test_init_default_project_root(self, mock_context7_commands, mock_config):
        """Test initialization with default project root."""
        manager = Context7CacheManager(
            config=mock_config,
            context7_commands=mock_context7_commands
        )
        assert manager.project_root == Path.cwd()


class TestCheckLibraryCached:
    """Test check_library_cached method."""

    def test_check_library_cached_exists(self, cache_manager):
        """Test checking cached library that exists."""
        cache_manager.kb_cache.exists.return_value = True

        result = cache_manager.check_library_cached("pytest")

        assert result is True
        cache_manager.kb_cache.exists.assert_called_once_with("pytest", "overview")

    def test_check_library_cached_not_exists(self, cache_manager):
        """Test checking library that is not cached."""
        cache_manager.kb_cache.exists.return_value = False

        result = cache_manager.check_library_cached("nonexistent")

        assert result is False

    def test_check_library_cached_with_topic(self, cache_manager):
        """Test checking library with specific topic."""
        cache_manager.kb_cache.exists.return_value = True

        result = cache_manager.check_library_cached("pytest", topic="fixtures")

        assert result is True
        cache_manager.kb_cache.exists.assert_called_once_with("pytest", "fixtures")

    def test_check_library_cached_disabled(self, temp_project, mock_config):
        """Test checking library when Context7 is disabled."""
        mock_disabled = MagicMock()
        mock_disabled.enabled = False

        manager = Context7CacheManager(
            project_root=temp_project,
            config=mock_config,
            context7_commands=mock_disabled
        )

        result = manager.check_library_cached("pytest")
        assert result is False


class TestQueueLibraryFetch:
    """Test queue_library_fetch method."""

    def test_queue_library_default_priority(self, cache_manager):
        """Test queueing library with default priority."""
        cache_manager.queue_library_fetch("fastapi")

        cache_manager.refresh_queue.add_task.assert_called_once_with(
            library="fastapi",
            topic=None,
            priority=5,
            reason="auto-population"
        )

    def test_queue_library_high_priority(self, cache_manager):
        """Test queueing library with high priority."""
        cache_manager.queue_library_fetch("pytest", priority=10, reason="critical")

        cache_manager.refresh_queue.add_task.assert_called_once_with(
            library="pytest",
            topic=None,
            priority=10,
            reason="critical"
        )

    def test_queue_library_with_topic(self, cache_manager):
        """Test queueing library with specific topic."""
        cache_manager.queue_library_fetch("pytest", topic="fixtures", priority=7)

        cache_manager.refresh_queue.add_task.assert_called_once_with(
            library="pytest",
            topic="fixtures",
            priority=7,
            reason="auto-population"
        )

    def test_queue_library_disabled(self, temp_project, mock_config):
        """Test queueing library when Context7 is disabled."""
        mock_disabled = MagicMock()
        mock_disabled.enabled = False

        manager = Context7CacheManager(
            project_root=temp_project,
            config=mock_config,
            context7_commands=mock_disabled
        )

        # Should not raise error, just do nothing
        manager.queue_library_fetch("pytest")


class TestFetchLibrariesAsync:
    """Test fetch_libraries_async method."""

    @pytest.mark.asyncio
    async def test_fetch_single_library(self, cache_manager):
        """Test fetching a single library."""
        cache_manager.context7_commands.cmd_populate.return_value = {
            "success": True,
            "populated": 1
        }

        results = await cache_manager.fetch_libraries_async(libraries=["pytest"])

        assert results == {"pytest": True}
        cache_manager.context7_commands.cmd_populate.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_multiple_libraries(self, cache_manager):
        """Test fetching multiple libraries."""
        async def mock_populate(libraries, topics, force):
            return {"success": True, "populated": len(libraries)}

        cache_manager.context7_commands.cmd_populate = mock_populate

        results = await cache_manager.fetch_libraries_async(
            libraries=["pytest", "fastapi", "pydantic"]
        )

        assert len(results) == 3
        assert all(success for success in results.values())

    @pytest.mark.asyncio
    async def test_fetch_with_custom_topics(self, cache_manager):
        """Test fetching libraries with custom topics."""
        cache_manager.context7_commands.cmd_populate.return_value = {
            "success": True
        }

        results = await cache_manager.fetch_libraries_async(
            libraries=["pytest"],
            topics=["fixtures", "markers"]
        )

        assert results["pytest"] is True

    @pytest.mark.asyncio
    async def test_fetch_with_force_refresh(self, cache_manager):
        """Test fetching with force refresh."""
        cache_manager.context7_commands.cmd_populate.return_value = {
            "success": True
        }

        results = await cache_manager.fetch_libraries_async(
            libraries=["pytest"],
            force=True
        )

        assert results["pytest"] is True
        # Verify force=True was passed
        call_args = cache_manager.context7_commands.cmd_populate.call_args
        assert call_args.kwargs.get("force") is True

    @pytest.mark.asyncio
    async def test_fetch_error_handling(self, cache_manager):
        """Test error handling during fetch."""
        cache_manager.context7_commands.cmd_populate.return_value = {
            "success": False,
            "error": "Network error"
        }

        results = await cache_manager.fetch_libraries_async(libraries=["pytest"])

        assert results["pytest"] is False
        assert "pytest" in cache_manager._fetch_results
        assert cache_manager._fetch_results["pytest"].success is False
        assert cache_manager._fetch_results["pytest"].error == "Network error"

    @pytest.mark.asyncio
    async def test_fetch_disabled(self, temp_project, mock_config):
        """Test fetching when Context7 is disabled."""
        mock_disabled = MagicMock()
        mock_disabled.enabled = False

        manager = Context7CacheManager(
            project_root=temp_project,
            config=mock_config,
            context7_commands=mock_disabled
        )

        results = await manager.fetch_libraries_async(libraries=["pytest"])

        assert results == {"pytest": False}


class TestGetFetchQueueStatus:
    """Test get_fetch_queue_status method."""

    def test_get_status_empty_queue(self, cache_manager):
        """Test getting status with empty queue."""
        status = cache_manager.get_fetch_queue_status()

        assert status["enabled"] is True
        assert status["total_queued"] == 0
        assert status["pending_libraries"] == []
        assert "fetch_statistics" in status

    def test_get_status_with_pending_tasks(self, cache_manager):
        """Test getting status with pending tasks."""
        mock_task1 = MagicMock(library="pytest")
        mock_task2 = MagicMock(library="fastapi")
        cache_manager.refresh_queue.tasks = [mock_task1, mock_task2]
        cache_manager.refresh_queue.size.return_value = 2

        status = cache_manager.get_fetch_queue_status()

        assert status["total_queued"] == 2
        assert set(status["pending_libraries"]) == {"pytest", "fastapi"}

    def test_get_status_with_fetch_results(self, cache_manager):
        """Test getting status with fetch results."""
        # Add some fetch results
        cache_manager._fetch_results["pytest"] = FetchResult(
            library="pytest",
            success=True,
            duration_ms=150.0
        )
        cache_manager._fetch_results["fastapi"] = FetchResult(
            library="fastapi",
            success=False,
            error="Network error",
            duration_ms=50.0
        )

        status = cache_manager.get_fetch_queue_status()

        assert status["fetch_statistics"]["total_fetched"] == 2
        assert status["fetch_statistics"]["successful"] == 1
        assert status["fetch_statistics"]["failed"] == 1
        assert status["fetch_statistics"]["avg_fetch_time_ms"] == 100.0

    def test_get_status_disabled(self, temp_project, mock_config):
        """Test getting status when Context7 is disabled."""
        mock_disabled = MagicMock()
        mock_disabled.enabled = False

        manager = Context7CacheManager(
            project_root=temp_project,
            config=mock_config,
            context7_commands=mock_disabled
        )

        status = manager.get_fetch_queue_status()

        assert status["enabled"] is False
        assert status["total_queued"] == 0


class TestScanAndPopulateFromTechStack:
    """Test scan_and_populate_from_tech_stack method."""

    @pytest.mark.asyncio
    async def test_scan_tech_stack_success(self, cache_manager, temp_project):
        """Test scanning and populating from tech-stack.yaml."""
        # Create tech-stack.yaml
        tech_stack_file = temp_project / ".tapps-agents" / "tech-stack.yaml"
        tech_stack_data = {
            "languages": ["python"],
            "libraries": ["pytest", "pydantic"],
            "frameworks": ["fastapi"],
            "context7_priority": ["fastapi", "pytest"]
        }
        tech_stack_file.write_text(yaml.dump(tech_stack_data))

        # Mock check_library_cached to return False
        cache_manager.kb_cache.exists.return_value = False

        # Mock fetch_libraries_async
        async def mock_fetch(libraries, max_concurrent):
            return {lib: True for lib in libraries}

        cache_manager.fetch_libraries_async = mock_fetch

        result = await cache_manager.scan_and_populate_from_tech_stack()

        assert result["success"] is True
        assert result["total_libraries"] >= 3  # At least pytest, pydantic, fastapi

    @pytest.mark.asyncio
    async def test_scan_tech_stack_skip_cached(self, cache_manager, temp_project):
        """Test scanning with skip_cached=True."""
        # Create tech-stack.yaml
        tech_stack_file = temp_project / ".tapps-agents" / "tech-stack.yaml"
        tech_stack_data = {
            "libraries": ["pytest", "pydantic", "fastapi"]
        }
        tech_stack_file.write_text(yaml.dump(tech_stack_data))

        # Mock check_library_cached: pytest already cached
        def mock_exists(library, topic="overview"):
            return library == "pytest"

        cache_manager.kb_cache.exists = mock_exists

        # Mock fetch_libraries_async
        fetched_libs = []
        async def mock_fetch(libraries, max_concurrent):
            fetched_libs.extend(libraries)
            return {lib: True for lib in libraries}

        cache_manager.fetch_libraries_async = mock_fetch

        result = await cache_manager.scan_and_populate_from_tech_stack(skip_cached=True)

        assert result["success"] is True
        assert result["already_cached"] >= 1
        assert "pytest" not in fetched_libs  # Should skip cached

    @pytest.mark.asyncio
    async def test_scan_tech_stack_not_found(self, cache_manager, temp_project):
        """Test scanning when tech-stack.yaml doesn't exist."""
        result = await cache_manager.scan_and_populate_from_tech_stack()

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_scan_tech_stack_invalid_yaml(self, cache_manager, temp_project):
        """Test scanning with invalid YAML."""
        # Create invalid tech-stack.yaml
        tech_stack_file = temp_project / ".tapps-agents" / "tech-stack.yaml"
        tech_stack_file.write_text("invalid: yaml: syntax:")

        result = await cache_manager.scan_and_populate_from_tech_stack()

        assert result["success"] is False
        assert "Failed to load" in result["error"]

    @pytest.mark.asyncio
    async def test_scan_tech_stack_disabled(self, temp_project, mock_config):
        """Test scanning when Context7 is disabled."""
        mock_disabled = MagicMock()
        mock_disabled.enabled = False

        manager = Context7CacheManager(
            project_root=temp_project,
            config=mock_config,
            context7_commands=mock_disabled
        )

        result = await manager.scan_and_populate_from_tech_stack()

        assert result["success"] is False
        assert "not enabled" in result["error"]


class TestScanAndPopulateEdgeCases:
    """Test edge cases in scan_and_populate_from_tech_stack."""

    @pytest.mark.asyncio
    async def test_scan_empty_tech_stack(self, cache_manager, temp_project):
        """Test scanning empty tech-stack.yaml."""
        # Create empty tech-stack.yaml
        tech_stack_file = temp_project / ".tapps-agents" / "tech-stack.yaml"
        tech_stack_file.write_text("")

        # Mock fetch_libraries_async
        async def mock_fetch(libraries, max_concurrent):
            return {}

        cache_manager.fetch_libraries_async = mock_fetch

        result = await cache_manager.scan_and_populate_from_tech_stack()

        assert result["success"] is True
        assert result["total_libraries"] == 0
        assert result["fetched"] == 0

    @pytest.mark.asyncio
    async def test_scan_with_force_refresh(self, cache_manager, temp_project):
        """Test scanning with force refresh (skip_cached=False)."""
        # Create tech-stack.yaml
        tech_stack_file = temp_project / ".tapps-agents" / "tech-stack.yaml"
        tech_stack_data = {"libraries": ["pytest"]}
        tech_stack_file.write_text(yaml.dump(tech_stack_data))

        # Mock check_library_cached to return True
        cache_manager.kb_cache.exists.return_value = True

        # Mock fetch_libraries_async
        fetched_libs = []
        async def mock_fetch(libraries, max_concurrent):
            fetched_libs.extend(libraries)
            return {lib: True for lib in libraries}

        cache_manager.fetch_libraries_async = mock_fetch

        result = await cache_manager.scan_and_populate_from_tech_stack(skip_cached=False)

        assert result["success"] is True
        assert "pytest" in fetched_libs  # Should fetch even if cached


class TestQueueStatusEdgeCases:
    """Test edge cases in queue status."""

    def test_get_status_with_recent_results_limit(self, cache_manager):
        """Test that recent results are limited to 10."""
        # Add 15 fetch results
        for i in range(15):
            cache_manager._fetch_results[f"lib{i}"] = FetchResult(
                library=f"lib{i}",
                success=True,
                duration_ms=100.0
            )

        status = cache_manager.get_fetch_queue_status()

        # Should only return last 10 results
        assert len(status["recent_results"]) == 10


class TestCLIIntegration:
    """Test CLI entry point."""

    @pytest.mark.asyncio
    async def test_main_help(self):
        """Test CLI help command."""
        from tapps_agents.core.context7.cache_manager import main
        import sys

        old_argv = sys.argv
        try:
            sys.argv = ["cache_manager", "--help"]

            with pytest.raises(SystemExit) as exc:
                await main()

            assert exc.value.code == 0
        finally:
            sys.argv = old_argv

    @pytest.mark.asyncio
    @patch("tapps_agents.core.context7.cache_manager.Context7CacheManager")
    async def test_main_disabled_context7(self, mock_manager_class):
        """Test CLI when Context7 is disabled."""
        from tapps_agents.core.context7.cache_manager import main
        import sys

        # Mock manager to be disabled
        mock_manager = MagicMock()
        mock_manager.enabled = False
        mock_manager_class.return_value = mock_manager

        old_argv = sys.argv
        try:
            sys.argv = ["cache_manager", "--status"]
            await main()
            # Should not raise error, just print message
        finally:
            sys.argv = old_argv

    @pytest.mark.asyncio
    @patch("tapps_agents.core.context7.cache_manager.Context7CacheManager")
    async def test_main_status_command(self, mock_manager_class):
        """Test CLI status command."""
        from tapps_agents.core.context7.cache_manager import main
        import sys

        # Mock manager
        mock_manager = MagicMock()
        mock_manager.enabled = True
        mock_manager.get_fetch_queue_status.return_value = {
            "total_queued": 5,
            "pending_libraries": ["pytest", "fastapi"],
            "fetch_statistics": {
                "total_fetched": 10,
                "successful": 8,
                "failed": 2,
                "avg_fetch_time_ms": 150.0
            }
        }
        mock_manager_class.return_value = mock_manager

        old_argv = sys.argv
        try:
            sys.argv = ["cache_manager", "--status"]
            await main()
            mock_manager.get_fetch_queue_status.assert_called_once()
        finally:
            sys.argv = old_argv

    @pytest.mark.asyncio
    @patch("tapps_agents.core.context7.cache_manager.Context7CacheManager")
    async def test_main_scan_command(self, mock_manager_class):
        """Test CLI scan command."""
        from tapps_agents.core.context7.cache_manager import main
        import sys

        # Mock manager
        mock_manager = MagicMock()
        mock_manager.enabled = True
        mock_manager.scan_and_populate_from_tech_stack = AsyncMock(
            return_value={
                "success": True,
                "total_libraries": 10,
                "already_cached": 5,
                "fetched": 5,
                "successful_fetches": 4,
                "failed_fetches": 1
            }
        )
        mock_manager_class.return_value = mock_manager

        old_argv = sys.argv
        try:
            sys.argv = ["cache_manager", "--scan"]
            await main()
            mock_manager.scan_and_populate_from_tech_stack.assert_called_once()
        finally:
            sys.argv = old_argv

    @pytest.mark.asyncio
    @patch("tapps_agents.core.context7.cache_manager.Context7CacheManager")
    async def test_main_libraries_command(self, mock_manager_class):
        """Test CLI libraries command."""
        from tapps_agents.core.context7.cache_manager import main
        import sys

        # Mock manager
        mock_manager = MagicMock()
        mock_manager.enabled = True
        mock_manager.fetch_libraries_async = AsyncMock(
            return_value={"pytest": True, "fastapi": True}
        )
        mock_manager_class.return_value = mock_manager

        old_argv = sys.argv
        try:
            sys.argv = ["cache_manager", "--libraries", "pytest", "fastapi"]
            await main()
            mock_manager.fetch_libraries_async.assert_called_once()
        finally:
            sys.argv = old_argv

    @pytest.mark.asyncio
    @patch("tapps_agents.core.context7.cache_manager.Context7CacheManager")
    async def test_main_libraries_with_force(self, mock_manager_class):
        """Test CLI libraries command with --force flag."""
        from tapps_agents.core.context7.cache_manager import main
        import sys

        # Mock manager
        mock_manager = MagicMock()
        mock_manager.enabled = True
        mock_manager.fetch_libraries_async = AsyncMock(
            return_value={"pytest": True}
        )
        mock_manager_class.return_value = mock_manager

        old_argv = sys.argv
        try:
            sys.argv = ["cache_manager", "--libraries", "pytest", "--force"]
            await main()

            # Verify force=True was passed
            call_args = mock_manager.fetch_libraries_async.call_args
            assert call_args.kwargs.get("force") is True
        finally:
            sys.argv = old_argv
