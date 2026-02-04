"""
Centralized retry logic for connection failures and transient errors.

Provides decorators and utilities for automatic retry with exponential backoff,
specifically designed for LLM operations and Cursor Skills integration.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryableError(Exception):
    """Base exception for errors that should trigger retry logic."""
    pass


class ConnectionError(RetryableError):
    """Connection-related errors that should be retried."""
    pass


def retry_on_connection_error(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying operations on connection errors with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        max_delay: Maximum delay in seconds between retries (default: 60.0)
    
    Returns:
        Decorated function with retry logic
    
    Example:
        @retry_on_connection_error(max_retries=3)
        async def call_llm(prompt: str) -> str:
            # LLM call that may fail
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (ConnectionError, TimeoutError, OSError) as e:
                    last_exception = e
                    
                    if attempt == max_retries - 1:
                        # Last attempt failed, raise the exception
                        logger.error(
                            f"Operation failed after {max_retries} attempts: {e}",
                            exc_info=True
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(initial_delay * (backoff_factor ** attempt), max_delay)
                    
                    logger.warning(
                        f"Connection error (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay:.1f}s: {e}"
                    )
                    await asyncio.sleep(delay)
                except Exception as e:
                    # Non-retryable error, raise immediately
                    logger.error(f"Non-retryable error in {func.__name__}: {e}", exc_info=True)
                    raise
            
            # Should never reach here, but satisfy type checker
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Unexpected retry loop exit in {func.__name__}")
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError, OSError) as e:
                    last_exception = e
                    
                    if attempt == max_retries - 1:
                        # Last attempt failed, raise the exception
                        logger.error(
                            f"Operation failed after {max_retries} attempts: {e}",
                            exc_info=True
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(initial_delay * (backoff_factor ** attempt), max_delay)
                    
                    logger.warning(
                        f"Connection error (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay:.1f}s: {e}"
                    )
                    import time
                    time.sleep(delay)
                except Exception as e:
                    # Non-retryable error, raise immediately
                    logger.error(f"Non-retryable error in {func.__name__}: {e}", exc_info=True)
                    raise
            
            # Should never reach here, but satisfy type checker
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Unexpected retry loop exit in {func.__name__}")
        
        # Return appropriate wrapper based on whether function is async
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


async def retry_operation[T](
    operation: Callable[[], T],
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple[type[Exception], ...] = (ConnectionError, TimeoutError, OSError),
) -> T:
    """
    Retry an operation with exponential backoff.
    
    Args:
        operation: Async callable to retry
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for delay between retries
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        retryable_exceptions: Tuple of exception types that should trigger retry
    
    Returns:
        Result of the operation
    
    Raises:
        Last exception if all retries fail
    """
    last_exception: Exception | None = None
    
    for attempt in range(max_retries):
        try:
            if asyncio.iscoroutinefunction(operation):
                return await operation()
            else:
                return operation()
        except retryable_exceptions as e:
            last_exception = e
            
            if attempt == max_retries - 1:
                logger.error(
                    f"Operation failed after {max_retries} attempts: {e}",
                    exc_info=True
                )
                raise
            
            # Calculate delay with exponential backoff
            delay = min(initial_delay * (backoff_factor ** attempt), max_delay)
            
            logger.warning(
                f"Retryable error (attempt {attempt + 1}/{max_retries}), "
                f"retrying in {delay:.1f}s: {e}"
            )
            await asyncio.sleep(delay)
        except Exception as e:
            # Non-retryable error, raise immediately
            logger.error(f"Non-retryable error: {e}", exc_info=True)
            raise
    
    # Should never reach here
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected retry loop exit")
