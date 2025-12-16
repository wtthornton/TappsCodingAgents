"""
Debugger agent parser definitions
"""
import argparse


def add_debugger_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add debugger agent parser and subparsers"""
    debugger_parser = subparsers.add_parser("debugger", help="Debugger Agent commands")
    debugger_subparsers = debugger_parser.add_subparsers(
        dest="command", help="Commands"
    )

    debug_parser = debugger_subparsers.add_parser(
        "debug", aliases=["*debug"], help="Debug an error or issue"
    )
    debug_parser.add_argument("error_message", help="Error message to debug")
    debug_parser.add_argument("--file", help="File path where error occurred")
    debug_parser.add_argument(
        "--line", type=int, help="Line number where error occurred"
    )
    debug_parser.add_argument("--stack-trace", help="Stack trace")

    analyze_error_parser = debugger_subparsers.add_parser(
        "analyze-error",
        aliases=["*analyze-error"],
        help="Analyze error message and stack trace",
    )
    analyze_error_parser.add_argument("error_message", help="Error message")
    analyze_error_parser.add_argument("--stack-trace", help="Stack trace")
    analyze_error_parser.add_argument(
        "--code-context", help="Code context around error"
    )

    trace_parser = debugger_subparsers.add_parser(
        "trace", aliases=["*trace"], help="Trace code execution path"
    )
    trace_parser.add_argument("file", help="File path to trace")
    trace_parser.add_argument("--function", help="Function name to trace from")
    trace_parser.add_argument("--line", type=int, help="Line number to trace from")

    debugger_subparsers.add_parser(
        "help", aliases=["*help"], help="Show debugger commands"
    )

