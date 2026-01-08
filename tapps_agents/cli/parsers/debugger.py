"""
Debugger agent parser definitions
"""
import argparse


def add_debugger_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add debugger agent parser and subparsers"""
    debugger_parser = subparsers.add_parser(
        "debugger",
        help="Debugger Agent commands",
        description="""Error debugging and code analysis agent.
        
The Debugger Agent helps diagnose and fix issues:
  • Debug errors and exceptions
  • Analyze stack traces
  • Trace code execution paths
  • Identify root causes
  • Suggest fixes

Use this agent when encountering bugs or unexpected behavior in your code.""",
    )
    debugger_subparsers = debugger_parser.add_subparsers(
        dest="command", help="Debugger agent subcommand (use 'help' to see all available commands)"
    )

    debug_parser = debugger_subparsers.add_parser(
        "debug",
        aliases=["*debug"],
        help="Debug an error or issue",
        description="""Debug errors and issues in your code.
        
Analyzes error messages, stack traces, and code context to:
  • Identify root causes
  • Suggest fixes
  • Explain error mechanisms
  • Provide prevention strategies

Example:
  tapps-agents debugger debug "KeyError: 'user_id'" --file src/api.py --line 42
  tapps-agents debugger debug "Connection timeout" --stack-trace "traceback.txt\"""",
    )
    debug_parser.add_argument("error_message", help="The error message or exception text to debug. Include the full error message for best results.")
    debug_parser.add_argument("--file", help="Path to the source code file where the error occurred. Helps provide context-aware debugging.")
    debug_parser.add_argument(
        "--line", type=int, help="Line number in the source file where the error occurred. Combined with --file, provides precise error location."
    )
    debug_parser.add_argument("--stack-trace", help="Full stack trace from the error. Can be a file path or the stack trace text. Provides execution context for better debugging.")
    debug_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    debug_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")
    debug_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    analyze_error_parser = debugger_subparsers.add_parser(
        "analyze-error",
        aliases=["*analyze-error"],
        help="Perform detailed analysis of error message and stack trace",
        description="""Analyze error messages and stack traces to identify root causes.
        
Provides:
  • Error type and category identification
  • Root cause analysis
  • Execution path leading to error
  • Variable state analysis
  • Suggested fixes
  • Prevention strategies

Use this for in-depth error analysis when you have both error message and stack trace available.""",
    )
    analyze_error_parser.add_argument("error_message", help="The error message or exception text to analyze. Include the complete error message.")
    analyze_error_parser.add_argument("--stack-trace", help="Full stack trace from the error. Can be a file path containing the stack trace or the stack trace text itself.")
    analyze_error_parser.add_argument(
        "--code-context", help="Code context around the error location (e.g., function code, surrounding lines). Helps provide more accurate analysis by understanding the code structure."
    )
    analyze_error_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    analyze_error_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")
    analyze_error_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    trace_parser = debugger_subparsers.add_parser(
        "trace", 
        aliases=["*trace"], 
        help="Trace code execution path and control flow",
        description="""Trace code execution path to understand control flow and identify issues.
        
Analyzes:
  • Function call sequences
  • Control flow paths
  • Variable state changes
  • Conditional branches taken
  • Loop iterations
  • Exception handling paths

Use this to understand how code executes and identify unexpected execution paths or logic errors.""",
    )
    trace_parser.add_argument("file", help="Path to the source code file to trace. The file will be analyzed to determine execution paths.")
    trace_parser.add_argument("--function", help="Name of the function to start tracing from. If not provided, traces from the entry point of the file.")
    trace_parser.add_argument("--line", type=int, help="Line number to start tracing from. Useful for tracing from a specific point in the code.")
    trace_parser.add_argument("--output", help="Output file path. If specified, results will be written to this file instead of stdout. Format is determined by file extension or --format option.")
    trace_parser.add_argument("--format", choices=["json", "text", "markdown"], default="json", help="Output format: 'json' for structured data (default), 'text' for human-readable, 'markdown' for markdown format")
    trace_parser.add_argument(
        "--verbose-output",
        action="store_true",
        help="Include all verbose debug data in output. By default, output is compacted to prevent Cursor terminal overflow.",
    )

    debugger_subparsers.add_parser(
        "help", aliases=["*help"], help="Show debugger commands"
    )

