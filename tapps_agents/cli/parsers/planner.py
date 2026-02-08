"""
Planner agent parser definitions
"""
import argparse


def add_planner_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add planner agent parser and subparsers"""
    planner_parser = subparsers.add_parser(
        "planner",
        help="Planner Agent commands",
        description="""Project planning and task breakdown agent.
        
The Planner Agent helps organize development work:
  • Create detailed implementation plans
  • Generate user stories
  • Break down features into tasks
  • Estimate effort and complexity
  • Organize work by epics

Use this agent at the start of development to create structured plans.""",
    )
    planner_subparsers = planner_parser.add_subparsers(
        dest="command", help="Planner agent subcommand (use 'help' to see all available commands)"
    )

    plan_parser = planner_subparsers.add_parser(
        "plan",
        aliases=["*plan"],
        help="Create a detailed plan for a feature",
        description="""Create a comprehensive implementation plan for a feature or requirement.
        
Generates a structured plan including:
  • Task breakdown
  • Dependencies
  • Estimated effort
  • Implementation steps
  • Testing strategy

Example:
  tapps-agents planner plan "Add user authentication with OAuth"
  tapps-agents planner plan "Implement shopping cart" --format text""",
    )
    plan_parser.add_argument("description", help="Description of the feature or requirement to plan. Include functional requirements, goals, constraints, and any relevant context. Be specific for more accurate planning.")
    plan_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    plan_parser.add_argument(
        "--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured plan data (default), 'text' for human-readable plan, 'markdown' for markdown format"
    )
    plan_parser.add_argument(
        "--no-enhance",
        action="store_true",
        help="Disable automatic prompt enhancement for this command",
    )
    plan_parser.add_argument(
        "--enhance",
        action="store_true",
        help="Force prompt enhancement even if quality is high",
    )
    plan_parser.add_argument(
        "--enhance-mode",
        choices=["quick", "full"],
        help="Override enhancement mode: 'quick' for fast 3-stage enhancement, 'full' for complete 7-stage enhancement",
    )
    plan_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    create_story_parser = planner_subparsers.add_parser(
        "create-story",
        aliases=["*create-story"],
        help="Generate a user story",
        description="""Generate a well-structured user story.
        
Creates user stories following the "As a... I want... So that..." format
with acceptance criteria, priority, and effort estimates.

Example:
  tapps-agents planner create-story "User login functionality"
  tapps-agents planner create-story "Export data to CSV" --epic "Data Management" --priority high""",
    )
    create_story_parser.add_argument("description", help="Description of the user story or feature to create. Can be a brief description - the planner will expand it into a full user story format.")
    create_story_parser.add_argument("--epic", help="Epic name or feature area this story belongs to (e.g., 'Authentication', 'User Management', 'Payment Processing'). Helps organize stories into larger features.")
    create_story_parser.add_argument(
        "--priority",
        choices=["high", "medium", "low"],
        default="medium",
        help="Priority level for the story: 'high' for critical features, 'medium' for important features (default), 'low' for nice-to-have features",
    )
    create_story_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    create_story_parser.add_argument(
        "--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured story data (default), 'text' for human-readable user story, 'markdown' for markdown format"
    )
    create_story_parser.add_argument(
        "--no-enhance",
        action="store_true",
        help="Disable automatic prompt enhancement for this command",
    )
    create_story_parser.add_argument(
        "--enhance",
        action="store_true",
        help="Force prompt enhancement even if quality is high",
    )
    create_story_parser.add_argument(
        "--enhance-mode",
        choices=["quick", "full"],
        help="Override enhancement mode: 'quick' for fast 3-stage enhancement, 'full' for complete 7-stage enhancement",
    )
    create_story_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    list_stories_parser = planner_subparsers.add_parser(
        "list-stories",
        aliases=["*list-stories"],
        help="List all user stories",
        description="""List user stories with optional filtering.
        
Shows all created user stories, optionally filtered by:
  • Epic/feature area
  • Status (todo, in-progress, done)
  
Example:
  tapps-agents planner list-stories
  tapps-agents planner list-stories --epic "Authentication" --status todo""",
    )
    list_stories_parser.add_argument("--epic", help="Filter stories to show only those belonging to a specific epic or feature area (e.g., 'Authentication', 'User Management')")
    list_stories_parser.add_argument("--status", help="Filter stories by status: 'todo' for unstarted stories, 'in-progress' for active stories, 'done' for completed stories")
    list_stories_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    list_stories_parser.add_argument(
        "--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured story list (default), 'text' for human-readable list, 'markdown' for markdown format"
    )
    list_stories_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    evaluate_epic_parser = planner_subparsers.add_parser(
        "evaluate-epic",
        aliases=["*evaluate-epic"],
        help="Evaluate Epic document quality",
        description="""Evaluate an Epic markdown document for structure, story breakdown, and dependencies.

Returns scores for: overview, story breakdown, dependencies, acceptance criteria.

Example:
  tapps-agents planner evaluate-epic docs/planning/EPIC-53-REVIEWER-AND-PLANNING-IMPROVEMENTS.md
  tapps-agents planner evaluate-epic docs/prd/epic-51.md --format text""",
    )
    evaluate_epic_parser.add_argument(
        "file",
        help="Path to Epic markdown file (e.g. docs/planning/EPIC-53.md)",
    )
    evaluate_epic_parser.add_argument(
        "--format", choices=["json", "text", "markdown"], default="json",
        help="Output format (default: json)",
    )

    evaluate_plan_parser = planner_subparsers.add_parser(
        "evaluate-plan",
        aliases=["*evaluate-plan", "evaluate-implementation-plan", "*evaluate-implementation-plan"],
        help="Evaluate implementation plan (phases, tasks, completion)",
        description="""Evaluate an implementation plan markdown for phases, tasks, and completion criteria.

Example:
  tapps-agents planner evaluate-plan docs/planning/REVIEWER_AND_PLANNING_IMPROVEMENTS_IMPLEMENTATION_PLAN.md""",
    )
    evaluate_plan_parser.add_argument("file", help="Path to implementation plan markdown file")
    evaluate_plan_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    planner_subparsers.add_parser(
        "help", aliases=["*help"], help="Show planner commands"
    )

