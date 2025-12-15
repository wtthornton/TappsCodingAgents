"""
Validation mode definitions for E2E test validators.

Provides:
- ValidationMode enum for strict vs relaxed validation
- Mode configuration utilities
"""

from enum import Enum
from typing import Optional


class ValidationMode(Enum):
    """
    Validation mode for E2E test validators.
    
    STRICT: Fail immediately on first error, no fallback paths, no error collection
    RELAXED: Collect all errors and report at end, still fails if any errors found
    """
    STRICT = "strict"
    RELAXED = "relaxed"


def get_validation_mode(mode: Optional[ValidationMode] = None) -> ValidationMode:
    """
    Get validation mode, defaulting to STRICT.
    
    Args:
        mode: Optional validation mode (defaults to STRICT)
        
    Returns:
        ValidationMode enum value
    """
    return mode if mode is not None else ValidationMode.STRICT


def is_strict_mode(mode: Optional[ValidationMode] = None) -> bool:
    """
    Check if validation mode is strict.
    
    Args:
        mode: Optional validation mode (defaults to STRICT)
        
    Returns:
        True if mode is STRICT, False otherwise
    """
    return get_validation_mode(mode) == ValidationMode.STRICT


def is_relaxed_mode(mode: Optional[ValidationMode] = None) -> bool:
    """
    Check if validation mode is relaxed.
    
    Args:
        mode: Optional validation mode (defaults to STRICT)
        
    Returns:
        True if mode is RELAXED, False otherwise
    """
    return get_validation_mode(mode) == ValidationMode.RELAXED

