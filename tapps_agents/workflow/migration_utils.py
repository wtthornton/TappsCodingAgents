"""
Migration Utilities for Artifact Migration.

Provides utilities for migrating artifacts from dataclass format to Pydantic models.
"""

from __future__ import annotations

import logging
from typing import Any, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def migrate_artifact_from_dataclass(
    data: dict[str, Any],
    artifact_type: type[T],
) -> T:
    """
    Migrate old dataclass artifact to Pydantic model.

    This function attempts to convert old dataclass-formatted artifact data
    to the new Pydantic model format. It handles:
    - Schema version differences
    - Field name changes
    - Type conversions (strings to enums, etc.)
    - Providing defaults for new fields

    Args:
        data: Dictionary containing artifact data (from old format)
        artifact_type: Pydantic model class to migrate to

    Returns:
        Migrated Pydantic model instance

    Raises:
        ValueError: If migration fails and model validation fails
    """
    # First, try direct Pydantic validation (for already-migrated artifacts)
    try:
        return artifact_type.model_validate(data)
    except Exception as e:
        logger.debug(f"Direct validation failed, attempting migration: {e}")

    # If direct validation fails, try using the model's from_dict method if it exists
    # (many artifacts have backward-compatible from_dict methods)
    if hasattr(artifact_type, "from_dict"):
        try:
            result = artifact_type.from_dict(data)
            logger.debug(f"Migrated {artifact_type.__name__} using from_dict method")
            return result
        except Exception as e:
            logger.warning(f"from_dict migration failed for {artifact_type.__name__}: {e}")

    # As a last resort, try validation again (might work with some fields)
    # This allows Pydantic to use defaults for missing fields
    try:
        return artifact_type.model_validate(data, strict=False)
    except Exception as e:
        logger.error(f"Migration failed for {artifact_type.__name__}: {e}")
        raise ValueError(f"Failed to migrate artifact to {artifact_type.__name__}: {e}") from e


def detect_artifact_schema_version(data: dict[str, Any]) -> str:
    """
    Detect artifact schema version from data.

    Args:
        data: Artifact data dictionary

    Returns:
        Schema version string (defaults to "1.0" if not found)
    """
    return data.get("schema_version", "1.0")


def is_pydantic_artifact(data: dict[str, Any]) -> bool:
    """
    Check if artifact data appears to be in Pydantic format.

    This is a heuristic check - artifacts with enum values (not strings)
    are likely already migrated.

    Args:
        data: Artifact data dictionary

    Returns:
        True if artifact appears to be in Pydantic format
    """
    # Check for common enum fields that should be strings in old format
    # but enum instances in new format
    status_fields = ["status", "operation_type", "priority"]
    for field in status_fields:
        if field in data:
            value = data[field]
            # Enums have a 'value' attribute
            if hasattr(value, "value"):
                return True
            # Or they might be enum instances directly
            if hasattr(value, "name") and hasattr(value, "value"):
                return True

    # Check for structured nested objects (Pydantic models)
    # Old format would have plain dicts, new format might have model instances
    nested_fields = ["plan", "metadata", "inputs", "results"]
    for field in nested_fields:
        if field in data:
            value = data[field]
            if isinstance(value, BaseModel):
                return True

    return False
