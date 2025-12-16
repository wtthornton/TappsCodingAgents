"""
Enhancer agent command handlers
"""
import asyncio
import json

from ...agents.enhancer.agent import EnhancerAgent
from ..base import normalize_command
from .common import check_result_error, format_json_output


def handle_enhancer_command(args: object) -> None:
    """Handle enhancer agent commands"""
    command = normalize_command(getattr(args, "command", None))
    enhancer = EnhancerAgent()
    asyncio.run(enhancer.activate())

    try:
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
        elif command == "enhance-resume":
            result = asyncio.run(
                enhancer.run("enhance-resume", session_id=args.session_id)
            )
        elif command == "help" or command is None:
            result = asyncio.run(enhancer.run("help"))
            print(result["content"] if isinstance(result, dict) else result)
            return
        else:
            result = asyncio.run(enhancer.run("help"))
            print(result["content"] if isinstance(result, dict) else result)
            return

        check_result_error(result)

        # Format output
        if getattr(args, "format", "markdown") == "json":
            format_json_output(result)
        else:
            enhanced = result.get("enhanced_prompt", {})
            if isinstance(enhanced, dict):
                print(enhanced.get("enhanced_prompt", json.dumps(enhanced, indent=2)))
            else:
                print(enhanced)
    finally:
        asyncio.run(enhancer.close())

