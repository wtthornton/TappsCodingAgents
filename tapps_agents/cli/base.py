"""
Base classes and shared utilities for CLI commands.

This module provides standardized patterns for:
- Agent lifecycle management (activate/run/close)
- Error handling with consistent exit codes
- Output formatting (JSON/text)
- Async command execution with proper event loop management
"""
import asyncio
import json
import sys
from collections.abc import Callable
from typing import Any, TypeVar

from .feedback import FeedbackManager, get_feedback

T = TypeVar("T")

# Standard exit codes
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_CONFIG_ERROR = 3


def get_exit_code_from_error_category(category: str) -> int:
    """
    Map error envelope category to appropriate CLI exit code.
    
    Args:
        category: Error category from ErrorEnvelope
        
    Returns:
        Exit code (1-3)
    """
    category_to_exit_code = {
        "configuration": EXIT_CONFIG_ERROR,  # 3
        "validation": EXIT_USAGE_ERROR,  # 2 - user input issue
        "permission": EXIT_GENERAL_ERROR,  # 1 - system/permission issue
        "execution": EXIT_GENERAL_ERROR,  # 1 - runtime error
        "external_dependency": EXIT_GENERAL_ERROR,  # 1 - external service issue
        "timeout": EXIT_GENERAL_ERROR,  # 1 - timeout issue
    }
    return category_to_exit_code.get(category, EXIT_GENERAL_ERROR)


def normalize_command(command: str | None) -> str | None:
    """
    Normalize command by removing star prefix if present.
    
    Supports both *command and command formats.
    """
    if command is None:
        return None
    return command.lstrip("*") if command.startswith("*") else command


def format_output(data: dict[str, Any] | str, format_type: str = "json") -> None:
    """
    Format and print output based on format type.
    
    Uses the feedback system for consistent output formatting.
    
    Args:
        data: Data to output (dict for JSON, str for text)
        format_type: Output format ("json" or "text")
    """
    feedback = get_feedback()
    # Temporarily set format type for this output
    original_format = feedback.format_type
    feedback.format_type = format_type
    
    try:
        if isinstance(data, dict):
            feedback.output_result(data)
        else:
            feedback.output_result(data)
    finally:
        feedback.format_type = original_format


def format_error_output(
    error: str,
    error_type: str = "error",
    exit_code: int = EXIT_GENERAL_ERROR,
    format_type: str = "text",
    details: dict[str, Any] | None = None,
) -> None:
    """
    Format and output error message with consistent structure.
    
    Uses the feedback system for standardized error formatting.
    
    Args:
        error: Error message
        error_type: Type of error (e.g., "error", "validation_error", "config_error")
        exit_code: Exit code to use (default: EXIT_GENERAL_ERROR)
        format_type: Output format ("json" or "text")
        details: Additional error details
    """
    feedback = get_feedback()
    # Temporarily set format type for this output
    original_format = feedback.format_type
    feedback.format_type = format_type
    
    try:
        # Map error_type to remediation if it's a common error
        remediation = None
        if error_type == "file_not_found" or "not found" in error.lower():
            remediation = "Check that the file exists and the path is correct"
        elif error_type == "validation_error":
            remediation = "Check your input and try again"
        elif error_type == "config_error":
            remediation = "Check your configuration file and settings"
        
        feedback.error(
            message=error,
            error_code=error_type,
            context=details,
            remediation=remediation,
            exit_code=exit_code,
        )
    finally:
        feedback.format_type = original_format


