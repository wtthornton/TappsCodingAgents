"""
Ops agent command handlers
"""
import asyncio

from ...agents.ops.agent import OpsAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error, format_json_output


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
            result = asyncio.run(
                ops.run(
                    "audit-dependencies",
                    severity_threshold=getattr(args, "severity_threshold", "high"),
                )
            )
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("ops")
            feedback.output_result(help_text)
            return

        check_result_error(result)
        feedback.output_result(result, message="Operations completed successfully")
    finally:
        safe_close_agent_sync(ops)

