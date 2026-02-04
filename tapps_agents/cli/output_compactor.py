"""
Output compactor for CLI commands.

Provides functions to reduce output size to prevent overwhelming Cursor's terminal.
Large outputs can cause Cursor to crash with "Connection Error".
"""
import json
from typing import Any

# Keys that should be removed in compact mode (verbose debug data)
DEBUG_KEYS = {
    "context7_debug",
    "_explanations",
    "metrics",  # Keep scoring, remove detailed metrics
    "language_detection",  # Keep file_type, remove detection details
}

# Keys that should be truncated (arrays that can be very large)
TRUNCATE_KEYS = {
    "suggestions": 5,  # Max 5 suggestions
    "libraries_detected": 10,  # Max 10 libraries
    "patterns": 5,  # Max 5 patterns
    "issues": 20,  # Max 20 linting issues
    "errors": 20,  # Max 20 type check errors
    "duplicates": 10,  # Max 10 duplicates
}

# Maximum size for string values (bytes)
MAX_STRING_SIZE = 10000  # 10KB

# Maximum total output size (bytes)
MAX_OUTPUT_SIZE = 100000  # 100KB


def compact_output(data: dict[str, Any], deep: bool = False) -> dict[str, Any]:
    """
    Compact output by removing verbose debug data.
    
    Args:
        data: Result dictionary to compact
        deep: If True, also apply aggressive truncation
        
    Returns:
        Compacted result dictionary
    """
    if not isinstance(data, dict):
        return data
    
    result = {}
    
    for key, value in data.items():
        # Skip debug keys
        if key in DEBUG_KEYS:
            continue
        
        # Handle context7_verification specially - only include summary
        if key == "context7_verification" and isinstance(value, dict):
            if deep:
                # In deep mode, just include a count
                result["context7_libraries_verified"] = len(value)
            else:
                # In normal mode, include simplified version
                result[key] = {
                    k: {
                        "docs_available": v.get("api_docs_available", False),
                        "error": v.get("error") if "error" in v else None,
                    }
                    for k, v in value.items()
                }
            continue
        
        # Handle library_recommendations - only include counts in deep mode
        if key == "library_recommendations" and isinstance(value, dict):
            if deep:
                result["library_recommendations_count"] = len(value)
            else:
                # Truncate long lists within recommendations
                result[key] = _truncate_nested(value, max_items=3)
            continue
        
        # Handle pattern_guidance - only include counts in deep mode
        if key == "pattern_guidance" and isinstance(value, dict):
            if deep:
                result["pattern_guidance_count"] = len(value)
            else:
                result[key] = _truncate_nested(value, max_items=3)
            continue
        
        # Truncate known large arrays
        if key in TRUNCATE_KEYS and isinstance(value, list):
            max_items = TRUNCATE_KEYS[key]
            if len(value) > max_items:
                result[key] = value[:max_items]
                result[f"{key}_truncated"] = True
                result[f"{key}_total"] = len(value)
            else:
                result[key] = value
            continue
        
        # Recursively compact nested dicts
        if isinstance(value, dict):
            result[key] = compact_output(value, deep)
        elif isinstance(value, list):
            # Compact each item in list if it's a dict
            result[key] = [
                compact_output(item, deep) if isinstance(item, dict) else item
                for item in value
            ]
        elif isinstance(value, str) and len(value) > MAX_STRING_SIZE:
            # Truncate very long strings
            result[key] = value[:MAX_STRING_SIZE] + f"... (truncated, {len(value)} chars total)"
        else:
            result[key] = value
    
    return result


def _truncate_nested(data: dict[str, Any], max_items: int = 3) -> dict[str, Any]:
    """Truncate nested lists within a dictionary."""
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            # Recursively truncate
            inner_result = {}
            for inner_key, inner_value in value.items():
                if isinstance(inner_value, list) and len(inner_value) > max_items:
                    inner_result[inner_key] = inner_value[:max_items]
                    inner_result[f"{inner_key}_truncated"] = True
                else:
                    inner_result[inner_key] = inner_value
            result[key] = inner_result
        elif isinstance(value, list) and len(value) > max_items:
            result[key] = value[:max_items]
            result[f"{key}_truncated"] = True
        else:
            result[key] = value
    return result


def estimate_size(data: Any) -> int:
    """
    Estimate the JSON serialized size of data.
    
    Args:
        data: Data to estimate size of
        
    Returns:
        Estimated size in bytes
    """
    try:
        return len(json.dumps(data, ensure_ascii=False))
    except (TypeError, ValueError):
        return 0


def limit_output_size(data: dict[str, Any], max_size: int = MAX_OUTPUT_SIZE) -> dict[str, Any]:
    """
    Limit output size by progressively compacting until under max_size.
    
    Args:
        data: Result dictionary
        max_size: Maximum output size in bytes
        
    Returns:
        Size-limited result dictionary
    """
    current_size = estimate_size(data)
    
    # If already under limit, return as-is
    if current_size <= max_size:
        return data
    
    # Try normal compaction first
    compacted = compact_output(data, deep=False)
    current_size = estimate_size(compacted)
    
    if current_size <= max_size:
        return compacted
    
    # Try deep compaction
    deep_compacted = compact_output(data, deep=True)
    current_size = estimate_size(deep_compacted)
    
    if current_size <= max_size:
        deep_compacted["_output_compacted"] = True
        return deep_compacted
    
    # Still too large - remove more data
    minimal = _create_minimal_output(data)
    minimal["_output_truncated"] = True
    minimal["_original_size_bytes"] = estimate_size(data)
    
    return minimal


def _create_minimal_output(data: dict[str, Any]) -> dict[str, Any]:
    """Create minimal output with only essential fields."""
    minimal = {}
    
    # Keep only essential fields
    essential_fields = {
        "file",
        "file_type",
        "scoring",
        "passed",
        "threshold",
        "error",
        "quality_gate",
    }
    
    for key in essential_fields:
        if key in data:
            value = data[key]
            # For scoring, only keep top-level scores
            if key == "scoring" and isinstance(value, dict):
                minimal[key] = {
                    "overall_score": value.get("overall_score"),
                    "complexity_score": value.get("complexity_score"),
                    "security_score": value.get("security_score"),
                    "maintainability_score": value.get("maintainability_score"),
                }
            else:
                minimal[key] = value
    
    return minimal


def clean_debug_output(data: dict[str, Any]) -> dict[str, Any]:
    """
    Remove debug and development-only data from output.
    
    This is less aggressive than compact_output and just removes
    debug logging and development diagnostic data.
    
    Args:
        data: Result dictionary
        
    Returns:
        Cleaned result dictionary
    """
    if not isinstance(data, dict):
        return data
    
    # Keys to always remove (debug/development only)
    debug_only_keys = {
        "context7_debug",
        "_explanations",
        "_from_cache",
        "_cache_stats",
    }
    
    result = {}
    for key, value in data.items():
        if key in debug_only_keys:
            continue
        if key.startswith("_"):
            # Skip private keys unless they're meaningful
            if key in {"_output_compacted", "_output_truncated", "_original_size_bytes"}:
                result[key] = value
            continue
        
        # Recursively clean nested dicts
        if isinstance(value, dict):
            result[key] = clean_debug_output(value)
        elif isinstance(value, list):
            result[key] = [
                clean_debug_output(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    
    return result
