"""
Main CLI entry point
"""
import argparse
import asyncio
import os
import sys
from collections.abc import Callable

from .exit_codes import ExitCode

# Try to import version, with fallback to importlib.metadata
try:
    from .. import __version__ as PACKAGE_VERSION
except (ImportError, AttributeError):
    # Fallback: use importlib.metadata (standard library, Python 3.8+)
    try:
        from importlib.metadata import version
        PACKAGE_VERSION = version("tapps-agents")
    except Exception:
        # Last resort: try reading from __init__.py directly
        try:
            import importlib.util
            import pathlib
            init_path = pathlib.Path(__file__).parent.parent / "__init__.py"
            if init_path.exists():
                spec = importlib.util.spec_from_file_location("tapps_agents_init", init_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    PACKAGE_VERSION = getattr(module, "__version__", "unknown")
                else:
                    PACKAGE_VERSION = "unknown"
            else:
                PACKAGE_VERSION = "unknown"
        except Exception:
            PACKAGE_VERSION = "unknown"
from .commands import (
    analyst,
    architect,
    cleanup_agent,
    debugger,
    designer,
    documenter,
    enhancer,
    evaluator,
    implementer,
    improver,
    learning,
    observability,
    ops,
    orchestrator,
    planner,
    reviewer,
    simple_mode,
    tester,
    top_level,
)
from .commands import (
    task as task_cmd,
)
from .feedback import FeedbackManager, ProgressMode, VerbosityLevel

# Import all parser registration functions
from .parsers import (
    analyst as analyst_parsers,
)
from .parsers import (
    architect as architect_parsers,
)
from .parsers import (
    cleanup_agent as cleanup_agent_parsers,
)
from .parsers import (
    debugger as debugger_parsers,
)
from .parsers import (
    designer as designer_parsers,
)
from .parsers import (
    documenter as documenter_parsers,
)
from .parsers import (
    enhancer as enhancer_parsers,
)
from .parsers import (
    evaluator as evaluator_parsers,
)
from .parsers import (
    implementer as implementer_parsers,
)
from .parsers import (
    improver as improver_parsers,
)
from .parsers import (
    ops as ops_parsers,
)
from .parsers import (
    orchestrator as orchestrator_parsers,
)
from .parsers import (
    planner as planner_parsers,
)
from .parsers import (
    reviewer as reviewer_parsers,
)
from .parsers import (
    tester as tester_parsers,
)
from .parsers import (
    top_level as top_level_parsers,
)


def _reorder_global_flags(argv: list[str]) -> list[str]:
    """
    Allow global flags to appear anywhere (common modern CLI UX).

    Argparse only supports global flags before the subcommand. Users frequently type:
      tapps-agents doctor --no-progress
    so we hoist known global flags to the front before parsing.
    """

    hoisted: list[str] = []
    rest: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]

        if a in {"--quiet", "-q", "--verbose", "-v", "--no-progress"}:
            hoisted.append(a)
            i += 1
            continue

        if a.startswith("--progress="):
            hoisted.append(a)
            i += 1
            continue

        if a == "--progress":
            # Keep the value if present; argparse will validate choices later.
            if i + 1 < len(argv):
                hoisted.extend([a, argv[i + 1]])
                i += 2
            else:
                hoisted.append(a)
                i += 1
            continue

        rest.append(a)
        i += 1

    return hoisted + rest


