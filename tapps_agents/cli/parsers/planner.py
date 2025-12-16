"""
Planner agent parser definitions
"""
import argparse


def add_planner_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add planner agent parser and subparsers"""
    planner_parser = subparsers.add_parser("planner", help="Planner Agent commands")
    planner_subparsers = planner_parser.add_subparsers(dest="command", help="Commands")

    plan_parser = planner_subparsers.add_parser(
        "plan", aliases=["*plan"], help="Create a plan for a feature"
    )
    plan_parser.add_argument("description", help="Feature/requirement description")
    plan_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    create_story_parser = planner_subparsers.add_parser(
        "create-story", aliases=["*create-story"], help="Generate a user story"
    )
    create_story_parser.add_argument("description", help="Story description")
    create_story_parser.add_argument("--epic", help="Epic or feature area")
    create_story_parser.add_argument(
        "--priority",
        choices=["high", "medium", "low"],
        default="medium",
        help="Priority",
    )
    create_story_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    list_stories_parser = planner_subparsers.add_parser(
        "list-stories", aliases=["*list-stories"], help="List all stories"
    )
    list_stories_parser.add_argument("--epic", help="Filter by epic")
    list_stories_parser.add_argument("--status", help="Filter by status")
    list_stories_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    planner_subparsers.add_parser(
        "help", aliases=["*help"], help="Show planner commands"
    )

