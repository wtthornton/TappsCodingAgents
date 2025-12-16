"""
Enhancer agent parser definitions
"""
import argparse


def add_enhancer_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add enhancer agent parser and subparsers"""
    enhancer_parser = subparsers.add_parser("enhancer", help="Enhancer Agent commands")
    enhancer_subparsers = enhancer_parser.add_subparsers(
        dest="command", help="Commands"
    )

    enhance_parser = enhancer_subparsers.add_parser(
        "enhance", aliases=["*enhance"], help="Full enhancement pipeline"
    )
    enhance_parser.add_argument("prompt", help="Prompt to enhance")
    enhance_parser.add_argument(
        "--format",
        choices=["markdown", "json", "yaml"],
        default="markdown",
        help="Output format",
    )
    enhance_parser.add_argument("--output", help="Output file path")
    enhance_parser.add_argument("--config", help="Enhancement config file path")

    enhance_quick_parser = enhancer_subparsers.add_parser(
        "enhance-quick",
        aliases=["*enhance-quick"],
        help="Quick enhancement (stages 1-3)",
    )
    enhance_quick_parser.add_argument("prompt", help="Prompt to enhance")
    enhance_quick_parser.add_argument(
        "--format",
        choices=["markdown", "json", "yaml"],
        default="markdown",
        help="Output format",
    )
    enhance_quick_parser.add_argument("--output", help="Output file path")

    enhance_stage_parser = enhancer_subparsers.add_parser(
        "enhance-stage",
        aliases=["*enhance-stage"],
        help="Run a specific enhancement stage",
    )
    enhance_stage_parser.add_argument(
        "stage", help="Stage to run (analysis, requirements, architecture, etc.)"
    )
    enhance_stage_parser.add_argument("--prompt", help="Prompt to enhance")
    enhance_stage_parser.add_argument("--session-id", help="Session ID to continue")

    enhance_resume_parser = enhancer_subparsers.add_parser(
        "enhance-resume",
        aliases=["*enhance-resume"],
        help="Resume enhancement from a specific stage",
    )
    enhance_resume_parser.add_argument("session_id", help="Session ID to resume")

    enhancer_subparsers.add_parser(
        "help", aliases=["*help"], help="Show enhancer commands"
    )

