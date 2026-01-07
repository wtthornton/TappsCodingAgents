"""
Documenter agent command handlers

Performance-optimized with:
- Result caching for document and generate-docs commands
"""
import asyncio
from pathlib import Path

from ...agents.documenter.agent import DocumenterAgent
from ...core.agent_cache import get_agent_cache, AgentResultCache
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error, format_json_output

# Version for cache invalidation on agent updates
DOCUMENTER_CACHE_VERSION = AgentResultCache.CACHE_VERSION


def handle_documenter_command(args: object) -> None:
    """Handle documenter agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("documenter")
        feedback.output_result(help_text)
        return
    
    # Check network requirement
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    from ..network_detection import NetworkDetector
    from ...core.network_errors import NetworkRequiredError
    from ..base import handle_network_error
    
    requirement = CommandClassifier.get_network_requirement("documenter", command)
    offline_mode = False
    
    if requirement == CommandNetworkRequirement.REQUIRED and not NetworkDetector.is_network_available():
        try:
            raise NetworkRequiredError(
                operation_name=f"documenter {command}",
                message="Network is required for this command"
            )
        except NetworkRequiredError as e:
            handle_network_error(e, format_type=output_format)
            return
    elif requirement == CommandNetworkRequirement.OFFLINE:
        offline_mode = True
    
    # Only activate for commands that need it
    documenter = DocumenterAgent()
    cache = get_agent_cache("documenter")
    
    try:
        asyncio.run(documenter.activate(offline_mode=offline_mode))
        if command == "document":
            file_path_obj = Path(args.file).resolve()
            
            # Check cache first
            cached_result = asyncio.run(
                cache.get_cached_result(file_path_obj, "document", DOCUMENTER_CACHE_VERSION)
            )
            
            if cached_result is not None:
                result = cached_result
                feedback.info("Using cached result (file unchanged)")
            else:
                result = asyncio.run(
                    documenter.run(
                        "document",
                        file=args.file,
                        output_format=getattr(args, "output_format", "markdown"),
                        output_file=getattr(args, "output", None) or getattr(args, "output_file", None),
                    )
                )
                # Cache the result
                asyncio.run(
                    cache.save_result(file_path_obj, "document", DOCUMENTER_CACHE_VERSION, result)
                )
        elif command in ("generate-docs", "document-api"):
            file_path_obj = Path(args.file).resolve()
            
            # Check cache first
            cached_result = asyncio.run(
                cache.get_cached_result(file_path_obj, "generate-docs", DOCUMENTER_CACHE_VERSION)
            )
            
            if cached_result is not None:
                result = cached_result
                feedback.info("Using cached result (file unchanged)")
            else:
                result = asyncio.run(
                    documenter.run(
                        "generate-docs",
                        file=args.file,
                        output_format=getattr(args, "output_format", "markdown"),
                    )
                )
                # Cache the result
                asyncio.run(
                    cache.save_result(file_path_obj, "generate-docs", DOCUMENTER_CACHE_VERSION, result)
                )
        elif command == "update-readme":
            result = asyncio.run(
                documenter.run(
                    "update-readme",
                    project_root=getattr(args, "project_root", None),
                    context=getattr(args, "context", None),
                )
            )
        elif command == "update-docstrings":
            result = asyncio.run(
                documenter.run(
                    "update-docstrings",
                    file=args.file,
                    docstring_format=getattr(args, "docstring_format", None),
                    write_file=getattr(args, "write_file", False),
                )
            )
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("documenter")
            feedback.output_result(help_text)
            return

        check_result_error(result)
        feedback.output_result(result, message="Documentation completed successfully")
    finally:
        safe_close_agent_sync(documenter)

