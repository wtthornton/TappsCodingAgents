"""
Ops agent command handlers

Performance-optimized with:
- Result caching for audit-dependencies (based on requirements files)
"""
import asyncio
from pathlib import Path

from ...agents.ops.agent import OpsAgent
from ...core.agent_cache import get_agent_cache, AgentResultCache
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error, format_json_output

# Version for cache invalidation on agent updates
OPS_CACHE_VERSION = AgentResultCache.CACHE_VERSION


def handle_ops_command(args: object) -> None:
    """Handle ops agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("ops")
        feedback.output_result(help_text)
        return
    
    # Check network requirement
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    from ..network_detection import NetworkDetector
    from ...core.network_errors import NetworkRequiredError
    from ..base import handle_network_error
    
    requirement = CommandClassifier.get_network_requirement("ops", command)
    offline_mode = False
    
    if requirement == CommandNetworkRequirement.REQUIRED and not NetworkDetector.is_network_available():
        try:
            raise NetworkRequiredError(
                operation_name=f"ops {command}",
                message="Network is required for this command"
            )
        except NetworkRequiredError as e:
            handle_network_error(e, format_type=output_format)
            return
    elif requirement == CommandNetworkRequirement.OFFLINE:
        offline_mode = True
    
    # Only activate for commands that need it
    ops = OpsAgent()
    try:
        asyncio.run(ops.activate(offline_mode=offline_mode))
        if command == "security-scan":
            result = asyncio.run(
                ops.run(
                    "security-scan",
                    target=getattr(args, "target", None),
                    scan_type=getattr(args, "type", "all"),
                )
            )
        elif command == "compliance-check":
            result = asyncio.run(
                ops.run(
                    "compliance-check", compliance_type=getattr(args, "type", "general")
                )
            )
        elif command == "deploy":
            result = asyncio.run(
                ops.run(
                    "deploy",
                    target=getattr(args, "target", "local"),
                    environment=getattr(args, "environment", None),
                )
            )
        elif command == "infrastructure-setup":
            result = asyncio.run(
                ops.run(
                    "infrastructure-setup",
                    infrastructure_type=getattr(args, "type", "docker"),
                )
            )
        elif command == "audit-dependencies":
            # Cache based on dependency files (requirements.txt, pyproject.toml)
            cache = get_agent_cache("ops")
            cwd = Path.cwd()
            
            # Find dependency files to use as cache key
            dep_files = []
            for dep_file in ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"]:
                path = cwd / dep_file
                if path.exists():
                    dep_files.append(path)
            
            # Check cache if we have dependency files
            cached_result = None
            if dep_files:
                cached_result = asyncio.run(
                    cache.get_cached_result(dep_files, "audit-dependencies", OPS_CACHE_VERSION)
                )
            
            if cached_result is not None:
                result = cached_result
                feedback.info("Using cached result (dependency files unchanged)")
            else:
                result = asyncio.run(
                    ops.run(
                        "audit-dependencies",
                        severity_threshold=getattr(args, "severity_threshold", "high"),
                    )
                )
                # Cache if we have dependency files
                if dep_files:
                    asyncio.run(
                        cache.save_result(dep_files, "audit-dependencies", OPS_CACHE_VERSION, result)
                    )
        elif command == "audit-bundle":
            result = asyncio.run(ops.run("audit-bundle"))
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("ops")
            feedback.output_result(help_text)
            return

        check_result_error(result)
        feedback.output_result(result, message="Operations completed successfully")
    finally:
        safe_close_agent_sync(ops)

