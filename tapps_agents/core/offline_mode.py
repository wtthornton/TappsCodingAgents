"""
Offline Mode Handler - Prevents connection errors by using local-only fallbacks.

This module provides offline mode detection and local fallbacks to prevent
connection errors when network is unavailable or API endpoints are down.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class OfflineMode:
    """Manages offline mode detection and local fallbacks."""

    _offline_mode: bool | None = None
    _connection_failures: int = 0
    _max_failures_before_offline: int = 2

    @classmethod
    def is_offline(cls) -> bool:
        """
        Check if we should operate in offline mode.
        
        Returns True if:
        - TAPPS_AGENTS_OFFLINE env var is set
        - Multiple connection failures detected
        - Network connectivity check fails
        """
        if cls._offline_mode is not None:
            return cls._offline_mode

        # Check explicit offline mode
        if os.getenv("TAPPS_AGENTS_OFFLINE", "").lower() in ("1", "true", "yes"):
            cls._offline_mode = True
            logger.info("Offline mode enabled via TAPPS_AGENTS_OFFLINE environment variable")
            return True

        # Check if we've had too many connection failures
        if cls._connection_failures >= cls._max_failures_before_offline:
            cls._offline_mode = True
            logger.warning(
                f"Offline mode enabled due to {cls._connection_failures} connection failures"
            )
            return True

        return False

    @classmethod
    def record_connection_failure(cls) -> None:
        """Record a connection failure and potentially enable offline mode."""
        cls._connection_failures += 1
        logger.debug(f"Connection failure recorded (total: {cls._connection_failures})")
        
        if cls._connection_failures >= cls._max_failures_before_offline:
            cls._offline_mode = True
            logger.warning("Too many connection failures - enabling offline mode")

    @classmethod
    def record_connection_success(cls) -> None:
        """Record a successful connection and reset offline mode if needed."""
        if cls._connection_failures > 0:
            cls._connection_failures = 0
            if cls._offline_mode:
                logger.info("Connection restored - disabling offline mode")
                cls._offline_mode = False

    @classmethod
    def reset(cls) -> None:
        """Reset offline mode state (for testing)."""
        cls._offline_mode = None
        cls._connection_failures = 0

    @classmethod
    def with_offline_fallback(
        cls,
        network_operation: Callable[[], T],
        local_fallback: Callable[[], T],
        operation_name: str = "operation",
    ) -> T:
        """
        Execute a network operation with local fallback if offline.
        
        Args:
            network_operation: Function that requires network
            local_fallback: Function that works offline
            operation_name: Name of operation for logging
            
        Returns:
            Result from network_operation or local_fallback
        """
        if cls.is_offline():
            logger.debug(f"Offline mode: using local fallback for {operation_name}")
            return local_fallback()

        try:
            result = network_operation()
            cls.record_connection_success()
            return result
        except (ConnectionError, TimeoutError, OSError) as e:
            cls.record_connection_failure()
            logger.warning(
                f"Network operation '{operation_name}' failed: {e}. Using local fallback."
            )
            return local_fallback()
        except Exception as e:
            # Check if it's a connection-related error
            error_str = str(e).lower()
            if any(
                keyword in error_str
                for keyword in [
                    "connection",
                    "network",
                    "timeout",
                    "unreachable",
                    "refused",
                    "failed to connect",
                ]
            ):
                cls.record_connection_failure()
                logger.warning(
                    f"Connection error in '{operation_name}': {e}. Using local fallback."
                )
                return local_fallback()
            # Not a connection error - re-raise
            raise


def skip_if_offline[T](func: Callable[..., T]) -> Callable[..., T | None]:
    """
    Decorator that skips function execution if in offline mode.
    
    Returns None if offline, otherwise executes function normally.
    """
    def wrapper(*args: Any, **kwargs: Any) -> T | None:
        if OfflineMode.is_offline():
            logger.debug(f"Skipping {func.__name__} - offline mode enabled")
            return None
        return func(*args, **kwargs)
    
    return wrapper


def local_only[T](func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that marks a function as local-only (no network required).
    
    This is informational - the function will always execute.
    """
    func._local_only = True  # type: ignore[attr-defined]
    return func

