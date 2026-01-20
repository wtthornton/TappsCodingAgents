"""
Enhancer agent command handlers
"""
import asyncio
import json
import sys

from ...agents.enhancer.agent import EnhancerAgent
from ...core.unicode_safe import safe_print
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error, format_json_output


def handle_enhancer_command(args: object) -> None:
    """Handle enhancer agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("enhancer")
        feedback.output_result(help_text)
        return
    
    # Check network requirement
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    from ..network_detection import NetworkDetector
    from ...core.network_errors import NetworkRequiredError
    from ..base import handle_network_error
    
    requirement = CommandClassifier.get_network_requirement("enhancer", command)
    offline_mode = False
    
    if requirement == CommandNetworkRequirement.REQUIRED and not NetworkDetector.is_network_available():
        try:
            raise NetworkRequiredError(
                operation_name=f"enhancer {command}",
                message="Network is required for this command"
            )
        except NetworkRequiredError as e:
            handle_network_error(e, format_type=output_format)
            return
    elif requirement == CommandNetworkRequirement.OFFLINE:
        offline_mode = True
    
    # Only activate for commands that need it
    enhancer = EnhancerAgent()
    try:
        asyncio.run(enhancer.activate(project_root=None, offline_mode=offline_mode))

        if command == "enhance":
            result = asyncio.run(
                enhancer.run(
                    "enhance",
                    prompt=args.prompt,
                    output_format=getattr(args, "format", "markdown"),
                    output_file=getattr(args, "output", None),
                    config_path=getattr(args, "config", None),
                )
            )
        elif command == "enhance-quick":
            result = asyncio.run(
                enhancer.run(
                    "enhance-quick",
                    prompt=args.prompt,
                    output_format=getattr(args, "format", "markdown"),
                    output_file=getattr(args, "output", None),
                )
            )
        elif command == "enhance-stage":
            result = asyncio.run(
                enhancer.run(
                    "enhance-stage",
                    stage=args.stage,
                    prompt=getattr(args, "prompt", None),
                    session_id=getattr(args, "session_id", None),
                )
            )
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("enhancer")
            feedback.output_result(help_text)
            return

        check_result_error(result)

        # Format output
        output_format = getattr(args, "format", "markdown")
        if output_format == "json":
            feedback.output_result(result, message="Enhancement completed successfully")
        else:
            # For markdown format, use safe_print to handle Unicode encoding on Windows
            enhanced = result.get("enhanced_prompt", {})
            feedback.success("Enhancement completed successfully")
            
            if isinstance(enhanced, dict):
                enhanced_text = enhanced.get("enhanced_prompt", json.dumps(enhanced, indent=2, ensure_ascii=False))
            else:
                enhanced_text = enhanced
            
            # Use safe_print to handle Unicode characters on Windows
            safe_print(enhanced_text)
    finally:
        safe_close_agent_sync(enhancer)

