"""
Shared command utilities for output formatting and error handling
"""
import json
import sys
from typing import Any


def format_json_output(data: dict[str, Any] | str, indent: int = 2) -> None:
    """
    Format output as JSON.
    
    Args:
        data: Data to output
        indent: JSON indentation level
    """
    if isinstance(data, dict):
        print(json.dumps(data, indent=indent))
    else:
        print(data)


def format_text_output(data: str) -> None:
    """
    Format output as plain text.
    
    Args:
        data: Text to output
    """
    print(data)


def handle_error(error: str | dict[str, Any], exit_code: int = 1) -> None:
    """
    Handle and output error, then exit.
    
    Args:
        error: Error message or dict with error info
        exit_code: Exit code to use
    """
    if isinstance(error, dict) and "error" in error:
        error_msg = error["error"]
    elif isinstance(error, str):
        error_msg = error
    else:
        error_msg = str(error)
    
    print(f"Error: {error_msg}", file=sys.stderr)
    sys.exit(exit_code)


def check_result_error(result: dict[str, Any]) -> None:
    """
    Check if result contains an error and handle it.
    
    Args:
        result: Result dictionary that may contain "error" key
        
    Raises:
        SystemExit: If error is found
    """
    if "error" in result:
        handle_error(result)

