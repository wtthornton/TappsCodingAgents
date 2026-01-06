"""
Circuit Breaker Pattern for Context7 Operations.

Prevents cascading failures by "opening" the circuit when failures exceed a threshold.
2025 Architecture Pattern: Resilient distributed systems with fail-fast semantics.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests flow through
    OPEN = "open"  # Circuit tripped, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    failure_threshold: int = 3  # Failures before opening circuit
    success_threshold: int = 2  # Successes in half-open to close circuit
    timeout_seconds: float = 5.0  # Request timeout
    reset_timeout_seconds: float = 30.0  # Time before half-open from open
    name: str = "context7"


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0  # Requests rejected due to open circuit
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_failure_time: float | None = None
    last_state_change: float | None = None


class CircuitBreaker:
    """
    Circuit Breaker for resilient Context7 operations.

    States:
    - CLOSED: Normal operation, requests flow through
    - OPEN: Circuit tripped, requests fail fast (no actual call)
    - HALF_OPEN: Testing recovery, limited requests allowed

    Transitions:
    - CLOSED -> OPEN: When failures >= failure_threshold
    - OPEN -> HALF_OPEN: After reset_timeout_seconds
    - HALF_OPEN -> CLOSED: When successes >= success_threshold
    - HALF_OPEN -> OPEN: On any failure
    """

    def __init__(self, config: CircuitBreakerConfig | None = None):
        self.config = config or CircuitBreakerConfig()
        self._stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._stats.state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._stats.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing fast)."""
        return self._stats.state == CircuitState.OPEN

    @property
    def stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        return self._stats

    async def _check_state_transition(self) -> None:
        """Check if state should transition (OPEN -> HALF_OPEN)."""
        if self._stats.state == CircuitState.OPEN:
            if self._stats.last_failure_time is not None:
                elapsed = time.time() - self._stats.last_failure_time
                if elapsed >= self.config.reset_timeout_seconds:
                    self._stats.state = CircuitState.HALF_OPEN
                    self._stats.consecutive_failures = 0
                    self._stats.consecutive_successes = 0
                    self._stats.last_state_change = time.time()
                    logger.info(
                        f"Circuit breaker [{self.config.name}] transitioned to HALF_OPEN "
                        f"after {elapsed:.1f}s"
                    )

    async def _record_success(self) -> None:
        """Record successful request."""
        self._stats.total_requests += 1
        self._stats.successful_requests += 1
        self._stats.consecutive_successes += 1
        self._stats.consecutive_failures = 0

        if self._stats.state == CircuitState.HALF_OPEN:
            if self._stats.consecutive_successes >= self.config.success_threshold:
                self._stats.state = CircuitState.CLOSED
                self._stats.last_state_change = time.time()
                logger.info(
                    f"Circuit breaker [{self.config.name}] CLOSED after "
                    f"{self._stats.consecutive_successes} consecutive successes"
                )

    async def _record_failure(self) -> None:
        """Record failed request."""
        self._stats.total_requests += 1
        self._stats.failed_requests += 1
        self._stats.consecutive_failures += 1
        self._stats.consecutive_successes = 0
        self._stats.last_failure_time = time.time()

        if self._stats.state == CircuitState.HALF_OPEN:
            # Any failure in half-open reopens the circuit
            self._stats.state = CircuitState.OPEN
            self._stats.last_state_change = time.time()
            logger.warning(
                f"Circuit breaker [{self.config.name}] OPENED from HALF_OPEN due to failure"
            )
        elif self._stats.state == CircuitState.CLOSED:
            if self._stats.consecutive_failures >= self.config.failure_threshold:
                self._stats.state = CircuitState.OPEN
                self._stats.last_state_change = time.time()
                logger.warning(
                    f"Circuit breaker [{self.config.name}] OPENED after "
                    f"{self._stats.consecutive_failures} consecutive failures"
                )

    async def _record_rejection(self) -> None:
        """Record rejected request (circuit open)."""
        self._stats.rejected_requests += 1

    async def call(
        self,
        func: Callable[..., Any],
        *args: Any,
        fallback: Any = None,
        **kwargs: Any,
    ) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            fallback: Value to return if circuit is open or call fails
            **kwargs: Keyword arguments for func

        Returns:
            Function result or fallback value

        Raises:
            CircuitBreakerOpen: If circuit is open and no fallback provided
        """
        async with self._lock:
            await self._check_state_transition()

            if self._stats.state == CircuitState.OPEN:
                await self._record_rejection()
                logger.debug(
                    f"Circuit breaker [{self.config.name}] OPEN - fast failing"
                )
                if fallback is not None:
                    return fallback
                raise CircuitBreakerOpen(
                    f"Circuit breaker [{self.config.name}] is OPEN"
                )

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout_seconds,
            )
            async with self._lock:
                await self._record_success()
            return result

        except asyncio.TimeoutError:
            async with self._lock:
                await self._record_failure()
            logger.debug(
                f"Circuit breaker [{self.config.name}] timeout after "
                f"{self.config.timeout_seconds}s"
            )
            if fallback is not None:
                return fallback
            raise

        except Exception as e:
            async with self._lock:
                await self._record_failure()
            logger.debug(
                f"Circuit breaker [{self.config.name}] call failed: {e}"
            )
            if fallback is not None:
                return fallback
            raise

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self._stats = CircuitBreakerStats()
        logger.info(f"Circuit breaker [{self.config.name}] reset to CLOSED")


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""

    pass


class ParallelExecutor:
    """
    Parallel executor with circuit breaker and bounded concurrency.

    2025 Pattern: Bounded parallelism with fail-fast semantics.
    """

    def __init__(
        self,
        max_concurrency: int = 5,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        """
        Initialize parallel executor.

        Args:
            max_concurrency: Maximum concurrent operations
            circuit_breaker: Optional shared circuit breaker
        """
        self.max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

    async def execute_all(
        self,
        items: list[Any],
        func: Callable[[Any], Any],
        fallback: Any = None,
    ) -> list[Any]:
        """
        Execute function for all items in parallel with circuit breaker.

        Args:
            items: List of items to process
            func: Async function to apply to each item
            fallback: Fallback value for failed items

        Returns:
            List of results (in same order as items)
        """

        async def execute_one(item: Any) -> Any:
            async with self._semaphore:
                return await self.circuit_breaker.call(
                    func, item, fallback=fallback
                )

        tasks = [execute_one(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Replace exceptions with fallback
        return [
            fallback if isinstance(r, Exception) else r
            for r in results
        ]

    @property
    def stats(self) -> dict[str, Any]:
        """Get executor statistics."""
        return {
            "max_concurrency": self.max_concurrency,
            "circuit_breaker": {
                "state": self.circuit_breaker.state.value,
                "stats": {
                    "total_requests": self.circuit_breaker.stats.total_requests,
                    "successful_requests": self.circuit_breaker.stats.successful_requests,
                    "failed_requests": self.circuit_breaker.stats.failed_requests,
                    "rejected_requests": self.circuit_breaker.stats.rejected_requests,
                },
            },
        }


# Global circuit breaker instance for Context7 operations
_context7_circuit_breaker: CircuitBreaker | None = None


def get_context7_circuit_breaker() -> CircuitBreaker:
    """Get the global Context7 circuit breaker."""
    global _context7_circuit_breaker
    if _context7_circuit_breaker is None:
        _context7_circuit_breaker = CircuitBreaker(
            CircuitBreakerConfig(
                name="context7",
                failure_threshold=3,
                success_threshold=2,
                timeout_seconds=5.0,
                reset_timeout_seconds=30.0,
            )
        )
    return _context7_circuit_breaker


def get_parallel_executor(
    max_concurrency: int = 5,
    circuit_breaker: CircuitBreaker | None = None,
) -> ParallelExecutor:
    """
    Get a parallel executor for Context7 operations.

    Args:
        max_concurrency: Maximum concurrent operations (default: 5)
        circuit_breaker: Optional circuit breaker (uses global if not provided)

    Returns:
        ParallelExecutor instance
    """
    if circuit_breaker is None:
        circuit_breaker = get_context7_circuit_breaker()
    return ParallelExecutor(
        max_concurrency=max_concurrency,
        circuit_breaker=circuit_breaker,
    )
