"""
Main CLI entry point
"""
import argparse
import asyncio
import sys

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
    architect as architect_parsers,
    debugger as debugger_parsers,
    designer as designer_parsers,
    documenter as documenter_parsers,
    enhancer as enhancer_parsers,
    implementer as implementer_parsers,
    improver as improver_parsers,
    ops as ops_parsers,
    orchestrator as orchestrator_parsers,
    planner as planner_parsers,
    reviewer as reviewer_parsers,
    tester as tester_parsers,
    top_level as top_level_parsers,
)


def create_root_parser() -> argparse.ArgumentParser:
    """Create the root ArgumentParser"""
    parser = argparse.ArgumentParser(
        description="TappsCodingAgents CLI - AI coding agents framework",
        epilog="""Quick shortcuts:
  create <description>  - Create new project from description (PRIMARY USE CASE)
  score <file>          - Score a code file (shortcut for 'reviewer score')
  init                  - Initialize project (Cursor Rules + workflow presets)
  workflow <preset>     - Run preset workflows (rapid, full, fix, quality, hotfix)
  
Examples:
  python -m tapps_agents.cli create "Build a task management web app"
  python -m tapps_agents.cli score example.py
  python -m tapps_agents.cli init
  python -m tapps_agents.cli workflow rapid""",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {PACKAGE_VERSION}",
        help="Show version and exit",
    )
    return parser


def register_all_parsers(parser: argparse.ArgumentParser) -> None:
    """Register all subparsers"""
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
    """Route command to appropriate handler"""
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
    elif args.agent == "hardware-profile" or args.agent == "hardware":
        top_level.hardware_profile_command(
            set_profile=getattr(args, "set", None),
            output_format=getattr(args, "format", "text"),
            show_metrics=not getattr(args, "no_metrics", False),
        )
    elif args.agent == "analytics":
        top_level.handle_analytics_command(args)
    elif args.agent == "setup-experts":
        top_level.handle_setup_experts_command(args)
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

