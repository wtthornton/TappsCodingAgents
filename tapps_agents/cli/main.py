"""
Main CLI entry point
"""
import argparse
import asyncio

from .. import __version__ as PACKAGE_VERSION
from .commands import (
    analyst,
    architect,
    debugger,
    designer,
    documenter,
    enhancer,
    implementer,
    improver,
    ops,
    orchestrator,
    planner,
    reviewer,
    tester,
    top_level,
)

# Import all parser registration functions
from .parsers import (
    analyst as analyst_parsers,
)
from .parsers import (
    architect as architect_parsers,
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
with 13 workflow agents, industry experts, and full Cursor AI integration.

Key Features:
  • 13 Workflow Agents: Analyst, Architect, Debugger, Designer, Documenter, Enhancer,
    Implementer, Improver, Ops, Orchestrator, Planner, Reviewer, Tester
  • Industry Experts: Domain-specific knowledge with weighted decision-making
  • Workflow Presets: Rapid development, full SDLC, bug fixes, quality improvement
  • Code Quality Tools: Scoring, linting, type checking, duplication detection
  • Cursor Integration: Skills, Background Agents, and natural language commands

For detailed documentation, visit: https://github.com/your-repo/docs""",
        epilog="""QUICK START COMMANDS:
  create <description>     Create a new project from description (PRIMARY USE CASE)
  score <file>             Score a code file (shortcut for 'reviewer score')
  init                     Initialize project (Cursor Rules + workflow presets)
  workflow <preset>         Run preset workflows (rapid, full, fix, quality, hotfix)
  doctor                    Validate local environment and tools
  setup-experts            Interactive expert setup wizard

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

    # Register top-level parsers
    top_level_parsers.add_top_level_parsers(subparsers)


def route_command(args: argparse.Namespace) -> None:
    """
    Route parsed command arguments to the appropriate handler function.
    
    This function acts as the central dispatcher, examining the 'agent' attribute
    from parsed arguments and calling the corresponding handler function.
    
    Supported routes:
    - Agent commands: reviewer, planner, implementer, tester, debugger, etc.
    - Top-level commands: create, init, workflow, score, doctor, etc.
    - Special commands: hardware-profile, analytics, customize, skill, etc.
    
    Args:
        args: Parsed command-line arguments with 'agent' attribute indicating the command.
        
    Note:
        If no agent is specified, prints the main help message.
    """
    # Route agent commands
    if args.agent == "reviewer":
        reviewer.handle_reviewer_command(args)
    elif args.agent == "planner":
        planner.handle_planner_command(args)
    elif args.agent == "implementer":
        implementer.handle_implementer_command(args)
    elif args.agent == "tester":
        tester.handle_tester_command(args)
    elif args.agent == "debugger":
        debugger.handle_debugger_command(args)
    elif args.agent == "documenter":
        documenter.handle_documenter_command(args)
    elif args.agent == "orchestrator":
        orchestrator.handle_orchestrator_command(args)
    elif args.agent == "analyst":
        analyst.handle_analyst_command(args)
    elif args.agent == "architect":
        architect.handle_architect_command(args)
    elif args.agent == "designer":
        designer.handle_designer_command(args)
    elif args.agent == "improver":
        improver.handle_improver_command(args)
    elif args.agent == "ops":
        ops.handle_ops_command(args)
    elif args.agent == "enhancer":
        enhancer.handle_enhancer_command(args)
    # Route top-level commands
    elif args.agent == "create":
        top_level.handle_create_command(args)
    elif args.agent == "init":
        top_level.handle_init_command(args)
    elif args.agent == "workflow":
        top_level.handle_workflow_command(args)
    elif args.agent == "score":
        top_level.handle_score_command(args)
    elif args.agent == "doctor":
        top_level.handle_doctor_command(args)
    elif args.agent == "health":
        from .commands import health
        if hasattr(args, "command"):
            if args.command == "check":
                health.handle_health_check_command(
                    check_name=getattr(args, "check", None),
                    output_format=getattr(args, "format", "text"),
                    save=getattr(args, "save", True),
                )
            elif args.command == "dashboard" or args.command == "show":
                health.handle_health_dashboard_command(
                    output_format=getattr(args, "format", "text"),
                )
            elif args.command == "metrics":
                health.handle_health_metrics_command(
                    check_name=getattr(args, "check_name", None),
                    status=getattr(args, "status", None),
                    days=getattr(args, "days", 30),
                    output_format=getattr(args, "format", "text"),
                )
            elif args.command == "trends":
                health.handle_health_trends_command(
                    check_name=getattr(args, "check_name", None) or "",
                    days=getattr(args, "days", 7),
                    output_format=getattr(args, "format", "text"),
                )
    elif args.agent == "install-dev":
        top_level.handle_install_dev_command(args)
    elif args.agent == "hardware-profile" or args.agent == "hardware":
        top_level.hardware_profile_command(
            set_profile=getattr(args, "set", None),
            output_format=getattr(args, "format", "text"),
            show_metrics=not getattr(args, "no_metrics", False),
        )
    elif args.agent == "analytics":
        top_level.handle_analytics_command(args)
    elif args.agent == "customize":
        top_level.handle_customize_command(args)
    elif args.agent == "skill":
        top_level.handle_skill_command(args)
    elif args.agent == "skill-template":
        top_level.handle_skill_template_command(args)
    elif args.agent == "background-agent-config" or args.agent == "bg-config":
        top_level.handle_background_agent_config_command(args)
    elif args.agent == "governance" or args.agent == "approval":
        top_level.handle_governance_command(args)
    elif args.agent == "auto-execution" or args.agent == "auto-exec" or args.agent == "ae":
        top_level.handle_auto_execution_command(args)
    elif args.agent == "setup-experts":
        top_level.handle_setup_experts_command(args)
    elif args.agent == "cursor":
        top_level.handle_cursor_command(args)
    else:
        # Show main help if no agent specified
        parser = create_root_parser()
        register_all_parsers(parser)
        parser.print_help()


def main() -> None:
    """Main CLI entry point - supports both *command and command formats"""
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
    args = parser.parse_args()

    # Route to appropriate handler
    route_command(args)

