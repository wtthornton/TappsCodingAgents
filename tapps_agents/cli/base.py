"""
Base classes and shared utilities for CLI commands
"""
import asyncio
import json
import sys
from abc import ABC, abstractmethod
from typing import Any


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
    
    Args:
        data: Data to output (dict for JSON, str for text)
        format_type: Output format ("json" or "text")
    """
    if format_type == "json":
        if isinstance(data, dict):
            print(json.dumps(data, indent=2))
        else:
            print(data)
    else:
        print(data)


def handle_agent_error(result: dict[str, Any]) -> None:
    """
    Handle errors from agent execution.
    
    Args:
        result: Agent result dictionary that may contain an "error" key
        
    Raises:
        SystemExit: If error is found in result
    """
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


async def run_with_agent_lifecycle(
    agent: Any,
    command_func: callable,
    *args,
    **kwargs,
) -> Any:
    """
    Run a command function with agent lifecycle management (activate/close).
    
    Args:
        agent: Agent instance
        command_func: Async function to execute
        *args: Positional arguments for command_func
        **kwargs: Keyword arguments for command_func
        
    Returns:
        Result from command_func
    """
    try:
        await agent.activate()
        return await command_func(*args, **kwargs)
    finally:
        await agent.close()


def run_async_command(coro: Any) -> Any:
    """
    Run an async coroutine using asyncio.run.
    
    Args:
        coro: Coroutine to run
        
    Returns:
        Result from coroutine
    """
    return asyncio.run(coro)

