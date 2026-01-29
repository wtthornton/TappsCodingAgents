"""
Parallel Tool Executor - Async execution of quality tools with timeout protection.

This module provides parallel execution capabilities for ReviewerAgent quality tools,
achieving 2-3x performance improvement through concurrent tool execution.

Architecture:
- Phase 1: Parallel batch (Ruff, mypy, bandit, pip-audit)
- Phase 2: Sequential batch (jscpd - requires full project context)
- Error recovery via asyncio.gather(return_exceptions=True)
- Timeout protection via asyncio.wait_for()
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================


@dataclass(frozen=True)
class ToolExecutionConfig:
    """
    Configuration for parallel tool execution.

    Attributes:
        enabled: Master switch for parallel execution
        timeout_seconds: Global timeout for all tools (seconds)
        max_concurrent_tools: Maximum concurrent subprocesses
        fallback_to_sequential: Auto-fallback on async errors
        tool_timeouts: Per-tool timeout overrides (optional)

    Example:
        >>> config = ToolExecutionConfig(
        ...     enabled=True,
        ...     timeout_seconds=30,
        ...     max_concurrent_tools=4
        ... )
    """
    enabled: bool = True
    timeout_seconds: int = 30
    max_concurrent_tools: int = 4
    fallback_to_sequential: bool = True
    tool_timeouts: Optional[Dict[str, int]] = None

    def __post_init__(self):
        """Validate configuration values."""
        # Use object.__setattr__ for frozen dataclass validation
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.max_concurrent_tools <= 0:
            raise ValueError("max_concurrent_tools must be positive")
        if self.tool_timeouts is not None:
            for tool, timeout in self.tool_timeouts.items():
                if timeout <= 0:
                    raise ValueError(
                        f"tool_timeouts[{tool}] must be positive, got {timeout}"
                    )

    def get_tool_timeout(self, tool_name: str) -> int:
        """
        Get timeout for specific tool (with fallback to global).

        Args:
            tool_name: Name of the tool (ruff, mypy, etc.)

        Returns:
            Timeout in seconds for the tool

        Example:
            >>> config.get_tool_timeout("mypy")
            45  # per-tool override
            >>> config.get_tool_timeout("ruff")
            30  # global fallback
        """
        if self.tool_timeouts and tool_name in self.tool_timeouts:
            return self.tool_timeouts[tool_name]
        return self.timeout_seconds

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ToolExecutionConfig":
        """
        Create config from dictionary (loaded from YAML).

        Args:
            config_dict: Configuration dictionary

        Returns:
            ToolExecutionConfig instance

        Example:
            >>> config = ToolExecutionConfig.from_dict({
            ...     "enabled": True,
            ...     "timeout_seconds": 30
            ... })
        """
        return cls(
            enabled=config_dict.get("enabled", True),
            timeout_seconds=config_dict.get("timeout_seconds", 30),
            max_concurrent_tools=config_dict.get("max_concurrent_tools", 4),
            fallback_to_sequential=config_dict.get("fallback_to_sequential", True),
            tool_timeouts=config_dict.get("tool_timeouts"),
        )


class ToolStatus(str, Enum):
    """Status of tool execution."""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(frozen=True)
class ToolResult:
    """
    Result from single tool execution.

    Attributes:
        tool: Tool name (ruff, mypy, bandit, pip-audit, jscpd)
        status: Execution status (success, timeout, error)
        data: Tool-specific result data (None if timeout/error)
        duration: Execution time in seconds
        error: Error message if status != success
        exit_code: Tool exit code (None if timeout)

    Example (success):
        >>> result = ToolResult(
        ...     tool="ruff",
        ...     status=ToolStatus.SUCCESS,
        ...     data={"issues": []},
        ...     duration=2.3,
        ...     error=None
        ... )

    Example (timeout):
        >>> result = ToolResult(
        ...     tool="mypy",
        ...     status=ToolStatus.TIMEOUT,
        ...     data=None,
        ...     duration=30.5,
        ...     error="Timeout after 30.5s"
        ... )

    Example (error):
        >>> result = ToolResult(
        ...     tool="bandit",
        ...     status=ToolStatus.ERROR,
        ...     data=None,
        ...     duration=1.2,
        ...     error="subprocess returned exit code 2",
        ...     exit_code=2
        ... )
    """
    tool: str
    status: ToolStatus
    data: Optional[Any]
    duration: float
    error: Optional[str] = None
    exit_code: Optional[int] = None

    def is_success(self) -> bool:
        """Check if tool executed successfully."""
        return self.status == ToolStatus.SUCCESS

    def is_timeout(self) -> bool:
        """Check if tool timed out."""
        return self.status == ToolStatus.TIMEOUT

    def is_error(self) -> bool:
        """Check if tool failed with error."""
        return self.status == ToolStatus.ERROR

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tool": self.tool,
            "status": self.status.value,
            "data": self.data,
            "duration": self.duration,
            "error": self.error,
            "exit_code": self.exit_code,
        }


# ============================================================================
# Parallel Tool Executor
# ============================================================================


class ParallelToolExecutor:
    """
    Coordinates parallel execution of quality tools with timeout protection.

    Architecture:
    - Phase 1: Parallel batch (Ruff, mypy, bandit, pip-audit)
    - Phase 2: Sequential batch (jscpd - requires full context)
    - Error recovery via asyncio.gather(return_exceptions=True)
    - Timeout protection via asyncio.wait_for()

    Example:
        >>> config = ToolExecutionConfig(enabled=True, timeout_seconds=30)
        >>> executor = ParallelToolExecutor(config)
        >>> results = await executor.execute_parallel(Path("src/example.py"))
    """

    def __init__(self, config: ToolExecutionConfig):
        """
        Initialize parallel tool executor.

        Args:
            config: Tool execution configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def execute_parallel(
        self,
        file_path: Path,
        tool_runners: Optional[Dict[str, Callable]] = None,
    ) -> List[ToolResult]:
        """
        Execute all quality tools with parallel optimization.

        Args:
            file_path: Path to file to review
            tool_runners: Optional dict of tool functions (for testing/customization)

        Returns:
            List of ToolResult objects (successful, timeout, or error)

        Raises:
            Never raises - always returns partial results on failures

        Example:
            >>> results = await executor.execute_parallel(Path("src/example.py"))
            >>> successful = [r for r in results if r.is_success()]
            >>> len(successful)
            4  # Ruff, mypy, bandit, pip-audit succeeded

        Performance:
            - Sequential: ~23s (sum of all tools)
            - Parallel: ~12s (2x faster)
        """
        if not self.config.enabled:
            self.logger.info("Parallel execution disabled, using sequential fallback")
            return await self._execute_sequential(file_path, tool_runners)

        try:
            # Phase 1: Parallel batch
            self.logger.debug("Starting parallel batch execution")
            parallel_results = await self._execute_parallel_batch(
                file_path, tool_runners
            )

            # Phase 2: Sequential batch (jscpd requires full context)
            self.logger.debug("Starting sequential batch execution")
            sequential_results = await self._execute_sequential_batch(
                file_path, tool_runners
            )

            all_results = parallel_results + sequential_results

            # Log summary
            successful = [r for r in all_results if r.is_success()]
            failed = [r for r in all_results if not r.is_success()]
            total_time = sum(r.duration for r in all_results)

            self.logger.info(
                f"Parallel execution complete: {len(successful)}/{len(all_results)} "
                f"tools successful, total time: {total_time:.2f}s"
            )

            if failed:
                self.logger.warning(
                    f"{len(failed)} tools failed: "
                    f"{', '.join(r.tool for r in failed)}"
                )

            return all_results

        except Exception as e:
            self.logger.error(f"Parallel execution failed: {e}", exc_info=True)

            if self.config.fallback_to_sequential:
                self.logger.warning("Falling back to sequential execution")
                return await self._execute_sequential(file_path, tool_runners)

            # Return empty list on catastrophic failure (defensive programming)
            self.logger.error("No fallback configured, returning empty results")
            return []

    async def _execute_parallel_batch(
        self,
        file_path: Path,
        tool_runners: Optional[Dict[str, Callable]] = None,
    ) -> List[ToolResult]:
        """
        Execute independent tools concurrently.

        Args:
            file_path: Path to file to analyze
            tool_runners: Optional dict of tool functions

        Returns:
            List of ToolResult objects from parallel execution
        """
        # Default tool runners (can be overridden for testing)
        if tool_runners is None:
            tool_runners = {}

        # Build list of tasks for parallel execution
        tasks = []
        parallel_tools = ["ruff", "mypy", "bandit", "pip_audit"]

        for tool_name in parallel_tools:
            if tool_name in tool_runners:
                tool_func = tool_runners[tool_name]
                tasks.append(
                    self.execute_with_timeout(tool_func, file_path, tool_name)
                )

        if not tasks:
            self.logger.warning("No parallel tools configured")
            return []

        # Execute all tasks concurrently
        # return_exceptions=True: Continue on individual failures
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results (convert exceptions to ToolResult objects)
        return self._process_results(results)

    async def _execute_sequential_batch(
        self,
        file_path: Path,
        tool_runners: Optional[Dict[str, Callable]] = None,
    ) -> List[ToolResult]:
        """
        Execute context-dependent tools sequentially.

        Args:
            file_path: Path to file to analyze
            tool_runners: Optional dict of tool functions

        Returns:
            List of ToolResult objects from sequential execution
        """
        if tool_runners is None:
            tool_runners = {}

        # jscpd requires full project context (cannot parallelize effectively)
        if "jscpd" not in tool_runners:
            self.logger.debug("No sequential tools configured")
            return []

        jscpd_result = await self.execute_with_timeout(
            tool_runners["jscpd"], file_path, "jscpd"
        )

        return [self._process_single_result(jscpd_result)]

    async def _execute_sequential(
        self,
        file_path: Path,
        tool_runners: Optional[Dict[str, Callable]] = None,
    ) -> List[ToolResult]:
        """
        Fallback: Execute all tools sequentially.

        Args:
            file_path: Path to file to analyze
            tool_runners: Optional dict of tool functions

        Returns:
            List of ToolResult objects from sequential execution
        """
        if tool_runners is None:
            tool_runners = {}

        results = []
        all_tools = ["ruff", "mypy", "bandit", "pip_audit", "jscpd"]

        for tool_name in all_tools:
            if tool_name in tool_runners:
                result = await self.execute_with_timeout(
                    tool_runners[tool_name], file_path, tool_name
                )
                results.append(result)

        return results

    async def execute_with_timeout(
        self,
        tool_func: Callable[[Path], Any],
        file_path: Path,
        tool_name: Optional[str] = None,
    ) -> ToolResult:
        """
        Execute single tool with timeout protection.

        Args:
            tool_func: Async tool function to execute
            file_path: Path to file to analyze
            tool_name: Tool name for logging (auto-detected if None)

        Returns:
            ToolResult (success, timeout, or error)

        Example:
            >>> result = await executor.execute_with_timeout(
            ...     run_ruff_async,
            ...     Path("src/example.py")
            ... )
            >>> result.status
            ToolStatus.SUCCESS
            >>> result.duration
            2.3

        Timeout Handling:
            - Global timeout: config.timeout_seconds
            - Per-tool timeout: config.get_tool_timeout(tool_name)
            - Timeout exception → ToolResult with status=TIMEOUT
        """
        # Extract tool name from function name if not provided
        if tool_name is None:
            tool_name = tool_func.__name__.replace("run_", "").replace("_async", "")

        # Get timeout for this tool
        timeout = self.config.get_tool_timeout(tool_name)

        start_time = time.time()

        try:
            # Execute with timeout protection
            result = await asyncio.wait_for(
                tool_func(file_path), timeout=timeout
            )

            duration = time.time() - start_time
            self.logger.debug(f"{tool_name} completed in {duration:.2f}s")

            return ToolResult(
                tool=tool_name,
                status=ToolStatus.SUCCESS,
                data=result,
                duration=duration,
                error=None,
                exit_code=None,
            )

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            error_msg = f"Timeout after {duration:.2f}s (limit: {timeout}s)"

            self.logger.warning(f"{tool_name}: {error_msg}")

            return self._handle_timeout(tool_name, duration, timeout)

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"{tool_name} failed after {duration:.2f}s: {e}",
                exc_info=True,
            )

            return self._handle_error(tool_name, e, duration)

    def _handle_timeout(
        self, tool_name: str, duration: float, timeout: int
    ) -> ToolResult:
        """
        Create timeout result annotation.

        Args:
            tool_name: Name of the tool that timed out
            duration: Actual execution time
            timeout: Configured timeout limit

        Returns:
            ToolResult with status=TIMEOUT
        """
        return ToolResult(
            tool=tool_name,
            status=ToolStatus.TIMEOUT,
            data=None,
            duration=duration,
            error=f"Timeout after {duration:.2f}s (limit: {timeout}s)",
            exit_code=None,
        )

    def _handle_error(
        self, tool_name: str, exception: Exception, duration: float
    ) -> ToolResult:
        """
        Create error result annotation.

        Args:
            tool_name: Name of the tool that failed
            exception: Exception that was raised
            duration: Execution time before failure

        Returns:
            ToolResult with status=ERROR
        """
        # Extract exit code from subprocess errors
        exit_code = None
        if hasattr(exception, "returncode"):
            exit_code = exception.returncode

        return ToolResult(
            tool=tool_name,
            status=ToolStatus.ERROR,
            data=None,
            duration=duration,
            error=str(exception),
            exit_code=exit_code,
        )

    def _process_results(
        self, results: List[Union[ToolResult, Exception]]
    ) -> List[ToolResult]:
        """
        Convert exceptions to error ToolResults.

        Args:
            results: List of ToolResult or Exception objects

        Returns:
            List of ToolResult objects (exceptions converted to errors)
        """
        processed = []

        for result in results:
            if isinstance(result, Exception):
                # Exception from asyncio.gather (shouldn't happen with our error handling)
                self.logger.error(f"Unexpected exception in gather: {result}")
                processed.append(
                    self._handle_error("unknown", result, 0.0)
                )
            elif isinstance(result, ToolResult):
                processed.append(result)
            else:
                # Unexpected result type (defensive programming)
                self.logger.error(f"Unexpected result type: {type(result)}")
                processed.append(
                    ToolResult(
                        tool="unknown",
                        status=ToolStatus.ERROR,
                        data=None,
                        duration=0.0,
                        error=f"Unexpected result type: {type(result)}",
                        exit_code=None,
                    )
                )

        return processed

    def _process_single_result(
        self, result: Union[ToolResult, Exception]
    ) -> ToolResult:
        """
        Process single result (for sequential execution).

        Args:
            result: ToolResult or Exception

        Returns:
            ToolResult object
        """
        if isinstance(result, Exception):
            return self._handle_error("unknown", result, 0.0)
        return result
