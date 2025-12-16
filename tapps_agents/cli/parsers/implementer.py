"""
Implementer agent parser definitions
"""
import argparse


def add_implementer_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add implementer agent parser and subparsers"""
    implementer_parser = subparsers.add_parser(
        "implementer", help="Implementer Agent commands"
    )
    implementer_subparsers = implementer_parser.add_subparsers(
        dest="command", help="Commands"
    )

    implement_parser = implementer_subparsers.add_parser(
        "implement", aliases=["*implement"], help="Generate and write code to file"
    )
    implement_parser.add_argument(
        "specification", help="Code specification/description"
    )
    implement_parser.add_argument("file_path", help="Target file path")
    implement_parser.add_argument("--context", help="Additional context")
    implement_parser.add_argument(
        "--language", default="python", help="Programming language"
    )
    implement_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    generate_code_parser = implementer_subparsers.add_parser(
        "generate-code",
        aliases=["*generate-code"],
        help="Generate code (no file write)",
    )
    generate_code_parser.add_argument(
        "specification", help="Code specification/description"
    )
    generate_code_parser.add_argument(
        "--file", help="Optional target file path for context"
    )
    generate_code_parser.add_argument("--context", help="Additional context")
    generate_code_parser.add_argument(
        "--language", default="python", help="Programming language"
    )
    generate_code_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    refactor_parser = implementer_subparsers.add_parser(
        "refactor", aliases=["*refactor"], help="Refactor existing code file"
    )
    refactor_parser.add_argument("file_path", help="Path to file to refactor")
    refactor_parser.add_argument("instruction", help="Refactoring instruction")
    refactor_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )

    implementer_subparsers.add_parser(
        "help", aliases=["*help"], help="Show implementer commands"
    )

