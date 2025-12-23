"""
Planner agent command handlers
"""
import asyncio

from ...agents.planner.agent import PlannerAgent
from ..base import normalize_command
from ..feedback import get_feedback
from ..help.static_help import get_static_help
from .common import check_result_error, format_json_output


async def plan_command(description: str, output_format: str = "json"):
    """Create a plan for a feature/requirement"""
    feedback = get_feedback()
    feedback.format_type = output_format
    desc_preview = description[:50] + "..." if len(description) > 50 else description
    feedback.start_operation("Plan Creation", f"Creating plan for: {desc_preview}")
    feedback.running("Analyzing requirements...", step=1, total_steps=3)
    
    planner = PlannerAgent()
    try:
        await planner.activate()
        feedback.running("Generating plan structure...", step=2, total_steps=3)
        result = await planner.run("plan", description=description)
        feedback.running("Finalizing plan...", step=3, total_steps=3)

        check_result_error(result)
        feedback.clear_progress()

        summary = {}
        if isinstance(result, dict):
            if "plan" in result:
                summary["plan_items"] = len(result.get("plan", "").split("\n")) if isinstance(result.get("plan"), str) else 0
            if "description" in result:
                summary["description"] = result["description"][:100] + "..." if len(result.get("description", "")) > 100 else result.get("description", "")

        if output_format == "json":
            feedback.output_result(result, message="Plan created successfully", summary=summary)
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
    feedback = get_feedback()
    feedback.format_type = output_format
    desc_preview = description[:50] + "..." if len(description) > 50 else description
    feedback.start_operation("Create User Story", f"Creating story: {desc_preview}")
    feedback.running("Analyzing story requirements...", step=1, total_steps=3)
    
    planner = PlannerAgent()
    try:
        await planner.activate()
        feedback.running("Generating story structure...", step=2, total_steps=3)
        result = await planner.run(
            "create-story", description=description, epic=epic, priority=priority
        )
        feedback.running("Saving story file...", step=3, total_steps=3)

        check_result_error(result)
        feedback.clear_progress()

        summary = {}
        if isinstance(result, dict):
            if "story_id" in result:
                summary["story_id"] = result["story_id"]
            if "story_file" in result:
                summary["story_file"] = result["story_file"]
            if "metadata" in result:
                summary["epic"] = result["metadata"].get("epic", "N/A")
                summary["priority"] = result["metadata"].get("priority", "medium")
                summary["complexity"] = result["metadata"].get("complexity", 0)

        if output_format == "json":
            feedback.output_result(result, message="User story created successfully", summary=summary)
        else:
            feedback.success("User story created successfully")
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
    feedback = get_feedback()
    
    # Help commands first - no activation needed
    if command == "help" or command is None:
        help_text = get_static_help("planner")
        feedback.output_result(help_text)
        return
    
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
        else:
            # Invalid command - show help without activation
            help_text = get_static_help("planner")
            feedback.output_result(help_text)
    finally:
        from ..utils.agent_lifecycle import safe_close_agent_sync
        safe_close_agent_sync(planner)

