"""
Reliability controls for E2E scenario tests.

Provides:
- Timeout controls (scenario, step, workflow levels)
- Retry policy for transient failures
- Cost guardrails (token budgets, call limits, parallelism)
- Partial progress capture on failure
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, TypeVar

# Configure logging
logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class TimeoutConfig:
    """Configuration for timeout controls."""

    scenario_timeout_seconds: float = 1800.0  # 30 minutes default
    step_timeout_seconds: float = 300.0  # 5 minutes default
    workflow_timeout_seconds: float = 1800.0  # 30 minutes default


@dataclass
class RetryConfig:
    """Configuration for retry policy."""

    max_attempts: int = 3
    initial_backoff_seconds: float = 2.0
    max_backoff_seconds: float = 60.0
    exponential_base: float = 2.0
    retryable_exceptions: tuple = (
        ConnectionError,
        TimeoutError,
        asyncio.TimeoutError,
        OSError,  # Network errors
    )

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """
        Determine if an exception should be retried.

        Args:
            attempt: Current attempt number (1-indexed)
            exception: Exception that occurred

        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.max_attempts:
            return False

        # Check if exception is retryable
        if isinstance(exception, self.retryable_exceptions):
            return True

        # Check for transient error patterns in message
        error_msg = str(exception).lower()
        transient_patterns = [
            "timeout",
            "connection",
            "network",
            "rate limit",
            "temporary",
            "unavailable",
            "503",
            "502",
            "429",
        ]
        return any(pattern in error_msg for pattern in transient_patterns)

    def get_backoff_seconds(self, attempt: int) -> float:
        """
        Calculate backoff delay for retry.

        Args:
            attempt: Current attempt number (1-indexed)

        Returns:
            Backoff delay in seconds
        """
        backoff = self.initial_backoff_seconds * (self.exponential_base ** (attempt - 1))
        return min(backoff, self.max_backoff_seconds)


@dataclass
class CostConfig:
    """Configuration for cost guardrails."""

    max_tokens_per_scenario: Optional[int] = None  # None = no limit
    max_calls_per_scenario: Optional[int] = None  # None = no limit
    max_parallel_scenarios: int = 2
    track_costs: bool = True

    def __post_init__(self):
        """Initialize from environment variables if present."""
        if self.max_tokens_per_scenario is None:
            env_tokens = os.getenv("E2E_MAX_TOKENS_PER_SCENARIO")
            if env_tokens:
                self.max_tokens_per_scenario = int(env_tokens)

        if self.max_calls_per_scenario is None:
            env_calls = os.getenv("E2E_MAX_CALLS_PER_SCENARIO")
            if env_calls:
                self.max_calls_per_scenario = int(env_calls)

        env_parallel = os.getenv("E2E_MAX_PARALLEL_SCENARIOS")
        if env_parallel:
            self.max_parallel_scenarios = int(env_parallel)


