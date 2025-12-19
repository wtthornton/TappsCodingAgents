"""
Unicode-safe printing utilities for Windows compatibility.

Provides functions that safely handle Unicode characters in print statements,
falling back to ASCII-safe alternatives when encoding errors occur.
"""
import sys
from typing import Any


def safe_print(*args: Any, **kwargs: Any) -> None:
    """
    Safely print text that may contain Unicode characters.
    
    On Windows, if UnicodeEncodeError occurs, falls back to ASCII-safe encoding.
    All other platforms print normally.
    
    Args:
        *args: Arguments to print (same as built-in print)
        **kwargs: Keyword arguments (same as built-in print, e.g., end, flush)
    """
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Convert all arguments to ASCII-safe strings
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                # Replace Unicode characters with ASCII equivalents
                safe_arg = _unicode_to_ascii(arg)
                safe_args.append(safe_arg)
            else:
                safe_args.append(arg)
        print(*safe_args, **kwargs)


def _unicode_to_ascii(text: str) -> str:
    """
    Convert Unicode characters to ASCII-safe equivalents.
    
    Args:
        text: Text that may contain Unicode characters
        
    Returns:
        ASCII-safe text with Unicode characters replaced
    """
    # Common Unicode to ASCII mappings
    replacements = {
        # Emojis
        '🚀': '[START]',
        '✅': '[OK]',
        '❌': '[FAIL]',
        '🔄': '[RUNNING]',
        '⏳': '[WAIT]',
        '⏭️': '[SKIP]',
        '⏸️': '[PAUSE]',
        '💻': '[CODE]',
        '📝': '[DOCS]',
        '🧪': '[TEST]',
        '📊': '[REPORT]',
        '⚙️': '[CONFIG]',
        '💾': '[DATA]',
        '📄': '[FILE]',
        '⚡': '[FAST]',
        '📋': '[LIST]',
        '🏢': '[ENTERPRISE]',
        '✓': '[OK]',
        '✗': '[FAIL]',
        '⚠️': '[WARN]',
        '→': '->',
        '←': '<-',
        # Progress bar characters
        '█': '#',
        '░': '-',
        '▓': '#',
        '▒': '=',
    }
    
    result = text
    for unicode_char, ascii_replacement in replacements.items():
        result = result.replace(unicode_char, ascii_replacement)
    
    # For any remaining Unicode characters, use encode/decode with replace
    try:
        return result.encode('ascii', 'replace').decode('ascii')
    except Exception:
        # Final fallback - replace all non-ASCII with ?
        return ''.join(c if ord(c) < 128 else '?' for c in result)


def safe_format_progress_bar(percentage: float, width: int = 30) -> str:
    """
    Generate ASCII-safe progress bar.
    
    Args:
        percentage: Completion percentage (0-100)
        width: Width of progress bar in characters
        
    Returns:
        ASCII-safe progress bar string
    """
    filled = int((percentage / 100.0) * width)
    # Use ASCII characters instead of Unicode blocks
    bar = "=" * filled + "-" * (width - filled)
    return f"[{bar}] {percentage:.1f}%"


def is_windows_console() -> bool:
    """
    Check if running on Windows with console that may have encoding issues.
    
    Returns:
        True if on Windows, False otherwise
    """
    return sys.platform == "win32"


def setup_windows_encoding() -> None:
    """
    Set up UTF-8 encoding for Windows console if possible.
    
    This should be called at the start of scripts that need Unicode support.
    """
    if not is_windows_console():
        return
    
    # Set environment variable for subprocess calls
    import os
    os.environ["PYTHONIOENCODING"] = "utf-8"
    
    # Reconfigure stdout/stderr if available (Python 3.7+)
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass  # Ignore if reconfigure fails
    
    if hasattr(sys.stderr, 'reconfigure'):
        try:
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass  # Ignore if reconfigure fails

