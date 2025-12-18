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
    plan_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format: 'json' for structured plan data (default), 'text' for human-readable plan"
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
    create_story_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format: 'json' for structured story data (default), 'text' for human-readable user story"
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
    list_stories_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format: 'json' for structured story list (default), 'text' for human-readable list"
    )

    planner_subparsers.add_parser(
        "help", aliases=["*help"], help="Show planner commands"
    )

