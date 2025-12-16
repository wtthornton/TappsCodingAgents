"""
Documenter agent parser definitions
"""
import argparse


def add_documenter_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add documenter agent parser and subparsers"""
    documenter_parser = subparsers.add_parser(
        "documenter", help="Documenter Agent commands"
    )
    documenter_subparsers = documenter_parser.add_subparsers(
        dest="command", help="Commands"
    )

    document_parser = documenter_subparsers.add_parser(
        "document", aliases=["*document"], help="Generate documentation for a file"
    )
    document_parser.add_argument("file", help="Source code file path")
    document_parser.add_argument(
        "--output-format", default="markdown", help="Output format (markdown/rst/html)"
    )
    document_parser.add_argument("--output-file", help="Output file path")

    generate_docs_parser = documenter_subparsers.add_parser(
        "generate-docs", aliases=["*generate-docs"], help="Generate API documentation"
    )
    generate_docs_parser.add_argument("file", help="Source code file path")
    generate_docs_parser.add_argument(
        "--output-format", default="markdown", help="Output format"
    )

    update_readme_parser = documenter_subparsers.add_parser(
        "update-readme", aliases=["*update-readme"], help="Generate or update README.md"
    )
    update_readme_parser.add_argument(
        "--project-root", help="Project root directory (default: current directory)"
    )
    update_readme_parser.add_argument("--context", help="Additional context for README")

    update_docstrings_parser = documenter_subparsers.add_parser(
        "update-docstrings",
        aliases=["*update-docstrings"],
        help="Update docstrings in code",
    )
    update_docstrings_parser.add_argument("file", help="Source code file path")
    update_docstrings_parser.add_argument(
        "--docstring-format",
        default="google",
        help="Docstring format (google/numpy/sphinx)",
    )
    update_docstrings_parser.add_argument(
        "--write-file", action="store_true", help="Write updated code back to file"
    )

    documenter_subparsers.add_parser(
        "help", aliases=["*help"], help="Show documenter commands"
    )

