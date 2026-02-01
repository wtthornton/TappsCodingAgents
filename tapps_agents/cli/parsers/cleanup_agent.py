"""
Cleanup Agent parser definitions
"""
import argparse


def add_cleanup_agent_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add cleanup-agent parser and subparsers."""
    cleanup_agent_parser = subparsers.add_parser(
        "cleanup-agent",
        help="Project Cleanup Agent commands",
        description="""Project structure analysis and intelligent cleanup agent.

The Cleanup Agent helps keep projects clean by:
  - Analyzing project structure for cleanup opportunities
  - Detecting duplicate files and content
  - Identifying outdated documentation
  - Enforcing naming conventions (kebab-case)
  - Generating cleanup plans with rationale
  - Executing cleanup operations safely with backups

Use this agent for guided project and docs cleanup after heavy development.""",
    )
    cleanup_subparsers = cleanup_agent_parser.add_subparsers(
        dest="command",
        help="Cleanup agent subcommand (use 'help' to see all available commands)",
    )

    # Analyze command
    analyze_parser = cleanup_subparsers.add_parser(
        "analyze",
        aliases=["*analyze"],
        help="Analyze project structure for cleanup opportunities",
        description="""Analyze project structure to identify cleanup opportunities.

Scans the specified path and detects:
  - Duplicate files (by content hash)
  - Outdated files (not modified in 90+ days)
  - Naming convention violations
  - Files with no references

Example:
  tapps-agents cleanup-agent analyze --path ./docs --pattern "*.md"
  tapps-agents cleanup-agent analyze --output analysis.json""",
    )
    analyze_parser.add_argument(
        "--path",
        help="Path to analyze (defaults to ./docs). Can be any directory in the project.",
    )
    analyze_parser.add_argument(
        "--pattern",
        default="*.md",
        help="File pattern to match (default: *.md). Supports glob patterns.",
    )
    analyze_parser.add_argument(
        "--output",
        help="Output file for analysis report (JSON format). If not specified, displays summary.",
    )
    analyze_parser.add_argument(
        "--format",
        choices=["json", "text", "markdown"],
        default="json",
        help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown",
    )

    # Plan command
    plan_parser = cleanup_subparsers.add_parser(
        "plan",
        aliases=["*plan"],
        help="Generate cleanup plan from analysis",
        description="""Generate a cleanup plan with prioritized actions.

Creates a plan based on analysis that includes:
  - File categorization (keep, archive, delete, merge, rename)
  - Priority levels (high, medium, low)
  - Safety levels (safe, moderate, risky)
  - Rationale for each action
  - Estimated space savings

Example:
  tapps-agents cleanup-agent plan --analysis-file analysis.json
  tapps-agents cleanup-agent plan --path ./docs --output cleanup-plan.json""",
    )
    plan_parser.add_argument(
        "--analysis-file",
        help="Path to analysis report JSON. If not provided, runs fresh analysis.",
    )
    plan_parser.add_argument(
        "--path",
        help="Path to analyze if no analysis file provided (defaults to ./docs).",
    )
    plan_parser.add_argument(
        "--pattern",
        default="*.md",
        help="File pattern if running fresh analysis (default: *.md).",
    )
    plan_parser.add_argument(
        "--output",
        help="Output file for cleanup plan (JSON format).",
    )
    plan_parser.add_argument(
        "--format",
        choices=["json", "text", "markdown"],
        default="json",
        help="Output format (default: json).",
    )

    # Execute command
    execute_parser = cleanup_subparsers.add_parser(
        "execute",
        aliases=["*execute"],
        help="Execute cleanup plan (dry-run by default)",
        description="""Execute cleanup operations from a plan.

Performs cleanup actions with safety measures:
  - Dry-run mode by default (preview changes)
  - Optional backup creation before execution
  - Reference updating for renamed/moved files
  - Transaction logging for rollback capability

Example:
  tapps-agents cleanup-agent execute --plan-file cleanup-plan.json --dry-run
  tapps-agents cleanup-agent execute --plan-file cleanup-plan.json --no-dry-run --backup""",
    )
    execute_parser.add_argument(
        "--plan-file",
        help="Path to cleanup plan JSON. If not provided, generates plan from analysis.",
    )
    execute_parser.add_argument(
        "--path",
        help="Path to analyze if no plan file provided (defaults to ./docs).",
    )
    execute_parser.add_argument(
        "--pattern",
        default="*.md",
        help="File pattern if running fresh (default: *.md).",
    )
    execute_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview changes without executing (default: True).",
    )
    execute_parser.add_argument(
        "--no-dry-run",
        action="store_true",
        help="Execute changes for real (disables dry-run).",
    )
    execute_parser.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Create backup before execution (default: True).",
    )
    execute_parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup creation (not recommended).",
    )
    execute_parser.add_argument(
        "--format",
        choices=["json", "text", "markdown"],
        default="json",
        help="Output format (default: json).",
    )

    # Run command (full workflow)
    run_parser = cleanup_subparsers.add_parser(
        "run",
        aliases=["*run"],
        help="Run full cleanup workflow (analyze, plan, execute)",
        description="""Run the complete cleanup workflow in one command.

Executes all steps:
  1. Analyze project structure
  2. Generate cleanup plan
  3. Execute cleanup operations

By default runs in dry-run mode with backups enabled.

Example:
  tapps-agents cleanup-agent run --path ./docs --dry-run
  tapps-agents cleanup-agent run --path ./docs --no-dry-run --backup""",
    )
    run_parser.add_argument(
        "--path",
        help="Path to analyze (defaults to ./docs).",
    )
    run_parser.add_argument(
        "--pattern",
        default="*.md",
        help="File pattern to match (default: *.md).",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview changes without executing (default: True).",
    )
    run_parser.add_argument(
        "--no-dry-run",
        action="store_true",
        help="Execute changes for real (disables dry-run).",
    )
    run_parser.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Create backup before execution (default: True).",
    )
    run_parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup creation (not recommended).",
    )
    run_parser.add_argument(
        "--format",
        choices=["json", "text", "markdown"],
        default="json",
        help="Output format (default: json).",
    )

    # Help command
    cleanup_subparsers.add_parser(
        "help",
        aliases=["*help"],
        help="Show cleanup agent commands",
    )
