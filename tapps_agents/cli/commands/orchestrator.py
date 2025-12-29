"""
Orchestrator agent command handlers
"""
import asyncio
import json

from ...agents.orchestrator.agent import OrchestratorAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error, format_json_output


def handle_orchestrator_command(args: object) -> None:
    """Handle orchestrator agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("orchestrator")
        feedback.output_result(help_text)
        return
    
    # Check network requirement
    from ..command_classifier import CommandClassifier, CommandNetworkRequirement
    from ..network_detection import NetworkDetector
    from ...core.network_errors import NetworkRequiredError
    from ..base import handle_network_error
    
    requirement = CommandClassifier.get_network_requirement("orchestrator", command)
    offline_mode = False
    
    if requirement == CommandNetworkRequirement.REQUIRED and not NetworkDetector.is_network_available():
        try:
            raise NetworkRequiredError(
                operation_name=f"orchestrator {command}",
                message="Network is required for this command"
            )
        except NetworkRequiredError as e:
            handle_network_error(e, format_type=output_format)
            return
    elif requirement == CommandNetworkRequirement.OFFLINE:
        offline_mode = True
    
    # Only activate for commands that need it
    orchestrator = OrchestratorAgent()
    try:
        asyncio.run(orchestrator.activate(offline_mode=offline_mode))
        if command == "workflow-list":
            result = asyncio.run(orchestrator.run("*workflow-list"))
        elif command == "workflow-start":
            workflow_id = getattr(args, "workflow_id", None)
            if not workflow_id:
                feedback.error(
                    "workflow_id required",
                    error_code="validation_error",
                    exit_code=2,
                )
            result = asyncio.run(
                orchestrator.run("*workflow-start", workflow_id=workflow_id)
            )
        elif command == "workflow-status":
            result = asyncio.run(orchestrator.run("*workflow-status"))
        elif command == "workflow-next":
            result = asyncio.run(orchestrator.run("*workflow-next"))
        elif command == "workflow-skip":
            step_id = getattr(args, "step_id", None)
            if not step_id:
                feedback.error(
                    "step_id required",
                    error_code="validation_error",
                    exit_code=2,
                )
            result = asyncio.run(orchestrator.run("*workflow-skip", step_id=step_id))
        elif command == "workflow-resume":
            result = asyncio.run(orchestrator.run("*workflow-resume"))
        elif command == "workflow":
            workflow_file = getattr(args, "workflow_file", None)
            if not workflow_file or not isinstance(workflow_file, str):
                feedback.error(
                    "workflow_file path required (must be a non-empty string)",
                    error_code="validation_error",
                    exit_code=2,
                )
            result = asyncio.run(
                orchestrator.run("*workflow", workflow_file=workflow_file)
            )
        elif command == "gate":
            condition = getattr(args, "condition", None)
            scoring_data = getattr(args, "scoring_data", {})
            if isinstance(scoring_data, str):
                scoring_data = json.loads(scoring_data)
            result = asyncio.run(
                orchestrator.run(
                    "*gate", condition=condition, scoring_data=scoring_data
                )
            )
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("orchestrator")
            feedback.output_result(help_text)
            return

        if isinstance(result, dict) and "error" in result:
            check_result_error(result)
        if isinstance(result, dict):
            feedback.output_result(result, message="Orchestration completed successfully")
        else:
            feedback.output_result(result)
    finally:
        safe_close_agent_sync(orchestrator)

