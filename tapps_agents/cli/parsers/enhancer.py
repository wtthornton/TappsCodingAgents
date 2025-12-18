"""
Enhancer agent parser definitions
"""
import argparse


def add_enhancer_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add enhancer agent parser and subparsers"""
    enhancer_parser = subparsers.add_parser(
        "enhancer",
        help="Enhancer Agent commands",
        description="""Prompt enhancement and specification generation agent.
        
The Enhancer Agent transforms simple prompts into comprehensive specifications:
  • Full enhancement pipeline (all stages)
  • Quick enhancement (stages 1-3)
  • Stage-specific enhancement
  • Resume from saved sessions

Use this agent to convert vague requirements into detailed, actionable
specifications for other agents to implement.

Example:
  tapps-agents enhancer enhance "Build a todo app"
  tapps-agents enhancer enhance-quick "Add user authentication\"""",
    )
    enhancer_subparsers = enhancer_parser.add_subparsers(
        dest="command", help="Enhancer agent subcommand (use 'help' to see all available commands)"
    )

    enhance_parser = enhancer_subparsers.add_parser(
        "enhance", 
        aliases=["*enhance"], 
        help="Run full enhancement pipeline (all stages)",
        description="""Execute the complete enhancement pipeline through all stages.
        
The full pipeline includes:
  • Stage 1: Analysis and context gathering
  • Stage 2: Requirements extraction
  • Stage 3: Architecture planning
  • Stage 4: Implementation strategy
  • Stage 5: Testing strategy
  • Stage 6: Documentation planning

This transforms a simple prompt into a comprehensive, actionable specification ready for implementation.""",
    )
    enhance_parser.add_argument("prompt", help="The initial prompt or description to enhance. Can be a simple requirement or vague description - the enhancer will expand it into a detailed specification.")
    enhance_parser.add_argument(
        "--format",
        choices=["markdown", "json", "yaml"],
        default="markdown",
        help="Output format for the enhanced specification: 'markdown' for Markdown format (default), 'json' for structured JSON, 'yaml' for YAML format",
    )
    enhance_parser.add_argument("--output", help="Path to output file where enhanced specification will be saved. If not provided, output is printed to stdout. File extension should match the format.")
    enhance_parser.add_argument("--config", help="Path to custom enhancement configuration file. Allows customization of enhancement stages, prompts, and output structure.")

    enhance_quick_parser = enhancer_subparsers.add_parser(
        "enhance-quick",
        aliases=["*enhance-quick"],
        help="Quick enhancement through stages 1-3 (faster, less detailed)",
        description="""Run quick enhancement through the first three stages only.
        
Includes:
  • Stage 1: Analysis and context gathering
  • Stage 2: Requirements extraction
  • Stage 3: Architecture planning

Skips implementation, testing, and documentation planning stages. Use this when you need a faster enhancement for initial planning or when those stages will be handled separately.""",
    )
    enhance_quick_parser.add_argument("prompt", help="The initial prompt or description to enhance. Will be expanded through the first three enhancement stages.")
    enhance_quick_parser.add_argument(
        "--format",
        choices=["markdown", "json", "yaml"],
        default="markdown",
        help="Output format for the enhanced specification: 'markdown' for Markdown format (default), 'json' for structured JSON, 'yaml' for YAML format",
    )
    enhance_quick_parser.add_argument("--output", help="Path to output file where enhanced specification will be saved. If not provided, output is printed to stdout.")

    enhance_stage_parser = enhancer_subparsers.add_parser(
        "enhance-stage",
        aliases=["*enhance-stage"],
        help="Run a specific enhancement stage individually",
        description="""Execute a single enhancement stage.
        
Available stages:
  • analysis - Context gathering and analysis
  • requirements - Requirements extraction
  • architecture - Architecture planning
  • implementation - Implementation strategy
  • testing - Testing strategy
  • documentation - Documentation planning

Use this to run specific stages or continue from a saved session. Provide either --prompt for a new enhancement or --session-id to continue from a previous session.""",
    )
    enhance_stage_parser.add_argument(
        "stage", help="Name of the enhancement stage to run: 'analysis', 'requirements', 'architecture', 'implementation', 'testing', or 'documentation'"
    )
    enhance_stage_parser.add_argument("--prompt", help="Prompt to enhance (required if --session-id is not provided). Used as input for the specified stage.")
    enhance_stage_parser.add_argument("--session-id", help="Session ID from a previous enhancement session to continue. Allows resuming or re-running a specific stage with existing context.")

    enhance_resume_parser = enhancer_subparsers.add_parser(
        "enhance-resume",
        aliases=["*enhance-resume"],
        help="Resume enhancement pipeline from a saved session",
        description="""Resume the enhancement pipeline from a previously saved session.
        
Loads session state and continues from where it left off. Useful for:
  • Resuming interrupted enhancements
  • Continuing after manual review
  • Re-running stages with modifications

The session ID is provided when you start an enhancement session.""",
    )
    enhance_resume_parser.add_argument("session_id", help="Session ID from a previous enhancement session. Obtain this from the session metadata when you start an enhancement.")

    enhancer_subparsers.add_parser(
        "help", aliases=["*help"], help="Show enhancer commands"
    )

