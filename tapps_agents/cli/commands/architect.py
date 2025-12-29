"""
Architect agent command handlers
"""
import asyncio

from ...agents.architect.agent import ArchitectAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error, format_json_output


def handle_architect_command(args: object) -> None:
    """Handle architect agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("architect")
        feedback.output_result(help_text)
        return
    
    # Check network requirement
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    from ..network_detection import NetworkDetector
    from ...core.network_errors import NetworkRequiredError
    from ..base import handle_network_error
    
    requirement = CommandClassifier.get_network_requirement("architect", command)
    offline_mode = False
    
    if requirement == CommandNetworkRequirement.REQUIRED and not NetworkDetector.is_network_available():
        try:
            raise NetworkRequiredError(
                operation_name=f"architect {command}",
                message="Network is required for this command"
            )
        except NetworkRequiredError as e:
            handle_network_error(e, format_type=output_format)
            return
    elif requirement == CommandNetworkRequirement.OFFLINE:
        offline_mode = True
    
    # Only activate for commands that need it
    architect = ArchitectAgent()
    try:
        asyncio.run(architect.activate(project_root=None, offline_mode=offline_mode))
        if command == "design-system" or command == "design":
            result = asyncio.run(
                architect.run(
                    "design-system",
                    requirements=args.requirements,
                    context=getattr(args, "context", ""),
                    output_file=getattr(args, "output", None) or getattr(args, "output_file", None),
                )
            )
        elif command == "architecture-diagram":
            result = asyncio.run(
                architect.run(
                    "create-diagram",
                    architecture_description=args.architecture_description,
                    diagram_type=getattr(args, "diagram_type", "component"),
                    output_file=getattr(args, "output", None) or getattr(args, "output_file", None),
                )
            )
        elif command == "tech-selection":
            result = asyncio.run(
                architect.run(
                    "select-technology",
                    component_description=args.component_description,
                    requirements=getattr(args, "requirements", ""),
                    constraints=getattr(args, "constraints", []),
                )
            )
        elif command == "design-security":
            result = asyncio.run(
                architect.run(
                    "design-security",
                    system_description=args.system_description,
                    threat_model=getattr(args, "threat_model", ""),
                )
            )
        elif command == "define-boundaries":
            result = asyncio.run(
                architect.run(
                    "define-boundaries",
                    system_description=args.system_description,
                    context=getattr(args, "context", ""),
                )
            )
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("architect")
            feedback.output_result(help_text)
            return

        check_result_error(result)
        feedback.output_result(result, message="Architecture design completed successfully")
    finally:
        safe_close_agent_sync(architect)

