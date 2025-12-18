"""
Implementer agent parser definitions
"""
import argparse


def add_implementer_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add implementer agent parser and subparsers"""
    implementer_parser = subparsers.add_parser(
        "implementer",
        help="Implementer Agent commands",
        description="""Code generation and implementation agent.
        
The Implementer Agent generates and writes code based on specifications:
  • Generate code from specifications
  • Write code to files
  • Refactor existing code
  • Follow project patterns and conventions
  • Integrate with existing codebase

Use this agent to implement features, create new modules, or refactor
existing code according to your project's standards.""",
    )
    implementer_subparsers = implementer_parser.add_subparsers(
        dest="command", help="Implementer agent subcommand (use 'help' to see all available commands)"
    )

    implement_parser = implementer_subparsers.add_parser(
        "implement",
        aliases=["*implement"],
        help="Generate and write code to file",
        description="""Generate code from a specification and write it to a file.
        
Creates new code or modifies existing files based on your specification.
The agent analyzes the target file and existing codebase to ensure
proper integration and adherence to project patterns.

Example:
  tapps-agents implementer implement "Create a User model with email and name fields" src/models/user.py
  tapps-agents implementer implement "Add authentication endpoint" src/api/auth.py --context "Use JWT tokens\"""",
    )
    implement_parser.add_argument(
        "specification", help="Detailed specification or description of what code to implement. Can be a feature description, function specification, or detailed requirements. Be specific for best results."
    )
    implement_parser.add_argument("file_path", help="Path to the target file where code will be written. If the file exists, code will be integrated with existing content. If it doesn't exist, a new file will be created.")
    implement_parser.add_argument(
        "--context", help="Additional context about the implementation such as existing patterns to follow, dependencies to use, constraints, or integration requirements"
    )
    implement_parser.add_argument(
        "--language",
        default="python",
        help="Programming language for code generation: 'python' (default), 'javascript', 'typescript', 'java', 'go', 'rust', etc. Determines syntax and conventions used.",
    )
    implement_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format: 'json' for structured output with metadata (default), 'text' for plain text code output",
    )

    generate_code_parser = implementer_subparsers.add_parser(
        "generate-code",
        aliases=["*generate-code"],
        help="Generate code without writing to file",
        description="""Generate code from a specification without writing to a file.
        
Useful for:
  • Previewing code before writing
  • Generating code snippets
  • Testing specifications
  • Getting code suggestions

The generated code is returned in the output but not written to disk.

Example:
  tapps-agents implementer generate-code "Create a function to validate email addresses"
  tapps-agents implementer generate-code "Add error handling" --file src/api.py""",
    )
    generate_code_parser.add_argument(
        "specification", help="Code specification or description of what to generate. Describes the functionality, inputs, outputs, and behavior of the code to be generated."
    )
    generate_code_parser.add_argument(
        "--file", help="Optional path to an existing file for context. The agent will analyze this file to understand existing patterns, imports, and structure to ensure generated code integrates well."
    )
    generate_code_parser.add_argument("--context", help="Additional context such as project conventions, framework usage, or specific requirements that should influence code generation")
    generate_code_parser.add_argument(
        "--language", default="python", help="Programming language for code generation: 'python' (default), 'javascript', 'typescript', 'java', 'go', 'rust', etc."
    )
    generate_code_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format: 'json' for structured output with metadata (default), 'text' for plain code output"
    )

    refactor_parser = implementer_subparsers.add_parser(
        "refactor",
        aliases=["*refactor"],
        help="Refactor existing code file",
        description="""Refactor existing code according to instructions.
        
Modifies code in place to:
  • Improve code structure
  • Apply design patterns
  • Fix code smells
  • Improve readability
  • Optimize performance

Example:
  tapps-agents implementer refactor src/utils.py "Extract common logic into helper functions"
  tapps-agents implementer refactor src/api.py "Apply dependency injection pattern\"""",
    )
    refactor_parser.add_argument("file_path", help="Path to the source code file to refactor. The file will be analyzed and refactored according to the instruction.")
    refactor_parser.add_argument("instruction", help="Detailed refactoring instruction describing what changes to make (e.g., 'Extract common logic into helper functions', 'Apply dependency injection pattern', 'Improve error handling'). Be specific about the refactoring goal.")
    refactor_parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format: 'json' for structured output with change descriptions (default), 'text' for plain refactored code"
    )

    implementer_subparsers.add_parser(
        "help", aliases=["*help"], help="Show implementer commands"
    )


