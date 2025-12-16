"""
Orchestrator agent command handlers
"""
import asyncio
import json

from ...agents.orchestrator.agent import OrchestratorAgent
from ..base import normalize_command
from .common import check_result_error, format_json_output


def handle_orchestrator_command(args: object) -> None:
    """Handle orchestrator agent commands"""
    command = normalize_command(getattr(args, "command", None))
    orchestrator = OrchestratorAgent()
    asyncio.run(orchestrator.activate())
    try:
        if command == "workflow-list":
            result = asyncio.run(orchestrator.run("*workflow-list"))
        elif command == "workflow-start":
            workflow_id = getattr(args, "workflow_id", None)
            if not workflow_id:
                print("Error: workflow_id required", file=__import__("sys").stderr)
                __import__("sys").exit(1)
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
                print("Error: step_id required", file=__import__("sys").stderr)
                __import__("sys").exit(1)
            result = asyncio.run(orchestrator.run("*workflow-skip", step_id=step_id))
        elif command == "workflow-resume":
            result = asyncio.run(orchestrator.run("*workflow-resume"))
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
        elif command == "help" or command is None:
            result = asyncio.run(orchestrator.run("*help"))
        else:
            result = asyncio.run(orchestrator.run("*help"))

        if isinstance(result, dict) and "error" in result:
            check_result_error(result)
        if isinstance(result, dict):
            format_json_output(result)
        else:
            print(result)
    finally:
        asyncio.run(orchestrator.close())

