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

    evaluator_subparsers.add_parser(
        "help", aliases=["*help"], help="Show evaluator commands"
    )
