"""
Documenter agent parser definitions
"""
import argparse


def add_documenter_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add documenter agent parser and subparsers"""
    documenter_parser = subparsers.add_parser(
        "documenter",
        help="Documenter Agent commands",
        description="""Documentation generation agent.
        
The Documenter Agent creates and maintains documentation:
  • Generate code documentation
  • Create API documentation
  • Update README files
  • Update docstrings
  • Generate documentation in multiple formats

Use this agent to keep documentation up-to-date with your codebase.""",
    )
    documenter_subparsers = documenter_parser.add_subparsers(
        dest="command", help="Documenter agent subcommand (use 'help' to see all available commands)"
    )

    document_parser = documenter_subparsers.add_parser(
        "document",
        aliases=["*document"],
        help="Generate documentation for a file",
        description="""Generate comprehensive documentation for a code file.
        
Creates documentation including:
  • Function and class descriptions
  • Parameter documentation
  • Usage examples
  • Code structure overview
  • Dependencies and requirements

Supports multiple output formats: Markdown, RST, HTML.

Example:
  tapps-agents documenter document src/utils.py
  tapps-agents documenter document src/api.py --output-format html --output-file docs/api.html""",
    )
    document_parser.add_argument("file", help="Path to the source code file to document. The file will be analyzed and comprehensive documentation will be generated.")
    document_parser.add_argument(
        "--output-format", default="markdown", help="Output format for documentation: 'markdown' for Markdown format (default), 'rst' for reStructuredText, 'html' for HTML documentation"
    )
    document_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    document_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    generate_docs_parser = documenter_subparsers.add_parser(
        "generate-docs", 
        aliases=["*generate-docs", "document-api", "*document-api"], 
        help="Generate API documentation from code",
        description="""Generate API documentation from source code.
        
Creates documentation including:
  • API endpoint descriptions
  • Request/response schemas
  • Parameter documentation
  • Authentication requirements
  • Usage examples
  • Error responses

Use this to generate API documentation for REST APIs, GraphQL schemas, or function APIs.""",
    )
    generate_docs_parser.add_argument("file", help="Path to the source code file containing API definitions (e.g., FastAPI routes, Flask endpoints, function definitions)")
    generate_docs_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    generate_docs_parser.add_argument(
        "--output-format", default="markdown", help="Output format for API documentation: 'markdown' for Markdown (default), 'rst' for reStructuredText, 'html' for HTML, 'openapi' for OpenAPI/Swagger YAML"
    )
    generate_docs_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    update_readme_parser = documenter_subparsers.add_parser(
        "update-readme", 
        aliases=["*update-readme"], 
        help="Generate or update project README.md file",
        description="""Generate or update a comprehensive README.md file for your project.
        
Creates documentation including:
  • Project description and purpose
  • Installation instructions
  • Usage examples
  • Configuration options
  • API documentation links
  • Contributing guidelines
  • License information

Analyzes the project structure and codebase to generate accurate, up-to-date documentation.""",
    )
    update_readme_parser.add_argument(
        "--project-root", help="Project root directory path. Defaults to current working directory. README.md will be created/updated in this directory."
    )
    update_readme_parser.add_argument("--context", help="Additional context, notes, or information to include in the README (e.g., special setup requirements, known issues, project history)")

    update_docstrings_parser = documenter_subparsers.add_parser(
        "update-docstrings",
        aliases=["*update-docstrings"],
        help="Update or add docstrings to code functions and classes",
        description="""Update or generate docstrings for functions and classes in code.
        
Analyzes code and:
  • Adds missing docstrings
  • Updates outdated docstrings
  • Ensures consistent format
  • Documents parameters and return values
  • Adds usage examples where appropriate

Use --write-file to automatically update the source file, or review the output first before applying changes.""",
    )
    update_docstrings_parser.add_argument("file", help="Path to the source code file to update with docstrings. All functions and classes without docstrings will have them generated.")
    update_docstrings_parser.add_argument(
        "--docstring-format",
        default="google",
        help="Docstring format style: 'google' for Google-style docstrings (default), 'numpy' for NumPy-style, 'sphinx' for Sphinx-style reStructuredText",
    )
    update_docstrings_parser.add_argument(
        "--write-file", action="store_true", help="Write the updated code with new docstrings back to the source file. Without this flag, updated code is only printed to stdout for review."
    )

    documenter_subparsers.add_parser(
        "help", aliases=["*help"], help="Show documenter commands"
    )

