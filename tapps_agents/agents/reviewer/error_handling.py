"""
Centralized Error Handling Utilities for Reviewer Agent

Provides reusable error handling patterns to reduce code duplication.
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorHandler:
    """Centralized error handling utilities."""
    
    @staticmethod
    async def with_fallback(
        operation: Callable[[], Any],
        fallback_value: T,
        error_message: str,
        log_level: str = "debug"
    ) -> T:
        """
        Execute async operation with fallback on error.
        
        Args:
            operation: Async or sync callable to execute
            fallback_value: Value to return on error
            error_message: Error message prefix for logging
            log_level: Logging level ("debug", "info", "warning", "error")
        
        Returns:
            Operation result or fallback_value on error
        """
        try:
            if asyncio.iscoroutinefunction(operation):
                return await operation()
            else:
                return operation()
        except Exception as e:
            logger_func = getattr(logger, log_level, logger.debug)
            logger_func(f"{error_message}: {e}")
            return fallback_value
    
    @staticmethod
    def silence_errors(
        operation: Callable[[], Any],
        error_message: str,
        log_level: str = "debug"
    ) -> Any | None:
        """
        Execute sync operation, return None on error.
        
        Args:
            operation: Sync callable to execute
            error_message: Error message prefix for logging
            log_level: Logging level ("debug", "info", "warning", "error")
        
        Returns:
            Operation result or None on error
        """
        try:
            return operation()
        except Exception as e:
            logger_func = getattr(logger, log_level, logger.debug)
            logger_func(f"{error_message}: {e}")
            return None
    
    @staticmethod
    async def with_timeout(
        operation: Callable[[], Any],
        timeout: float,
        timeout_message: str,
        log_level: str = "warning"
    ) -> Any | None:
        """
        Execute async operation with timeout.
        
        Args:
            operation: Async callable to execute
            timeout: Timeout in seconds
            timeout_message: Message to log on timeout
            log_level: Logging level for timeout ("debug", "info", "warning", "error")
        
        Returns:
            Operation result or None on timeout/error
        """
        try:
            return await asyncio.wait_for(operation(), timeout=timeout)
        except TimeoutError:
            logger_func = getattr(logger, log_level, logger.warning)
            logger_func(f"{timeout_message} (timeout: {timeout}s)")
            return None
        except Exception as e:
            logger.debug(f"{timeout_message}: {e}")
            return None
    
    @staticmethod
    async def gather_with_exceptions(
        *operations: Callable[[], Any],
        return_exceptions: bool = True
    ) -> list[Any]:
        """
        Execute multiple async operations in parallel, handling exceptions.
        
        Args:
            *operations: Async callables to execute in parallel
            return_exceptions: If True, return exceptions in results instead of raising
        
        Returns:
            List of results (exceptions if return_exceptions=True)
        """
        async def wrap(op: Callable[[], Any]) -> Any:
            """Wrap operation to handle exceptions."""
            try:
                return await op() if asyncio.iscoroutinefunction(op) else op()
            except Exception as e:
                if return_exceptions:
                    return e
                raise
        
        tasks = [wrap(op) for op in operations]
        return await asyncio.gather(*tasks, return_exceptions=return_exceptions)