def handle_agent_error(
    result: dict[str, Any],
    format_type: str = "text",
    exit_code: int | None = None,
) -> None:
    """
    Handle errors from agent execution with standardized output.
    
    Uses error envelope information if available to determine appropriate exit code.
    
    Args:
        result: Agent result dictionary that may contain an "error" key or error envelope
        format_type: Output format ("json" or "text")
        exit_code: Exit code to use (if None, determined from error envelope category)
        
    Raises:
        SystemExit: Always raises SystemExit with appropriate code
    """
    if "error" in result:
        # Check if result contains error envelope structure
        error_info = result.get("error", {})
        if isinstance(error_info, dict) and "category" in error_info:
            # Error envelope format
            category = error_info.get("category", "execution")
            error_message = error_info.get("message", "An error occurred")
            error_code = error_info.get("code", "unknown_error")
            details = error_info.get("details")
            
            # Determine exit code from category if not explicitly provided
            if exit_code is None:
                exit_code = get_exit_code_from_error_category(category)
            
            format_error_output(
                error_message,
                error_type=error_code,
                exit_code=exit_code,
                format_type=format_type,
                details=details,
            )
        else:
            # Legacy format: simple error string or dict with error_type
            error_message = error_info if isinstance(error_info, str) else str(error_info)
            error_type = result.get("error_type", "error")
            details = result.get("details")
            
            # Use provided exit_code or default
            if exit_code is None:
                exit_code = EXIT_GENERAL_ERROR
            
            format_error_output(
                error_message,
                error_type=error_type,
                exit_code=exit_code,
                format_type=format_type,
                details=details,
            )


async def run_with_agent_lifecycle(
    agent: Any,
    command_func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    """
    Run a command function with agent lifecycle management (activate/close).
    
    This is the standard pattern for running agent commands:
    1. Activate agent (load configs, initialize)
    2. Run command
    3. Close agent (cleanup)
    
    Args:
        agent: Agent instance (must have activate() and close() methods)
        command_func: Async function to execute (can be agent.run or a wrapper)
        *args: Positional arguments for command_func
        **kwargs: Keyword arguments for command_func
        
    Returns:
        Result from command_func
        
    Raises:
        Any exception raised by command_func or agent methods
    """
    try:
        await agent.activate()
        return await command_func(*args, **kwargs)
    finally:
        if hasattr(agent, "close") and agent.close is not None:
            await agent.close()


def run_async_command(coro: Any) -> Any:
    """
    Run an async coroutine using asyncio.run.
    
    This function ensures proper event loop management and avoids
    nested event loop issues. Use this instead of calling asyncio.run()
    directly throughout the codebase.
    
    Args:
        coro: Coroutine to run
        
    Returns:
        Result from coroutine
        
    Raises:
        RuntimeError: If called from within an existing event loop
    """
    try:
        # Check if we're already in an event loop
        asyncio.get_running_loop()
        # If we get here, we're in a loop - this is an error
        raise RuntimeError(
            "run_async_command() called from within an event loop. "
            "Use 'await' instead of run_async_command()."
        )
    except RuntimeError:
        # No running loop - safe to use asyncio.run()
        return asyncio.run(coro)


async def run_agent_command(
    agent: Any,
    command: str,
    format_type: str = "json",
    exit_on_error: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Run an agent command with full lifecycle management and error handling.
    
    This is the high-level convenience function that combines:
    - Agent lifecycle management
    - Command execution
    - Error handling
    - Output formatting
    
    Args:
        agent: Agent instance
        command: Command name to run (will be normalized)
        format_type: Output format ("json" or "text")
        exit_on_error: If True, exit on error; if False, return error in result
        **kwargs: Arguments to pass to agent.run()
        
    Returns:
        Result dictionary (may contain "error" key if exit_on_error=False)
        
    Raises:
        SystemExit: If exit_on_error=True and command fails
    """
    normalized_command = normalize_command(command)

    async def _run_command() -> dict[str, Any]:
        return await agent.run(normalized_command, **kwargs)

    result = await run_with_agent_lifecycle(agent, _run_command)

    if exit_on_error:
        handle_agent_error(result, format_type=format_type)
    else:
        return result

    return result


def get_verbosity_level() -> str:
    """
    Get current verbosity level as string.
    
    Returns:
        Verbosity level: "quiet", "normal", or "verbose"
    """
    from .feedback import VerbosityLevel
    verbosity = FeedbackManager.get_verbosity()
    return verbosity.value