@dataclass
class CostTracker:
    """Tracks costs for scenario tests."""

    tokens_used: int = 0
    calls_made: int = 0
    scenarios_run: int = 0

    def record_tokens(self, tokens: int) -> None:
        """Record token usage."""
        self.tokens_used += tokens
        logger.debug(f"Cost tracker: {tokens} tokens used (total: {self.tokens_used})")

    def record_call(self) -> None:
        """Record API call."""
        self.calls_made += 1
        logger.debug(f"Cost tracker: API call made (total: {self.calls_made})")

    def record_scenario(self) -> None:
        """Record scenario run."""
        self.scenarios_run += 1

    def check_budget(self, config: CostConfig) -> tuple[bool, Optional[str]]:
        """
        Check if cost budget is exceeded.

        Args:
            config: Cost configuration

        Returns:
            Tuple of (within_budget, error_message)
        """
        if config.max_tokens_per_scenario and self.tokens_used > config.max_tokens_per_scenario:
            return (
                False,
                f"Token budget exceeded: {self.tokens_used} > {config.max_tokens_per_scenario}",
            )

        if config.max_calls_per_scenario and self.calls_made > config.max_calls_per_scenario:
            return (
                False,
                f"Call budget exceeded: {self.calls_made} > {config.max_calls_per_scenario}",
            )

        return (True, None)

    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary."""
        return {
            "tokens_used": self.tokens_used,
            "calls_made": self.calls_made,
            "scenarios_run": self.scenarios_run,
        }


class ReliabilityController:
    """Controller for reliability controls in scenario tests."""

    def __init__(
        self,
        timeout_config: Optional[TimeoutConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        cost_config: Optional[CostConfig] = None,
    ):
        """
        Initialize reliability controller.

        Args:
            timeout_config: Timeout configuration (defaults to TimeoutConfig())
            retry_config: Retry configuration (defaults to RetryConfig())
            cost_config: Cost configuration (defaults to CostConfig())
        """
        self.timeout_config = timeout_config or TimeoutConfig()
        self.retry_config = retry_config or RetryConfig()
        self.cost_config = cost_config or CostConfig()
        self.cost_tracker = CostTracker()

    async def execute_with_timeout(
        self,
        coro: Callable[[], Any],
        timeout_seconds: Optional[float] = None,
        operation_name: str = "operation",
    ) -> Any:
        """
        Execute a coroutine with timeout.

        Args:
            coro: Coroutine to execute
            timeout_seconds: Timeout in seconds (uses step timeout if not provided)
            operation_name: Name of operation for logging

        Returns:
            Result of coroutine

        Raises:
            asyncio.TimeoutError: If operation times out
        """
        timeout = timeout_seconds or self.timeout_config.step_timeout_seconds

        try:
            result = await asyncio.wait_for(coro(), timeout=timeout)
            return result
        except asyncio.TimeoutError:
            logger.error(f"{operation_name} timed out after {timeout} seconds")
            raise

    async def execute_with_retry(
        self,
        coro: Callable[[], Any],
        operation_name: str = "operation",
        capture_progress: Optional[Callable[[], None]] = None,
    ) -> Any:
        """
        Execute a coroutine with retry policy.

        Args:
            coro: Coroutine to execute
            operation_name: Name of operation for logging
            capture_progress: Optional function to capture progress on failure

        Returns:
            Result of coroutine

        Raises:
            Exception: Last exception if all retries fail
        """
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.retry_config.max_attempts + 1):
            try:
                result = await coro()
                if attempt > 1:
                    logger.info(f"{operation_name} succeeded on attempt {attempt}")
                return result
            except Exception as e:
                last_exception = e

                # Capture progress on failure
                if capture_progress:
                    try:
                        capture_progress()
                    except Exception as capture_error:
                        logger.warning(f"Failed to capture progress: {capture_error}")

                # Check if should retry
                if not self.retry_config.should_retry(attempt, e):
                    logger.error(f"{operation_name} failed on attempt {attempt} (non-retryable): {e}")
                    break

                # Calculate backoff
                backoff = self.retry_config.get_backoff_seconds(attempt)
                logger.warning(
                    f"{operation_name} failed on attempt {attempt}: {e}. Retrying in {backoff}s..."
                )

                # Wait before retry
                await asyncio.sleep(backoff)

        # All retries exhausted
        logger.error(f"{operation_name} failed after {self.retry_config.max_attempts} attempts")
        raise last_exception

    def check_cost_budget(self) -> tuple[bool, Optional[str]]:
        """
        Check if cost budget is exceeded.

        Returns:
            Tuple of (within_budget, error_message)
        """
        return self.cost_tracker.check_budget(self.cost_config)

    def record_tokens(self, tokens: int) -> None:
        """Record token usage."""
        if self.cost_config.track_costs:
            self.cost_tracker.record_tokens(tokens)

    def record_call(self) -> None:
        """Record API call."""
        if self.cost_config.track_costs:
            self.cost_tracker.record_call()

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary."""
        return self.cost_tracker.get_summary()


# Global reliability controller instance (can be overridden in tests)
_default_controller: Optional[ReliabilityController] = None


def get_reliability_controller() -> ReliabilityController:
    """
    Get the default reliability controller.

    Returns:
        Default reliability controller instance
    """
    global _default_controller
    if _default_controller is None:
        _default_controller = ReliabilityController()
    return _default_controller


def set_reliability_controller(controller: ReliabilityController) -> None:
    """
    Set the default reliability controller.

    Args:
        controller: Reliability controller to use as default
    """
    global _default_controller
    _default_controller = controller

