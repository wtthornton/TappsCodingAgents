"""
Comprehensive tests for parallel_executor module.

Tests cover:
- ToolExecutionConfig: validation, from_dict, get_tool_timeout
- ToolStatus: enum values
- ToolResult: creation, helper methods, to_dict
- ParallelToolExecutor: parallel/sequential execution, timeout handling, error recovery
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

import pytest

from tapps_agents.agents.reviewer.tools.parallel_executor import (
    ParallelToolExecutor,
    ToolExecutionConfig,
    ToolResult,
    ToolStatus,
)

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def default_config():
    """Create default ToolExecutionConfig for testing."""
    return ToolExecutionConfig(
        enabled=True,
        timeout_seconds=30,
        max_concurrent_tools=4,
        fallback_to_sequential=True,
    )


@pytest.fixture
def custom_config():
    """Create ToolExecutionConfig with custom tool timeouts."""
    return ToolExecutionConfig(
        enabled=True,
        timeout_seconds=30,
        max_concurrent_tools=4,
        fallback_to_sequential=True,
        tool_timeouts={"mypy": 45, "bandit": 15},
    )


@pytest.fixture
def disabled_config():
    """Create ToolExecutionConfig with parallel execution disabled."""
    return ToolExecutionConfig(
        enabled=False,
        timeout_seconds=30,
        max_concurrent_tools=4,
        fallback_to_sequential=True,
    )


@pytest.fixture
def executor(default_config):
    """Create ParallelToolExecutor for testing."""
    return ParallelToolExecutor(default_config)


@pytest.fixture
def test_file_path():
    """Create test file path."""
    return Path("src/example.py")


# ============================================================================
# ToolExecutionConfig Tests
# ============================================================================


class TestToolExecutionConfig:
    """Test ToolExecutionConfig dataclass."""

    def test_default_values(self):
        """Test ToolExecutionConfig default values."""
        config = ToolExecutionConfig()

        assert config.enabled is True
        assert config.timeout_seconds == 30
        assert config.max_concurrent_tools == 4
        assert config.fallback_to_sequential is True
        assert config.tool_timeouts is None

    def test_custom_values(self):
        """Test ToolExecutionConfig with custom values."""
        config = ToolExecutionConfig(
            enabled=False,
            timeout_seconds=60,
            max_concurrent_tools=8,
            fallback_to_sequential=False,
            tool_timeouts={"mypy": 90},
        )

        assert config.enabled is False
        assert config.timeout_seconds == 60
        assert config.max_concurrent_tools == 8
        assert config.fallback_to_sequential is False
        assert config.tool_timeouts == {"mypy": 90}

    def test_validation_negative_timeout(self):
        """Test validation fails with negative timeout."""
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            ToolExecutionConfig(timeout_seconds=-1)

    def test_validation_zero_timeout(self):
        """Test validation fails with zero timeout."""
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            ToolExecutionConfig(timeout_seconds=0)

    def test_validation_negative_max_concurrent(self):
        """Test validation fails with negative max_concurrent_tools."""
        with pytest.raises(ValueError, match="max_concurrent_tools must be positive"):
            ToolExecutionConfig(max_concurrent_tools=-1)

    def test_validation_zero_max_concurrent(self):
        """Test validation fails with zero max_concurrent_tools."""
        with pytest.raises(ValueError, match="max_concurrent_tools must be positive"):
            ToolExecutionConfig(max_concurrent_tools=0)

    def test_validation_negative_tool_timeout(self):
        """Test validation fails with negative tool timeout."""
        with pytest.raises(ValueError, match="tool_timeouts\\[mypy\\] must be positive"):
            ToolExecutionConfig(tool_timeouts={"mypy": -1})

    def test_validation_zero_tool_timeout(self):
        """Test validation fails with zero tool timeout."""
        with pytest.raises(ValueError, match="tool_timeouts\\[mypy\\] must be positive"):
            ToolExecutionConfig(tool_timeouts={"mypy": 0})

    def test_get_tool_timeout_with_override(self, custom_config):
        """Test get_tool_timeout returns per-tool override."""
        assert custom_config.get_tool_timeout("mypy") == 45
        assert custom_config.get_tool_timeout("bandit") == 15

    def test_get_tool_timeout_fallback_to_global(self, custom_config):
        """Test get_tool_timeout falls back to global timeout."""
        assert custom_config.get_tool_timeout("ruff") == 30
        assert custom_config.get_tool_timeout("jscpd") == 30

    def test_get_tool_timeout_no_overrides(self, default_config):
        """Test get_tool_timeout with no tool_timeouts configured."""
        assert default_config.get_tool_timeout("mypy") == 30
        assert default_config.get_tool_timeout("ruff") == 30

    def test_from_dict_with_all_fields(self):
        """Test from_dict with all fields specified."""
        config_dict = {
            "enabled": False,
            "timeout_seconds": 60,
            "max_concurrent_tools": 8,
            "fallback_to_sequential": False,
            "tool_timeouts": {"mypy": 90},
        }

        config = ToolExecutionConfig.from_dict(config_dict)

        assert config.enabled is False
        assert config.timeout_seconds == 60
        assert config.max_concurrent_tools == 8
        assert config.fallback_to_sequential is False
        assert config.tool_timeouts == {"mypy": 90}

    def test_from_dict_with_defaults(self):
        """Test from_dict uses defaults for missing fields."""
        config_dict = {}
        config = ToolExecutionConfig.from_dict(config_dict)

        assert config.enabled is True
        assert config.timeout_seconds == 30
        assert config.max_concurrent_tools == 4
        assert config.fallback_to_sequential is True
        assert config.tool_timeouts is None

    def test_from_dict_partial_fields(self):
        """Test from_dict with some fields specified."""
        config_dict = {
            "enabled": False,
            "timeout_seconds": 60,
        }

        config = ToolExecutionConfig.from_dict(config_dict)

        assert config.enabled is False
        assert config.timeout_seconds == 60
        assert config.max_concurrent_tools == 4  # default
        assert config.fallback_to_sequential is True  # default

    def test_frozen_dataclass(self):
        """Test ToolExecutionConfig is immutable (frozen)."""
        config = ToolExecutionConfig()

        with pytest.raises(Exception):  # FrozenInstanceError
            config.timeout_seconds = 60


# ============================================================================
# ToolStatus Tests
# ============================================================================


class TestToolStatus:
    """Test ToolStatus enum."""

    def test_enum_values(self):
        """Test ToolStatus enum values."""
        assert ToolStatus.SUCCESS.value == "success"
        assert ToolStatus.TIMEOUT.value == "timeout"
        assert ToolStatus.ERROR.value == "error"

    def test_enum_comparison(self):
        """Test ToolStatus enum comparison."""
        assert ToolStatus.SUCCESS == ToolStatus.SUCCESS
        assert ToolStatus.SUCCESS != ToolStatus.TIMEOUT
        assert ToolStatus.SUCCESS != ToolStatus.ERROR

    def test_string_enum(self):
        """Test ToolStatus inherits from str."""
        assert isinstance(ToolStatus.SUCCESS, str)
        assert ToolStatus.SUCCESS.value == "success"
        assert ToolStatus.SUCCESS == "success"  # Can compare directly with string


# ============================================================================
# ToolResult Tests
# ============================================================================


class TestToolResult:
    """Test ToolResult dataclass."""

    def test_success_result(self):
        """Test ToolResult with success status."""
        result = ToolResult(
            tool="ruff",
            status=ToolStatus.SUCCESS,
            data={"issues": []},
            duration=2.3,
            error=None,
            exit_code=None,
        )

        assert result.tool == "ruff"
        assert result.status == ToolStatus.SUCCESS
        assert result.data == {"issues": []}
        assert result.duration == 2.3
        assert result.error is None
        assert result.exit_code is None

    def test_timeout_result(self):
        """Test ToolResult with timeout status."""
        result = ToolResult(
            tool="mypy",
            status=ToolStatus.TIMEOUT,
            data=None,
            duration=30.5,
            error="Timeout after 30.5s",
        )

        assert result.tool == "mypy"
        assert result.status == ToolStatus.TIMEOUT
        assert result.data is None
        assert result.duration == 30.5
        assert result.error == "Timeout after 30.5s"
        assert result.exit_code is None

    def test_error_result(self):
        """Test ToolResult with error status."""
        result = ToolResult(
            tool="bandit",
            status=ToolStatus.ERROR,
            data=None,
            duration=1.2,
            error="subprocess returned exit code 2",
            exit_code=2,
        )

        assert result.tool == "bandit"
        assert result.status == ToolStatus.ERROR
        assert result.data is None
        assert result.duration == 1.2
        assert result.error == "subprocess returned exit code 2"
        assert result.exit_code == 2

    def test_is_success(self):
        """Test is_success helper method."""
        success_result = ToolResult(
            tool="ruff",
            status=ToolStatus.SUCCESS,
            data={},
            duration=1.0,
        )
        timeout_result = ToolResult(
            tool="mypy",
            status=ToolStatus.TIMEOUT,
            data=None,
            duration=30.0,
        )

        assert success_result.is_success() is True
        assert timeout_result.is_success() is False

    def test_is_timeout(self):
        """Test is_timeout helper method."""
        timeout_result = ToolResult(
            tool="mypy",
            status=ToolStatus.TIMEOUT,
            data=None,
            duration=30.0,
        )
        success_result = ToolResult(
            tool="ruff",
            status=ToolStatus.SUCCESS,
            data={},
            duration=1.0,
        )

        assert timeout_result.is_timeout() is True
        assert success_result.is_timeout() is False

    def test_is_error(self):
        """Test is_error helper method."""
        error_result = ToolResult(
            tool="bandit",
            status=ToolStatus.ERROR,
            data=None,
            duration=1.0,
            error="Failed",
        )
        success_result = ToolResult(
            tool="ruff",
            status=ToolStatus.SUCCESS,
            data={},
            duration=1.0,
        )

        assert error_result.is_error() is True
        assert success_result.is_error() is False

    def test_to_dict(self):
        """Test to_dict serialization."""
        result = ToolResult(
            tool="ruff",
            status=ToolStatus.SUCCESS,
            data={"issues": []},
            duration=2.3,
            error=None,
            exit_code=None,
        )

        result_dict = result.to_dict()

        assert result_dict == {
            "tool": "ruff",
            "status": "success",
            "data": {"issues": []},
            "duration": 2.3,
            "error": None,
            "exit_code": None,
        }

    def test_frozen_dataclass(self):
        """Test ToolResult is immutable (frozen)."""
        result = ToolResult(
            tool="ruff",
            status=ToolStatus.SUCCESS,
            data={},
            duration=1.0,
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            result.duration = 2.0


# ============================================================================
# ParallelToolExecutor Tests
# ============================================================================


class TestParallelToolExecutor:
    """Test ParallelToolExecutor class."""

    def test_init(self, default_config):
        """Test ParallelToolExecutor initialization."""
        executor = ParallelToolExecutor(default_config)

        assert executor.config == default_config
        assert isinstance(executor.logger, logging.Logger)

    @pytest.mark.asyncio
    async def test_execute_with_timeout_success(self, executor, test_file_path):
        """Test execute_with_timeout with successful execution."""
        # Create mock async tool function
        async def mock_tool(path: Path) -> dict[str, Any]:
            await asyncio.sleep(0.01)
            return {"result": "success"}

        result = await executor.execute_with_timeout(
            mock_tool, test_file_path, "test_tool"
        )

        assert result.tool == "test_tool"
        assert result.status == ToolStatus.SUCCESS
        assert result.data == {"result": "success"}
        assert result.duration > 0
        assert result.error is None
        assert result.exit_code is None

    @pytest.mark.asyncio
    async def test_execute_with_timeout_timeout(self, executor, test_file_path):
        """Test execute_with_timeout with timeout."""
        # Create mock async tool that sleeps longer than timeout
        async def slow_tool(path: Path) -> dict[str, Any]:
            await asyncio.sleep(100)  # Much longer than 30s timeout
            return {"result": "success"}

        # Use short timeout for testing
        executor.config = ToolExecutionConfig(timeout_seconds=1)

        result = await executor.execute_with_timeout(
            slow_tool, test_file_path, "slow_tool"
        )

        assert result.tool == "slow_tool"
        assert result.status == ToolStatus.TIMEOUT
        assert result.data is None
        assert result.duration >= 1.0
        assert "Timeout after" in result.error
        assert result.exit_code is None

    @pytest.mark.asyncio
    async def test_execute_with_timeout_error(self, executor, test_file_path):
        """Test execute_with_timeout with exception."""
        # Create mock async tool that raises exception
        async def failing_tool(path: Path) -> dict[str, Any]:
            raise ValueError("Tool failed")

        result = await executor.execute_with_timeout(
            failing_tool, test_file_path, "failing_tool"
        )

        assert result.tool == "failing_tool"
        assert result.status == ToolStatus.ERROR
        assert result.data is None
        assert result.duration >= 0
        assert "Tool failed" in result.error
        assert result.exit_code is None

    @pytest.mark.asyncio
    async def test_execute_with_timeout_subprocess_error(self, executor, test_file_path):
        """Test execute_with_timeout with subprocess error (has returncode)."""
        # Create mock exception with returncode
        class SubprocessError(Exception):
            def __init__(self, returncode: int):
                self.returncode = returncode
                super().__init__(f"Process exited with code {returncode}")

        async def subprocess_failing_tool(path: Path) -> dict[str, Any]:
            raise SubprocessError(2)

        result = await executor.execute_with_timeout(
            subprocess_failing_tool, test_file_path, "subprocess_tool"
        )

        assert result.tool == "subprocess_tool"
        assert result.status == ToolStatus.ERROR
        assert result.data is None
        assert result.exit_code == 2

    @pytest.mark.asyncio
    async def test_execute_with_timeout_auto_name_detection(self, executor, test_file_path):
        """Test execute_with_timeout auto-detects tool name from function."""
        async def run_ruff_async(path: Path) -> dict[str, Any]:
            return {"result": "success"}

        result = await executor.execute_with_timeout(
            run_ruff_async, test_file_path
        )

        assert result.tool == "ruff"

    @pytest.mark.asyncio
    async def test_execute_with_timeout_per_tool_timeout(self, test_file_path):
        """Test execute_with_timeout uses per-tool timeout."""
        config = ToolExecutionConfig(
            timeout_seconds=30,
            tool_timeouts={"mypy": 1},  # Short timeout for mypy
        )
        executor = ParallelToolExecutor(config)

        async def slow_tool(path: Path) -> dict[str, Any]:
            await asyncio.sleep(100)
            return {"result": "success"}

        result = await executor.execute_with_timeout(
            slow_tool, test_file_path, "mypy"
        )

        assert result.status == ToolStatus.TIMEOUT
        assert result.duration >= 1.0
        assert result.duration < 30.0  # Used mypy timeout (1s), not global (30s)

    @pytest.mark.asyncio
    async def test_execute_parallel_batch(self, executor, test_file_path):
        """Test _execute_parallel_batch with multiple tools."""
        # Create mock tools
        async def ruff_tool(path: Path) -> dict[str, Any]:
            await asyncio.sleep(0.01)
            return {"tool": "ruff"}

        async def mypy_tool(path: Path) -> dict[str, Any]:
            await asyncio.sleep(0.01)
            return {"tool": "mypy"}

        tool_runners = {
            "ruff": ruff_tool,
            "mypy": mypy_tool,
        }

        results = await executor._execute_parallel_batch(test_file_path, tool_runners)

        assert len(results) == 2
        assert all(r.status == ToolStatus.SUCCESS for r in results)
        assert {r.tool for r in results} == {"ruff", "mypy"}

    @pytest.mark.asyncio
    async def test_execute_parallel_batch_no_tools(self, executor, test_file_path):
        """Test _execute_parallel_batch with no tools configured."""
        results = await executor._execute_parallel_batch(test_file_path, {})

        assert results == []

    @pytest.mark.asyncio
    async def test_execute_sequential_batch(self, executor, test_file_path):
        """Test _execute_sequential_batch with jscpd."""
        async def jscpd_tool(path: Path) -> dict[str, Any]:
            await asyncio.sleep(0.01)
            return {"tool": "jscpd"}

        tool_runners = {"jscpd": jscpd_tool}

        results = await executor._execute_sequential_batch(test_file_path, tool_runners)

        assert len(results) == 1
        assert results[0].status == ToolStatus.SUCCESS
        assert results[0].tool == "jscpd"

    @pytest.mark.asyncio
    async def test_execute_sequential_batch_no_jscpd(self, executor, test_file_path):
        """Test _execute_sequential_batch with no jscpd configured."""
        results = await executor._execute_sequential_batch(test_file_path, {})

        assert results == []

    @pytest.mark.asyncio
    async def test_execute_sequential(self, executor, test_file_path):
        """Test _execute_sequential fallback."""
        async def mock_tool(path: Path) -> dict[str, Any]:
            await asyncio.sleep(0.01)
            return {"result": "success"}

        tool_runners = {
            "ruff": mock_tool,
            "mypy": mock_tool,
        }

        results = await executor._execute_sequential(test_file_path, tool_runners)

        assert len(results) == 2
        assert all(r.status == ToolStatus.SUCCESS for r in results)

    @pytest.mark.asyncio
    async def test_execute_parallel_success(self, executor, test_file_path):
        """Test execute_parallel with all tools succeeding."""
        async def mock_tool(path: Path) -> dict[str, Any]:
            await asyncio.sleep(0.01)
            return {"result": "success"}

        tool_runners = {
            "ruff": mock_tool,
            "mypy": mock_tool,
            "bandit": mock_tool,
            "pip_audit": mock_tool,
            "jscpd": mock_tool,
        }

        results = await executor.execute_parallel(test_file_path, tool_runners)

        assert len(results) == 5
        assert all(r.status == ToolStatus.SUCCESS for r in results)
        assert {r.tool for r in results} == {"ruff", "mypy", "bandit", "pip_audit", "jscpd"}

    @pytest.mark.asyncio
    async def test_execute_parallel_partial_failure(self, executor, test_file_path):
        """Test execute_parallel with some tools failing."""
        async def success_tool(path: Path) -> dict[str, Any]:
            return {"result": "success"}

        async def failing_tool(path: Path) -> dict[str, Any]:
            raise ValueError("Tool failed")

        tool_runners = {
            "ruff": success_tool,
            "mypy": failing_tool,
            "bandit": success_tool,
            "pip_audit": failing_tool,
            "jscpd": success_tool,
        }

        results = await executor.execute_parallel(test_file_path, tool_runners)

        assert len(results) == 5
        successful = [r for r in results if r.is_success()]
        failed = [r for r in results if r.is_error()]
        assert len(successful) == 3
        assert len(failed) == 2

    @pytest.mark.asyncio
    async def test_execute_parallel_disabled(self, disabled_config, test_file_path):
        """Test execute_parallel with parallel execution disabled."""
        executor = ParallelToolExecutor(disabled_config)

        async def mock_tool(path: Path) -> dict[str, Any]:
            return {"result": "success"}

        tool_runners = {"ruff": mock_tool}

        results = await executor.execute_parallel(test_file_path, tool_runners)

        assert len(results) == 1
        assert results[0].status == ToolStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_execute_parallel_catastrophic_failure_with_fallback(
        self, executor, test_file_path
    ):
        """Test execute_parallel catastrophic failure with fallback enabled."""
        # Mock _execute_parallel_batch to raise exception
        async def failing_batch(path, runners):
            raise RuntimeError("Catastrophic failure")

        executor._execute_parallel_batch = failing_batch

        async def mock_tool(path: Path) -> dict[str, Any]:
            return {"result": "success"}

        tool_runners = {"ruff": mock_tool}

        results = await executor.execute_parallel(test_file_path, tool_runners)

        # Should fall back to sequential execution
        assert len(results) == 1
        assert results[0].status == ToolStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_execute_parallel_catastrophic_failure_no_fallback(
        self, test_file_path
    ):
        """Test execute_parallel catastrophic failure with fallback disabled."""
        config = ToolExecutionConfig(fallback_to_sequential=False)
        executor = ParallelToolExecutor(config)

        # Mock _execute_parallel_batch to raise exception
        async def failing_batch(path, runners):
            raise RuntimeError("Catastrophic failure")

        executor._execute_parallel_batch = failing_batch

        results = await executor.execute_parallel(test_file_path, {})

        # Should return empty list
        assert results == []

    @pytest.mark.asyncio
    async def test_process_results_with_exceptions(self, executor):
        """Test _process_results converts exceptions to ToolResult."""
        results = [
            ToolResult(
                tool="ruff",
                status=ToolStatus.SUCCESS,
                data={},
                duration=1.0,
            ),
            ValueError("Tool failed"),
            ToolResult(
                tool="bandit",
                status=ToolStatus.ERROR,
                data=None,
                duration=2.0,
                error="Failed",
            ),
        ]

        processed = executor._process_results(results)

        assert len(processed) == 3
        assert processed[0].status == ToolStatus.SUCCESS
        assert processed[1].status == ToolStatus.ERROR
        assert "Tool failed" in processed[1].error
        assert processed[2].status == ToolStatus.ERROR

    @pytest.mark.asyncio
    async def test_process_results_unexpected_type(self, executor):
        """Test _process_results handles unexpected result types."""
        results = [
            ToolResult(
                tool="ruff",
                status=ToolStatus.SUCCESS,
                data={},
                duration=1.0,
            ),
            "unexpected_string",  # Unexpected type
        ]

        processed = executor._process_results(results)

        assert len(processed) == 2
        assert processed[0].status == ToolStatus.SUCCESS
        assert processed[1].status == ToolStatus.ERROR
        assert "Unexpected result type" in processed[1].error

    @pytest.mark.asyncio
    async def test_process_single_result_with_exception(self, executor):
        """Test _process_single_result converts exception to ToolResult."""
        exception = ValueError("Tool failed")
        result = executor._process_single_result(exception)

        assert result.status == ToolStatus.ERROR
        assert "Tool failed" in result.error

    @pytest.mark.asyncio
    async def test_process_single_result_with_tool_result(self, executor):
        """Test _process_single_result passes through ToolResult."""
        tool_result = ToolResult(
            tool="ruff",
            status=ToolStatus.SUCCESS,
            data={},
            duration=1.0,
        )

        result = executor._process_single_result(tool_result)

        assert result == tool_result

    def test_handle_timeout(self, executor):
        """Test _handle_timeout creates correct ToolResult."""
        result = executor._handle_timeout("mypy", 30.5, 30)

        assert result.tool == "mypy"
        assert result.status == ToolStatus.TIMEOUT
        assert result.data is None
        assert result.duration == 30.5
        assert "Timeout after 30.5" in result.error
        assert "limit: 30s" in result.error
        assert result.exit_code is None

    def test_handle_error(self, executor):
        """Test _handle_error creates correct ToolResult."""
        exception = ValueError("Tool failed")
        result = executor._handle_error("bandit", exception, 1.2)

        assert result.tool == "bandit"
        assert result.status == ToolStatus.ERROR
        assert result.data is None
        assert result.duration == 1.2
        assert "Tool failed" in result.error
        assert result.exit_code is None

    def test_handle_error_with_returncode(self, executor):
        """Test _handle_error extracts returncode from exception."""
        class SubprocessError(Exception):
            def __init__(self, returncode: int):
                self.returncode = returncode
                super().__init__(f"Process exited with code {returncode}")

        exception = SubprocessError(2)
        result = executor._handle_error("bandit", exception, 1.2)

        assert result.exit_code == 2


# ============================================================================
# Integration Tests
# ============================================================================


class TestParallelExecutorIntegration:
    """Integration tests for ParallelToolExecutor."""

    @pytest.mark.asyncio
    async def test_parallel_execution_faster_than_sequential(self):
        """Test parallel execution is faster than sequential."""
        config = ToolExecutionConfig(timeout_seconds=30)
        executor = ParallelToolExecutor(config)

        # Create mock tools that take 0.1s each
        async def slow_tool(path: Path) -> dict[str, Any]:
            await asyncio.sleep(0.1)
            return {"result": "success"}

        tool_runners = {
            "ruff": slow_tool,
            "mypy": slow_tool,
            "bandit": slow_tool,
            "pip_audit": slow_tool,
        }

        # Measure parallel execution time
        import time
        start = time.time()
        results = await executor._execute_parallel_batch(Path("test.py"), tool_runners)
        parallel_duration = time.time() - start

        # Parallel should take ~0.1s (all run concurrently)
        # Sequential would take ~0.4s (sum of all tools)
        assert len(results) == 4
        assert all(r.is_success() for r in results)
        assert parallel_duration < 0.3  # Should be closer to 0.1s than 0.4s

    @pytest.mark.asyncio
    async def test_timeout_recovery(self):
        """Test executor recovers from individual tool timeouts."""
        config = ToolExecutionConfig(
            timeout_seconds=1,
            tool_timeouts={"mypy": 1},
        )
        executor = ParallelToolExecutor(config)

        async def fast_tool(path: Path) -> dict[str, Any]:
            await asyncio.sleep(0.01)
            return {"result": "success"}

        async def slow_tool(path: Path) -> dict[str, Any]:
            await asyncio.sleep(100)  # Will timeout
            return {"result": "success"}

        tool_runners = {
            "ruff": fast_tool,
            "mypy": slow_tool,  # Will timeout
            "bandit": fast_tool,
        }

        results = await executor._execute_parallel_batch(Path("test.py"), tool_runners)

        assert len(results) == 3
        successful = [r for r in results if r.is_success()]
        timeouts = [r for r in results if r.is_timeout()]
        assert len(successful) == 2  # ruff, bandit
        assert len(timeouts) == 1  # mypy

    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test executor recovers from individual tool errors."""
        config = ToolExecutionConfig(timeout_seconds=30)
        executor = ParallelToolExecutor(config)

        async def success_tool(path: Path) -> dict[str, Any]:
            return {"result": "success"}

        async def error_tool(path: Path) -> dict[str, Any]:
            raise ValueError("Tool error")

        tool_runners = {
            "ruff": success_tool,
            "mypy": error_tool,
            "bandit": success_tool,
        }

        results = await executor._execute_parallel_batch(Path("test.py"), tool_runners)

        assert len(results) == 3
        successful = [r for r in results if r.is_success()]
        errors = [r for r in results if r.is_error()]
        assert len(successful) == 2  # ruff, bandit
        assert len(errors) == 1  # mypy
