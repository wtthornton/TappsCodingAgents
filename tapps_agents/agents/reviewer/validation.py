"""
Input Validation Utilities for Reviewer Agent

Provides validation decorators and utilities for validating inputs
to reviewer agent methods.
"""

import functools
import inspect
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def validate_file_path(file_path: Any) -> bool:
    """
    Validate that file_path is a valid Path and exists.
    
    Args:
        file_path: The file path to validate
    
    Returns:
        True if valid, False otherwise
    """
    if file_path is None:
        return False
    if not isinstance(file_path, Path):
        return False
    return file_path.exists() and file_path.is_file()


def validate_code_string(code: Any) -> bool:
    """
    Validate that code is a non-empty string.
    
    Args:
        code: The code string to validate
    
    Returns:
        True if valid, False otherwise
    """
    return code is not None and isinstance(code, str) and len(code.strip()) > 0


def validate_boolean(value: Any) -> bool:
    """
    Validate that value is a boolean.
    
    Args:
        value: The value to validate
    
    Returns:
        True if valid, False otherwise
    """
    return isinstance(value, bool)


def validate_positive_int(value: Any) -> bool:
    """
    Validate that value is a positive integer.
    
    Args:
        value: The value to validate
    
    Returns:
        True if valid, False otherwise
    """
    return isinstance(value, int) and value > 0


def validate_non_negative_float(value: Any) -> bool:
    """
    Validate that value is a non-negative float.
    
    Args:
        value: The value to validate
    
    Returns:
        True if valid, False otherwise
    """
    return isinstance(value, (int, float)) and value >= 0.0


def validate_inputs(**validators: Callable[[Any], bool]):
    """
    Decorator for input validation.
    
    Usage:
        @validate_inputs(
            file_path=validate_file_path,
            include_scoring=validate_boolean,
        )
        async def review_file(self, file_path: Path, include_scoring: bool = True):
            ...
    
    Args:
        **validators: Dictionary mapping parameter names to validator functions
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Extract parameter values
            sig = inspect.signature(func)
            bound = sig.bind(self, *args, **kwargs)
            bound.apply_defaults()
            
            # Validate each parameter
            for param_name, validator in validators.items():
                if param_name not in bound.arguments:
                    continue  # Parameter not provided, skip
                
                value = bound.arguments[param_name]
                if not validator(value):
                    raise ValueError(
                        f"Invalid {param_name}: {value} (expected {validator.__name__})"
                    )
            
            return await func(self, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # Extract parameter values
            sig = inspect.signature(func)
            bound = sig.bind(self, *args, **kwargs)
            bound.apply_defaults()
            
            # Validate each parameter
            for param_name, validator in validators.items():
                if param_name not in bound.arguments:
                    continue  # Parameter not provided, skip
                
                value = bound.arguments[param_name]
                if not validator(value):
                    raise ValueError(
                        f"Invalid {param_name}: {value} (expected {validator.__name__})"
                    )
            
            return func(self, *args, **kwargs)
        
        # Return appropriate wrapper based on whether function is async
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def validate_code_input(code: str, method_name: str = "method") -> None:
    """
    Validate code string input and raise if invalid.
    
    Args:
        code: The code string to validate
        method_name: Name of the method calling this (for error messages)
    
    Raises:
        ValueError: If code is invalid
    """
    if not validate_code_string(code):
        raise ValueError(
            f"{method_name}: code must be a non-empty string, got {type(code).__name__}"
        )


def validate_file_path_input(file_path: Any, must_exist: bool = True, method_name: str = "method") -> Path:
    """
    Validate file path input and convert to Path if needed.
    
    Args:
        file_path: The file path to validate
        must_exist: Whether the file must exist
        method_name: Name of the method calling this (for error messages)
    
    Returns:
        Path object
    
    Raises:
        ValueError: If file path is invalid
        FileNotFoundError: If file doesn't exist and must_exist is True
    """
    if file_path is None:
        raise ValueError(f"{method_name}: file_path cannot be None")
    
    if not isinstance(file_path, Path):
        try:
            file_path = Path(file_path)
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"{method_name}: file_path must be a Path or path-like string: {e}"
            ) from e
    
    if must_exist and not file_path.exists():
        raise FileNotFoundError(
            f"{method_name}: file_path does not exist: {file_path}"
        )
    
    if must_exist and not file_path.is_file():
        raise ValueError(
            f"{method_name}: file_path must be a file, not a directory: {file_path}"
        )
    
    return file_path
