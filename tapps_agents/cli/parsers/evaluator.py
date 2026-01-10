"""
Evaluator agent parser definitions
"""
import argparse


def add_evaluator_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add evaluator agent parser and subparsers"""
    evaluator_parser = subparsers.add_parser(
        "evaluator",
        help="Evaluator Agent commands",
        description="""Evaluates TappsCodingAgents framework effectiveness.
        
The Evaluator Agent provides analysis of:
  • Command usage patterns (CLI vs Cursor Skills vs Simple Mode)
  • Workflow adherence (did users follow intended workflows?)
  • Code quality metrics
  • Actionable recommendations for continuous improvement

Use this agent to understand how TappsCodingAgents is being used and identify
opportunities for improvement.""",
    )
    evaluator_subparsers = evaluator_parser.add_subparsers(
        dest="command", help="Evaluator agent subcommand (use 'help' to see all available commands)"
    )

    evaluate_parser = evaluator_subparsers.add_parser(
        "evaluate",
        aliases=["*evaluate"],
        help="Evaluate framework effectiveness",
        description="""Evaluate TappsCodingAgents framework effectiveness.
        
Analyzes:
  • Command usage patterns and statistics
  • Workflow adherence (if workflow_id provided)
  • Code quality metrics
  • Generates actionable recommendations

Example:
  tapps-agents evaluator evaluate
  tapps-agents evaluator evaluate --workflow-id workflow-123
  tapps-agents evaluator evaluate --format markdown --output evaluation.md""",
    )
    evaluate_parser.add_argument(
        "--workflow-id",
        help="Optional workflow ID to evaluate specific workflow execution"
    )
    evaluate_parser.add_argument(
        "--format",
        choices=["json", "text", "markdown"],
        default="markdown",
        help="Output format: 'markdown' for report (default), 'json' for structured data, 'text' for human-readable"
    )
    evaluate_parser.add_argument(
        "--output",
        help="Output file path. If specified, report will be written to this file. Default: .tapps-agents/evaluations/evaluation-{timestamp}.md"
    )

    evaluate_workflow_parser = evaluator_subparsers.add_parser(
        "evaluate-workflow",
        aliases=["*evaluate-workflow"],
        help="Evaluate specific workflow",
        description="""Evaluate a specific workflow execution.
        
Analyzes:
  • Workflow step completion
  • Documentation artifacts created
  • Workflow deviations
  • Quality metrics

Example:
  tapps-agents evaluator evaluate-workflow workflow-123""",
    )
    evaluate_workflow_parser.add_argument(
        "workflow_id",
        help="Workflow ID to evaluate"
    )
    evaluate_workflow_parser.add_argument(
        "--format",
        choices=["json", "text", "markdown"],
        default="markdown",
        help="Output format: 'markdown' for report (default), 'json' for structured data, 'text' for human-readable"
    )
    evaluate_workflow_parser.add_argument(
        "--output",
        help="Output file path. If specified, report will be written to this file. Default: .tapps-agents/evaluations/evaluation-{workflow_id}-{timestamp}.md"
    )

    submit_feedback_parser = evaluator_subparsers.add_parser(
        "submit-feedback",
        aliases=["*submit-feedback"],
        help="Submit external feedback about framework performance",
        description="""Submit feedback about TappsCodingAgents performance from external projects.
        
Allows external projects to provide structured feedback including:
  • Performance ratings (1.0-10.0 scale)
  • Improvement suggestions
  • Optional context (workflow_id, agent_id, task_type)
  • Optional metrics (execution_time_seconds, quality_score, etc.)

Example:
  tapps-agents evaluator submit-feedback \\
    --rating overall=8.5 --rating usability=7.0 \\
    --suggestion "Improve error messages" \\
    --workflow-id workflow-123 --agent-id reviewer
  
  # From JSON file
  tapps-agents evaluator submit-feedback --file feedback.json""",
    )
    submit_feedback_parser.add_argument(
        "--rating",
        action="append",
        dest="ratings",
        metavar="METRIC=VALUE",
        help="Performance rating (can specify multiple: --rating overall=8.5 --rating usability=7.0)"
    )
    submit_feedback_parser.add_argument(
        "--suggestion",
        action="append",
        dest="suggestions",
        metavar="TEXT",
        help="Improvement suggestion (can specify multiple)"
    )
    submit_feedback_parser.add_argument(
        "--workflow-id",
        help="Optional workflow identifier"
    )
    submit_feedback_parser.add_argument(
        "--agent-id",
        help="Optional agent identifier"
    )
    submit_feedback_parser.add_argument(
        "--task-type",
        help="Optional task type (e.g., 'code-review', 'test-generation')"
    )
    submit_feedback_parser.add_argument(
        "--metric",
        action="append",
        dest="metrics",
        metavar="KEY=VALUE",
        help="Optional performance metric (can specify multiple: --metric execution_time_seconds=45.2)"
    )
    submit_feedback_parser.add_argument(
        "--project-id",
        help="Optional project identifier"
    )
    submit_feedback_parser.add_argument(
        "--file",
        help="JSON file with feedback data (alternative to command-line arguments)"
    )

    get_feedback_parser = evaluator_subparsers.add_parser(
        "get-feedback",
        aliases=["*get-feedback"],
        help="Retrieve feedback by ID",
        description="""Retrieve a specific feedback entry by UUID.

Example:
  tapps-agents evaluator get-feedback 550e8400-e29b-41d4-a716-446655440000""",
    )
    get_feedback_parser.add_argument(
        "feedback_id",
        help="Feedback UUID"
    )
    get_feedback_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)"
    )

    list_feedback_parser = evaluator_subparsers.add_parser(
        "list-feedback",
        aliases=["*list-feedback"],
        help="List feedback entries with optional filtering",
        description="""List feedback entries with optional filtering.

Example:
  tapps-agents evaluator list-feedback
  tapps-agents evaluator list-feedback --workflow-id workflow-123
  tapps-agents evaluator list-feedback --start-date 2026-01-01 --end-date 2026-01-31""",
    )
    list_feedback_parser.add_argument(
        "--workflow-id",
        help="Filter by workflow ID"
    )
    list_feedback_parser.add_argument(
        "--agent-id",
        help="Filter by agent ID"
    )
    list_feedback_parser.add_argument(
        "--start-date",
        help="Filter by start date (YYYY-MM-DD)"
    )
    list_feedback_parser.add_argument(
        "--end-date",
        help="Filter by end date (YYYY-MM-DD)"
    )
    list_feedback_parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of entries to return"
    )
    list_feedback_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)"
    )

    evaluator_subparsers.add_parser(
        "help", aliases=["*help"], help="Show evaluator commands"
    )
