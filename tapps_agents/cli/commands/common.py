"""
Shared command utilities for output formatting and error handling
"""
import os
from typing import Any

from ..command_classifier import CommandNetworkRequirement
from ..feedback import get_feedback
from ..network_detection import NetworkDetector


def format_json_output(data: dict[str, Any] | str, indent: int = 2) -> None:
    """
    Format output as JSON.
    
    Uses feedback system for consistent output.
    
    Args:
        data: Data to output
        indent: JSON indentation level
    """
    feedback = get_feedback()
    feedback.format_type = "json"
    if isinstance(data, dict):
        feedback.output_result(data)
    else:
        feedback.output_result(data)


def format_text_output(data: str) -> None:
    """
    Format output as plain text.
    
    Uses feedback system for consistent output.
    
    Args:
        data: Text to output
    """
    feedback = get_feedback()
    feedback.format_type = "text"
    feedback.output_result(data)


def handle_error(error: str | dict[str, Any], exit_code: int = 1) -> None:
    """
    Handle and output error, then exit.
    
    Uses feedback system for standardized error formatting.
    
    Args:
        error: Error message or dict with error info
        exit_code: Exit code to use
    """
    feedback = get_feedback()
    if isinstance(error, dict) and "error" in error:
        error_msg = error["error"]
        error_code = error.get("error_code", "error")
        context = error.get("context")
        remediation = error.get("remediation")
    elif isinstance(error, str):
        error_msg = error
        error_code = "error"
        context = None
        remediation = None
    else:
        error_msg = str(error)
        error_code = "error"
        context = None
        remediation = None
    
    feedback.error(
        message=error_msg,
        error_code=error_code,
        context=context,
        remediation=remediation,
        exit_code=exit_code,
    )


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


def should_use_offline_mode(command_requirement: CommandNetworkRequirement) -> bool:
    """Determine if offline mode should be used.

    Args:
        command_requirement: Network requirement for the command

    Returns:
        True if offline mode should be used, False otherwise
    """
    # Check environment variable
    if os.getenv("TAPPS_AGENTS_OFFLINE", "0") == "1":
        return True

    # Check .tapps-agents/config.yaml for offline_mode
    try:
        from ..core.config import load_config

        cfg = load_config()
        if getattr(cfg, "offline_mode", False):
            return True
    except Exception:
        pass

    # Auto-detect based on command requirement
    if command_requirement == CommandNetworkRequirement.OFFLINE:
        return True
    if command_requirement == CommandNetworkRequirement.OPTIONAL:
        return not NetworkDetector.is_network_available()

    return False

