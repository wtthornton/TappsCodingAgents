"""
Improver agent parser definitions
"""
import argparse


def add_improver_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add improver agent parser and subparsers"""
    improver_parser = subparsers.add_parser(
        "improver",
        help="Improver Agent commands",
        description="""Code improvement and optimization agent.
        
The Improver Agent enhances existing code:
  • Refactor code for better structure
  • Optimize performance and memory usage
  • Improve overall code quality
  • Apply best practices
  • Reduce technical debt

Use this agent to improve existing code without changing functionality.""",
    )
    improver_subparsers = improver_parser.add_subparsers(
        dest="command", help="Improver agent subcommand (use 'help' to see all available commands)"
    )

    refactor_improver_parser = improver_subparsers.add_parser(
        "refactor", 
        aliases=["*refactor"], 
        help="Refactor existing code to improve structure and maintainability",
        description="""Refactor code to improve structure, readability, and maintainability.
        
Improves code by:
  • Extracting common patterns
  • Reducing complexity
  • Improving naming and organization
  • Applying design patterns
  • Reducing duplication

Use --instruction to specify particular refactoring goals, or let the agent identify improvement opportunities automatically.""",
    )
    refactor_improver_parser.add_argument("file_path", help="Path to the source code file to refactor. The file will be analyzed for improvement opportunities.")
    refactor_improver_parser.add_argument(
        "--instruction", help="Optional specific refactoring instructions (e.g., 'extract methods', 'simplify conditionals', 'improve error handling'). If not provided, the agent will identify and apply general improvements."
    )
    refactor_improver_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    refactor_improver_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")
    refactor_improver_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    optimize_parser = improver_subparsers.add_parser(
        "optimize",
        aliases=["*optimize"],
        help="Optimize code for performance, memory usage, or both",
        description="""Optimize code for better performance or reduced memory usage.
        
Performance optimizations:
  • Algorithm improvements
  • Caching strategies
  • Loop optimizations
  • Lazy evaluation
  • Parallel processing opportunities

Memory optimizations:
  • Reducing object allocations
  • Memory-efficient data structures
  • Garbage collection improvements
  • Resource cleanup

Use --type to specify the optimization focus.""",
    )
    optimize_parser.add_argument("file_path", help="Path to the source code file to optimize. The file will be analyzed for optimization opportunities.")
    optimize_parser.add_argument(
        "--type",
        choices=["performance", "memory", "both"],
        default="performance",
        help="Type of optimization to focus on: 'performance' for speed improvements (default), 'memory' for memory usage reduction, 'both' for comprehensive optimization",
    )
    optimize_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    optimize_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")
    optimize_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    improve_quality_parser = improver_subparsers.add_parser(
        "improve-quality",
        aliases=["*improve-quality"],
        help="Improve overall code quality through comprehensive analysis",
        description="""Perform comprehensive code quality improvements.
        
Addresses multiple quality aspects:
  • Code structure and organization
  • Readability and maintainability
  • Best practices and patterns
  • Error handling
  • Documentation
  • Testability

This is a general quality improvement that addresses multiple concerns simultaneously.""",
    )
    improve_quality_parser.add_argument("file_path", help="Path to the source code file to improve. The file will be comprehensively analyzed and improved across multiple quality dimensions.")
    improve_quality_parser.add_argument(
        "--focus",
        help="Comma-separated list of quality aspects to focus on (e.g., 'security, maintainability, type-safety'). If not provided, performs comprehensive quality improvement.",
    )
    improve_quality_parser.add_argument(
        "--auto-apply",
        action="store_true",
        help="Automatically apply improvements to the file. Creates a backup before modifying. Returns a diff of changes made and runs verification review.",
    )
    improve_quality_parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview improvements as a diff without modifying the file. Shows what changes would be made without applying them.",
    )
    improve_quality_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    improve_quality_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")
    improve_quality_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    improver_subparsers.add_parser(
        "help", aliases=["*help"], help="Show improver commands"
    )

