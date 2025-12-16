"""
Improver agent parser definitions
"""
import argparse


def add_improver_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add improver agent parser and subparsers"""
    improver_parser = subparsers.add_parser("improver", help="Improver Agent commands")
    improver_subparsers = improver_parser.add_subparsers(
        dest="command", help="Commands"
    )

    refactor_improver_parser = improver_subparsers.add_parser(
        "refactor", aliases=["*refactor"], help="Refactor existing code"
    )
    refactor_improver_parser.add_argument("file_path", help="Path to file to refactor")
    refactor_improver_parser.add_argument(
        "--instruction", help="Specific refactoring instructions"
    )

    optimize_parser = improver_subparsers.add_parser(
        "optimize",
        aliases=["*optimize"],
        help="Optimize code for performance or memory",
    )
    optimize_parser.add_argument("file_path", help="Path to file to optimize")
    optimize_parser.add_argument(
        "--type",
        choices=["performance", "memory", "both"],
        default="performance",
        help="Optimization type",
    )

    improve_quality_parser = improver_subparsers.add_parser(
        "improve-quality",
        aliases=["*improve-quality"],
        help="Improve overall code quality",
    )
    improve_quality_parser.add_argument("file_path", help="Path to file to improve")

    improver_subparsers.add_parser(
        "help", aliases=["*help"], help="Show improver commands"
    )

