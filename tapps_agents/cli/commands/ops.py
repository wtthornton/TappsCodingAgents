"""
Ops agent command handlers
"""
import asyncio

from ...agents.ops.agent import OpsAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..utils.agent_lifecycle import safe_close_agent_sync
from .common import check_result_error, format_json_output


def handle_ops_command(args: object) -> None:
    """Handle ops agent commands"""
    feedback = get_feedback()
    command = normalize_command(getattr(args, "command", None))
    output_format = getattr(args, "format", "json")
    feedback.format_type = output_format
    ops = OpsAgent()
    asyncio.run(ops.activate())

    try:
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
        elif command == "help" or command is None:
            result = asyncio.run(ops.run("help"))
            feedback.output_result(result["content"] if isinstance(result, dict) else result)
            return
        else:
            result = asyncio.run(ops.run("help"))
            feedback.output_result(result["content"] if isinstance(result, dict) else result)
            return

        check_result_error(result)
        feedback.output_result(result, message="Operations completed successfully")
    finally:
        safe_close_agent_sync(ops)