def create_root_parser() -> argparse.ArgumentParser:
    """
    Create the root ArgumentParser for the TappsCodingAgents CLI.
    
    Sets up the main parser with version information and helpful epilog
    showing common usage examples and shortcuts.
    
    Returns:
        Configured ArgumentParser instance ready for subparser registration.
        
    Example:
        >>> parser = create_root_parser()
        >>> parser.parse_args(['--version'])
    """
    parser = argparse.ArgumentParser(
        description="""TappsCodingAgents CLI - AI Coding Agents Framework

A comprehensive framework for defining, configuring, and orchestrating AI coding agents
with 14 workflow agents, industry experts, and full Cursor AI integration.

Key Features:
  • 14 Workflow Agents: Analyst, Architect, Debugger, Designer, Documenter, Enhancer,
    Evaluator, Implementer, Improver, Ops, Orchestrator, Planner, Reviewer, Tester
  • Industry Experts: Domain-specific knowledge with weighted decision-making
  • Workflow Presets: Rapid development, full SDLC, bug fixes, quality improvement
  • Code Quality Tools: Scoring, linting, type checking, duplication detection
  • Cursor Integration: Skills and natural language commands

For detailed documentation, visit: https://github.com/your-repo/docs""",
        epilog="""QUICK START COMMANDS:
  create <description>     Create a new project from description (PRIMARY USE CASE)
  score <file>             Score a code file (shortcut for 'reviewer score')
  init                     Initialize project (Cursor Rules + workflow presets)
  workflow <preset>         Run preset workflows (rapid, full, fix, quality, hotfix)
  doctor                   Validate local environment and tools
  setup-experts            Interactive expert setup wizard

ALSO: simple-mode status | cleanup workflow-docs | health check | health overview | health usage dashboard | beads ready | cursor verify

WORKFLOW PRESETS:
  rapid / feature          Rapid development for sprint work and features
  full / enterprise        Full SDLC pipeline for complete lifecycle management
  fix / refactor           Maintenance and bug fixing workflows
  quality / improve         Quality improvement and code review cycles
  hotfix / urgent          Quick fixes for urgent production bugs

AGENT COMMANDS:
  Use 'tapps-agents <agent> help' to see available commands for each agent:
  • analyst      - Requirements gathering, stakeholder analysis, tech research
  • architect    - System design, architecture diagrams, tech selection
  • debugger     - Error debugging, stack trace analysis, code tracing
  • designer     - API design, data models, UI/UX design, wireframes
  • documenter   - Generate documentation, update README, docstrings
  • enhancer     - Transform simple prompts into comprehensive specifications
  • evaluator    - Framework effectiveness evaluation and usage analysis
  • implementer  - Code generation, refactoring, file writing
  • improver     - Code refactoring, performance optimization, quality improvement
  • ops          - Security scanning, compliance checks, deployment
  • orchestrator - Workflow management, step coordination, gate decisions
  • planner      - Create plans, user stories, task breakdowns
  • reviewer     - Code review, scoring, linting, type checking, reports
  • tester       - Generate and run tests, test coverage

EXAMPLES:
  # Create a new project
  tapps-agents create "Build a task management web app with React and FastAPI"
  
  # Score code quality
  tapps-agents score src/main.py
  
  # Initialize project setup
  tapps-agents init
  
  # Run rapid development workflow
  tapps-agents workflow rapid --prompt "Add user authentication"
  
  # Review code with detailed analysis
  tapps-agents reviewer review src/app.py --format json
  
  # Generate tests
  tapps-agents tester test src/utils.py
  
  # Get workflow recommendation
  tapps-agents workflow recommend
  
  # Check environment
  tapps-agents doctor

For more information on a specific command, use:
  tapps-agents <command> --help
  tapps-agents <agent> help""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {PACKAGE_VERSION}",
        help="Show version and exit",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_const",
        const="quiet",
        dest="verbosity",
        help="Quiet mode: only show errors and final results",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_const",
        const="verbose",
        dest="verbosity",
        help="Verbose mode: show detailed debugging information",
    )
    parser.add_argument(
        "--progress",
        choices=[m.value for m in ProgressMode],
        default=None,
        help=(
            "Progress UI mode: auto (default), rich (animated), plain (single-line), off (disabled). "
            "You can also set TAPPS_PROGRESS=auto|rich|plain|off or TAPPS_NO_PROGRESS=1."
        ),
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress UI (same as --progress off)",
    )
    return parser


def register_all_parsers(parser: argparse.ArgumentParser) -> None:
    """
    Register all agent and top-level command subparsers.
    
    This function sets up the complete command structure by registering:
    - Agent parsers (reviewer, planner, implementer, tester, etc.)
    - Top-level command parsers (create, init, workflow, score, etc.)
    
    Args:
        parser: Root ArgumentParser to attach subparsers to.
        
    Note:
        This must be called after create_root_parser() and before parsing arguments.
    """
    subparsers = parser.add_subparsers(dest="agent", help="Agent or command to use")

    # Register agent parsers
    reviewer_parsers.add_reviewer_parser(subparsers)
    planner_parsers.add_planner_parser(subparsers)
    implementer_parsers.add_implementer_parser(subparsers)
    tester_parsers.add_tester_parser(subparsers)
    debugger_parsers.add_debugger_parser(subparsers)
    documenter_parsers.add_documenter_parser(subparsers)
    orchestrator_parsers.add_orchestrator_parser(subparsers)
    analyst_parsers.add_analyst_parser(subparsers)
    architect_parsers.add_architect_parser(subparsers)
    designer_parsers.add_designer_parser(subparsers)
    improver_parsers.add_improver_parser(subparsers)
    ops_parsers.add_ops_parser(subparsers)
    enhancer_parsers.add_enhancer_parser(subparsers)
    evaluator_parsers.add_evaluator_parser(subparsers)
    cleanup_agent_parsers.add_cleanup_agent_parser(subparsers)

    # Register top-level parsers
    top_level_parsers.add_top_level_parsers(subparsers)


def _get_agent_command_handlers() -> dict[str, Callable[[argparse.Namespace], None]]:
    """
    Get dictionary mapping agent names to their command handlers.
    
    Returns:
        Dictionary mapping agent names to handler functions
    """
    return {
        "reviewer": reviewer.handle_reviewer_command,
        "planner": planner.handle_planner_command,
        "implementer": implementer.handle_implementer_command,
        "tester": tester.handle_tester_command,
        "debugger": debugger.handle_debugger_command,
        "documenter": documenter.handle_documenter_command,
        "orchestrator": orchestrator.handle_orchestrator_command,
        "analyst": analyst.handle_analyst_command,
        "architect": architect.handle_architect_command,
        "designer": designer.handle_designer_command,
        "improver": improver.handle_improver_command,
        "ops": ops.handle_ops_command,
        "enhancer": enhancer.handle_enhancer_command,
        "evaluator": evaluator.handle_evaluator_command,
        "cleanup-agent": cleanup_agent.handle_cleanup_agent_command,
    }


def _get_top_level_command_handlers() -> dict[str, Callable[[argparse.Namespace], None]]:
    """
    Get dictionary mapping top-level command names to their handlers.
    
    Returns:
        Dictionary mapping command names to handler functions
    """
    return {
        "create": top_level.handle_create_command,
        "init": top_level.handle_init_command,
        "generate-rules": top_level.handle_generate_rules_command,
        "workflow": top_level.handle_workflow_command,
        "score": top_level.handle_score_command,
        "status": top_level.handle_status_command,
        "doctor": top_level.handle_doctor_command,
        "docs": top_level.handle_docs_command,
        "install-dev": top_level.handle_install_dev_command,
        "customize": top_level.handle_customize_command,
        "commands": top_level.handle_commands_command,
        "skill": top_level.handle_skill_command,
        "skill-template": top_level.handle_skill_template_command,
        "setup-experts": top_level.handle_setup_experts_command,
        "cursor": top_level.handle_cursor_command,
        "beads": top_level.handle_beads_command,
        "task": task_cmd.handle_task_command,
        "continuous-bug-fix": top_level.handle_continuous_bug_fix_command,
        "bug-fix-continuous": top_level.handle_continuous_bug_fix_command,
        "brownfield": top_level.handle_brownfield_command,
    }


def _handle_cleanup_command(args: argparse.Namespace) -> None:
    """Handle cleanup command with sub-commands."""
    cleanup_type = getattr(args, "cleanup_type", None)
    if cleanup_type == "workflow-docs":
        top_level.handle_cleanup_workflow_docs_command(args)
    elif cleanup_type == "sessions":
        top_level.handle_cleanup_sessions_command(args)
    elif cleanup_type == "epic-state":
        from .commands.epic import handle_cleanup_epic_state_command
        handle_cleanup_epic_state_command(args)
    elif cleanup_type == "all":
        top_level.handle_cleanup_all_command(args)
        # Also cleanup epic-state as part of "all"
        from .commands.epic import handle_cleanup_epic_state_command
        handle_cleanup_epic_state_command(args)
    else:
        print(f"Unknown cleanup type: {cleanup_type}", file=sys.stderr)
        print("Use 'tapps-agents cleanup --help' for available cleanup operations", file=sys.stderr)
        sys.exit(ExitCode.GENERAL_ERROR)


def _handle_epic_command(args: argparse.Namespace) -> None:
    """Handle epic command with sub-commands."""
    from .commands.epic import handle_epic_command
    handle_epic_command(args)


def _handle_expert_command(args: argparse.Namespace) -> None:
    """Handle expert command with sub-commands."""
    from .commands.expert import handle_expert_command
    handle_expert_command(args)


def _handle_observability_command(args: argparse.Namespace) -> None:
    """Handle observability command with sub-commands."""
    from pathlib import Path
    
    project_root = Path.cwd()
    command = getattr(args, "observability_command", None)
    
    observability_handlers = {
        "dashboard": lambda: observability.handle_observability_dashboard_command(
            workflow_id=getattr(args, "workflow_id", None),
            output_format=getattr(args, "format", "text"),
            output_file=getattr(args, "output", None),
            project_root=project_root,
        ),
        "graph": lambda: observability.handle_observability_graph_command(
            workflow_id=args.workflow_id,
            output_format=getattr(args, "format", "dot"),
            output_file=getattr(args, "output", None),
            project_root=project_root,
        ),
        "otel": lambda: observability.handle_observability_otel_command(
            workflow_id=args.workflow_id,
            output_file=getattr(args, "output", None),
            project_root=project_root,
        ),
    }
    
    handler = observability_handlers.get(command)
    if handler:
        handler()
    else:
        print(f"Unknown observability subcommand: {command}")
        sys.exit(ExitCode.GENERAL_ERROR)


def _handle_health_command(args: argparse.Namespace) -> None:
    """Handle health command with sub-commands."""
    from pathlib import Path

    from .commands import health

    if not hasattr(args, "command"):
        return
    
    health_handlers = {
        "check": lambda: health.handle_health_check_command(
            check_name=getattr(args, "check", None),
            output_format=getattr(args, "format", "text"),
            save=getattr(args, "save", True),
        ),
        "dashboard": lambda: health.handle_health_dashboard_command(
            output_format=getattr(args, "format", "text"),
        ),
        "show": lambda: health.handle_health_dashboard_command(
            output_format=getattr(args, "format", "text"),
        ),
        "metrics": lambda: health.handle_health_metrics_command(
            check_name=getattr(args, "check_name", None),
            status=getattr(args, "status", None),
            days=getattr(args, "days", 30),
            output_format=getattr(args, "format", "text"),
        ),
        "trends": lambda: health.handle_health_trends_command(
            check_name=getattr(args, "check_name", None) or "",
            days=getattr(args, "days", 7),
            output_format=getattr(args, "format", "text"),
        ),
        "usage": lambda: health.handle_health_usage_command(args),
        "overview": lambda: health.handle_health_overview_command(
            output_format=getattr(args, "format", "text"),
            project_root=Path.cwd(),
        ),
        "summary": lambda: health.handle_health_overview_command(
            output_format=getattr(args, "format", "text"),
            project_root=Path.cwd(),
        ),
    }
    
    handler = health_handlers.get(args.command)
    if handler:
        handler()


def route_command(args: argparse.Namespace) -> None:
    """
    Route parsed command arguments to the appropriate handler function.
    
    This function acts as the central dispatcher, examining the 'agent' attribute
    from parsed arguments and calling the corresponding handler function.
    
    Supported routes:
    - Agent commands: reviewer, planner, implementer, tester, debugger, etc.
    - Top-level commands: create, init, workflow, score, doctor, etc.
    - Special commands: customize, skill, etc.
    
    Args:
        args: Parsed command-line arguments with 'agent' attribute indicating the command.
        
    Note:
        If no agent is specified, prints the main help message.
    """
    # Apply prompt enhancement middleware if enabled
    from ..cli.utils.prompt_enhancer import enhance_prompt_if_needed
    from ..core.config import load_config
    
    config = load_config()
    if config.auto_enhancement.enabled:
        args = enhance_prompt_if_needed(args, config.auto_enhancement)
    
    agent = args.agent

    # Handle None case (show help)
    if agent is None:
        help_parser = create_root_parser()
        register_all_parsers(help_parser)
        _safe_print_help(help_parser)
        return

    # Session lifecycle: start on first CLI command, SessionEnd via atexit
    from pathlib import Path

    from ..session import ensure_session_started
    ensure_session_started(Path.cwd())

    # Try agent command handlers first
    agent_handlers = _get_agent_command_handlers()
    if agent in agent_handlers:
        agent_handlers[agent](args)
        return
    
    # Try top-level command handlers
    top_level_handlers = _get_top_level_command_handlers()
    if agent in top_level_handlers:
        top_level_handlers[agent](args)
        return
    
    # Handle special cases with sub-commands or aliases
    special_handlers = {
        "cleanup": _handle_cleanup_command,
        "health": _handle_health_command,
        "observability": _handle_observability_command,
        "simple-mode": simple_mode.handle_simple_mode_command,
        "learning": learning.handle_learning_command,
        "knowledge": top_level.handle_knowledge_command,
        "epic": _handle_epic_command,
        "expert": _handle_expert_command,
    }
    
    if agent in special_handlers:
        special_handlers[agent](args)
        return
    
    # Unknown command - show help
    help_parser = create_root_parser()
    register_all_parsers(help_parser)
    _safe_print_help(help_parser)


def _setup_windows_encoding() -> None:
    """
    Set up UTF-8 encoding for Windows console to prevent encoding errors.
    
    This must be called before any argparse operations or help text printing.
    """
    if sys.platform == "win32":
        # Set environment variable for subprocess encoding
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        
        # Reconfigure stdout/stderr to UTF-8 if possible (Python 3.7+)
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError, OSError):
            # Fallback: use environment variable only
            # Some terminals may not support reconfiguration
            pass


def _safe_print_help(parser: argparse.ArgumentParser) -> None:
    """
    Safely print argparse help text with Windows encoding handling.
    
    Args:
        parser: ArgumentParser instance to print help for
    """
    try:
        parser.print_help()
    except (UnicodeEncodeError, OSError) as e:
        # If encoding fails, try to print ASCII-safe version
        try:
            # Get help text and encode safely
            help_text = parser.format_help()
            # Replace any problematic Unicode characters with ASCII equivalents
            safe_text = help_text.encode('ascii', 'replace').decode('ascii')
            print(safe_text, file=sys.stdout)
        except Exception:
            # Last resort: print basic error message
            print("Help text unavailable due to encoding issues.", file=sys.stderr)
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(ExitCode.GENERAL_ERROR)


def main() -> None:
    """Main CLI entry point - supports both *command and command formats"""
    # Set up Windows encoding FIRST, before any argparse operations
    _setup_windows_encoding()
    
    # Run startup routines (documentation refresh) before main
    from ..core.startup import startup_routines
    
    async def startup():
        """Run startup routines in background."""
        try:
            await startup_routines(refresh_docs=True, background_refresh=True)
        except Exception:
            # Don't fail if startup routines fail
            return

    # Start startup routines in background
    asyncio.run(startup())

    # Create parser and register all subparsers
    parser = create_root_parser()
    register_all_parsers(parser)

    # Parse arguments
    argv = _reorder_global_flags(sys.argv[1:])
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse raises SystemExit(0) for --help, SystemExit(2) for errors
        # We need to handle this gracefully with encoding safety
        if e.code == 0:
            # --help was used, argparse already printed help, but we need to ensure encoding
            # If we get here, argparse.print_help() was called internally
            # The encoding setup at the start should have handled it, but exit cleanly
            sys.exit(ExitCode.SUCCESS)
        else:
            # Parse error - argparse already printed error message
            # Ensure encoding was set up, then exit with error code
            sys.exit(e.code)
    
    # Set verbosity level from arguments
    verbosity_str = getattr(args, "verbosity", None)
    if verbosity_str == "quiet":
        FeedbackManager.set_verbosity(VerbosityLevel.QUIET)
    elif verbosity_str == "verbose":
        FeedbackManager.set_verbosity(VerbosityLevel.VERBOSE)
    else:
        FeedbackManager.set_verbosity(VerbosityLevel.NORMAL)

    # Set progress mode (CLI flags override env; env is handled by FeedbackManager.AUTO)
    if getattr(args, "no_progress", False):
        FeedbackManager.set_progress_mode(ProgressMode.OFF)
    else:
        progress_str = getattr(args, "progress", None)
        if progress_str:
            FeedbackManager.set_progress_mode(ProgressMode(progress_str))
    
    # Set format type if specified (for commands that support it)
    format_type = getattr(args, "format", None)
    if format_type:
        FeedbackManager.set_format(format_type)

    # Route to appropriate handler
    route_command(args)

