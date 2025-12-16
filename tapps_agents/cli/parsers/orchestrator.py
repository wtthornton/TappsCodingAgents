"""
Orchestrator agent parser definitions
"""
import argparse


def add_orchestrator_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add orchestrator agent parser and subparsers"""
    orchestrator_parser = subparsers.add_parser(
        "orchestrator", help="Orchestrator Agent commands"
    )
    orchestrator_subparsers = orchestrator_parser.add_subparsers(
        dest="command", help="Commands"
    )

    orchestrator_subparsers.add_parser(
        "workflow-list", aliases=["*workflow-list"], help="List available workflows"
    )

    workflow_start_parser = orchestrator_subparsers.add_parser(
        "workflow-start", aliases=["*workflow-start"], help="Start a workflow"
    )
    workflow_start_parser.add_argument("workflow_id", help="Workflow ID to start")

    orchestrator_subparsers.add_parser(
        "workflow-status",
        aliases=["*workflow-status"],
        help="Show current workflow status",
    )

    orchestrator_subparsers.add_parser(
        "workflow-next", aliases=["*workflow-next"], help="Show next step"
    )

    workflow_skip_parser = orchestrator_subparsers.add_parser(
        "workflow-skip", aliases=["*workflow-skip"], help="Skip an optional step"
    )
    workflow_skip_parser.add_argument("step_id", help="Step ID to skip")

    orchestrator_subparsers.add_parser(
        "workflow-resume",
        aliases=["*workflow-resume"],
        help="Resume interrupted workflow",
    )

    gate_parser = orchestrator_subparsers.add_parser(
        "gate", aliases=["*gate"], help="Make a gate decision"
    )
    gate_parser.add_argument("--condition", help="Gate condition")
    gate_parser.add_argument(
        "--scoring-data", help="Scoring data as JSON", default="{}"
    )

    orchestrator_subparsers.add_parser(
        "help", aliases=["*help"], help="Show orchestrator commands"
    )

