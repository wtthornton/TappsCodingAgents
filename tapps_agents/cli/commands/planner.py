"""
Planner agent command handlers
"""
import asyncio

from ...agents.planner.agent import PlannerAgent
from ..base import normalize_command
from ..feedback import get_feedback
from .common import check_result_error, format_json_output


async def plan_command(description: str, output_format: str = "json"):
    """Create a plan for a feature/requirement"""
    feedback = get_feedback()
    feedback.format_type = output_format
    feedback.start_operation("Plan")
    feedback.info("Creating plan...")
    
    planner = PlannerAgent()
    try:
        await planner.activate()
        result = await planner.run("plan", description=description)

        check_result_error(result)
        feedback.clear_progress()

        if output_format == "json":
            feedback.output_result(result, message="Plan created successfully")
        else:
            feedback.success("Plan created successfully")
            print(f"\nPlan: {result['description']}")
            print(f"\n{result.get('plan', '')}")
    finally:
        await planner.close()


async def create_story_command(
    description: str,
    epic: str | None = None,
    priority: str = "medium",
    output_format: str = "json",
):
    """Generate a user story from description"""
    planner = PlannerAgent()
    try:
        await planner.activate()
        result = await planner.run(
            "create-story", description=description, epic=epic, priority=priority
        )

        check_result_error(result)

        if output_format == "json":
            format_json_output(result)
        else:
            print(f"Story created: {result['story_id']}")
            print(f"File: {result['story_file']}")
            print(f"\nTitle: {result['metadata']['title']}")
            print(f"Epic: {result['metadata']['epic']}")
            print(f"Priority: {result['metadata']['priority']}")
            print(f"Complexity: {result['metadata']['complexity']}/5")
    finally:
        await planner.close()


async def list_stories_command(
    epic: str | None = None,
    status: str | None = None,
    output_format: str = "json",
):
    """List all stories in the project"""
    planner = PlannerAgent()
    try:
        await planner.activate()
        result = await planner.run("list-stories", epic=epic, status=status)

        if output_format == "json":
            format_json_output(result)
        else:
            print(f"Found {result['count']} stories")
            for story in result["stories"]:
                print(f"\n{story['story_id']}: {story['title']}")
                print(
                    f"  Epic: {story['epic']}, Status: {story['status']}, Priority: {story['priority']}"
                )
    finally:
        await planner.close()


def handle_planner_command(args: object) -> None:
    """Handle planner agent commands"""
    command = normalize_command(getattr(args, "command", None))
    planner = PlannerAgent()
    
    try:
        if command == "plan":
            asyncio.run(plan_command(args.description, getattr(args, "format", "json")))
        elif command == "create-story":
            asyncio.run(
                create_story_command(
                    args.description,
                    epic=getattr(args, "epic", None),
                    priority=getattr(args, "priority", "medium"),
                    output_format=getattr(args, "format", "json"),
                )
            )
        elif command == "list-stories":
            asyncio.run(
                list_stories_command(
                    epic=getattr(args, "epic", None),
                    status=getattr(args, "status", None),
                    output_format=getattr(args, "format", "json"),
                )
            )
        elif command == "help" or command is None:
            asyncio.run(planner.activate())
            result = asyncio.run(planner.run("help"))
            print(result["content"])
        else:
            asyncio.run(planner.activate())
            result = asyncio.run(planner.run("help"))
            print(result["content"])
    finally:
        from ..utils.agent_lifecycle import safe_close_agent_sync
        safe_close_agent_sync(planner)

