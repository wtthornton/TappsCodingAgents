"""
JSON serialization utilities with circular reference handling.

Provides safe JSON serialization that handles circular references and
non-serializable types gracefully.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def safe_json_dumps(obj: Any, indent: int = 2, ensure_ascii: bool = False) -> str:
    """
    Safely serialize object to JSON string, handling circular references.
    
    This function detects and handles circular references in data structures,
    replacing them with the string "<circular reference>" to prevent serialization errors.
    
    Args:
        obj: Object to serialize (can contain circular references)
        indent: JSON indentation level (default: 2)
        ensure_ascii: Whether to escape non-ASCII characters (default: False)
        
    Returns:
        JSON string representation of the object
        
    Example:
        >>> data = {}
        >>> data['self'] = data  # Circular reference
        >>> safe_json_dumps(data)
        '{\\n  "self": "<circular reference>"\\n}'
    """
    def _make_serializable(o: Any, seen: set[int] | None = None) -> Any:
        """Recursively convert object to JSON-serializable format."""
        if seen is None:
            seen = set()
        
        # Handle primitives first (no circular reference risk)
        if isinstance(o, (str, int, float, bool, type(None))):
            return o
        
        # Handle datetime (immutable)
        if isinstance(o, datetime):
            return o.isoformat()
        
        # Handle Path objects (immutable)
        if isinstance(o, Path):
            return str(o)
        
        # For mutable objects, check for circular references
        obj_id = id(o)
        if obj_id in seen:
            return "<circular reference>"
        
        try:
            # Handle dict
            if isinstance(o, dict):
                seen.add(obj_id)
                result = {}
                for k, v in o.items():
                    # Convert non-string keys to string
                    key = str(k) if not isinstance(k, (str, int, float, bool, type(None))) else k
                    result[key] = _make_serializable(v, seen)
                seen.remove(obj_id)
                return result
            
            # Handle list/tuple
            if isinstance(o, (list, tuple)):
                seen.add(obj_id)
                result = [_make_serializable(item, seen) for item in o]
                seen.remove(obj_id)
                return result
            
            # For other objects, try to convert to dict or string
            if hasattr(o, '__dict__'):
                seen.add(obj_id)
                try:
                    result = _make_serializable(o.__dict__, seen)
                    seen.remove(obj_id)
                    return result
                except Exception:
                    seen.remove(obj_id)
                    return str(o)
            
            # Fallback: convert to string
            return str(o)
            
        except Exception as e:
            # If anything fails, return error string
            seen.discard(obj_id)
            logger.debug(f"Serialization error for object {type(o).__name__}: {e}")
            return f"<serialization error: {e!s}>"
    
    try:
        serializable_obj = _make_serializable(obj)
        return json.dumps(serializable_obj, indent=indent, ensure_ascii=ensure_ascii)
    except Exception as e:
        logger.error(f"Failed to serialize object to JSON: {e}")
        # Last resort: return minimal error representation
        return json.dumps({"error": f"Serialization failed: {e!s}"}, indent=indent)


def safe_json_dump(obj: Any, fp: Any, indent: int = 2, ensure_ascii: bool = False) -> None:
    """
    Safely serialize object to JSON file, handling circular references.
    
    This is a drop-in replacement for json.dump() that handles circular references.
    
    Args:
        obj: Object to serialize (can contain circular references)
        fp: File-like object to write to
        indent: JSON indentation level (default: 2)
        ensure_ascii: Whether to escape non-ASCII characters (default: False)
        
    Example:
        >>> data = {}
        >>> data['self'] = data  # Circular reference
        >>> with open('output.json', 'w') as f:
        ...     safe_json_dump(data, f)
    """
    json_str = safe_json_dumps(obj, indent=indent, ensure_ascii=ensure_ascii)
    fp.write(json_str)

