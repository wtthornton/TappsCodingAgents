"""
Improver agent command handlers
"""
import asyncio

from ...agents.improver.agent import ImproverAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error, format_json_output


def handle_improver_command(args: object) -> None:
    """Handle improver agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("improver")
        feedback.output_result(help_text)
        return
    
    # Check network requirement
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    from ..network_detection import NetworkDetector
    from ...core.network_errors import NetworkRequiredError
    from ..base import handle_network_error
    
    requirement = CommandClassifier.get_network_requirement("improver", command)
    offline_mode = False
    
    if requirement == CommandNetworkRequirement.REQUIRED and not NetworkDetector.is_network_available():
        try:
            raise NetworkRequiredError(
                operation_name=f"improver {command}",
                message="Network is required for this command"
            )
        except NetworkRequiredError as e:
            handle_network_error(e, format_type=output_format)
            return
    elif requirement == CommandNetworkRequirement.OFFLINE:
        offline_mode = True
    
    # Only activate for commands that need it
    improver = ImproverAgent()
    try:
        asyncio.run(improver.activate(offline_mode=offline_mode))
        if command == "refactor":
            result = asyncio.run(
                improver.run(
                    "refactor",
                    file_path=args.file_path,
                    instruction=getattr(args, "instruction", None),
                )
            )
        elif command == "optimize":
            result = asyncio.run(
                improver.run(
                    "optimize",
                    file_path=args.file_path,
                    optimization_type=getattr(args, "type", "performance"),
                )
            )
        elif command == "improve-quality":
            focus = getattr(args, "focus", None)
            auto_apply = getattr(args, "auto_apply", False)
            preview = getattr(args, "preview", False)
            result = asyncio.run(
                improver.run(
                    "improve-quality", 
                    file_path=args.file_path, 
                    focus=focus,
                    auto_apply=auto_apply,
                    preview=preview,
                )
            )
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("improver")
            feedback.output_result(help_text)
            return

        check_result_error(result)
        feedback.output_result(result, message="Improvement completed successfully")
    finally:
        safe_close_agent_sync(improver)

