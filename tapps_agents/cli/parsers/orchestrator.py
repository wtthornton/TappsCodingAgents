"""
Orchestrator agent parser definitions
"""
import argparse


def add_orchestrator_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add orchestrator agent parser and subparsers"""
    orchestrator_parser = subparsers.add_parser(
        "orchestrator",
        help="Orchestrator Agent commands",
        description="""Workflow orchestration and coordination agent.
        
The Orchestrator Agent manages multi-agent workflows:
  • List available workflows
  • Start and manage workflows
  • Track workflow status
  • Make gate decisions
  • Resume interrupted workflows

Use this agent to coordinate complex multi-step development processes.""",
    )
    orchestrator_subparsers = orchestrator_parser.add_subparsers(
        dest="command", help="Orchestrator agent subcommand (use 'help' to see all available commands)"
    )

    orchestrator_subparsers.add_parser(
        "workflow-list", 
        aliases=["*workflow-list"], 
        help="List all available workflows with descriptions",
        description="Display all available workflows that can be orchestrated, including their purposes, steps, and use cases."
    )

    workflow_start_parser = orchestrator_subparsers.add_parser(
        "workflow-start", 
        aliases=["*workflow-start"], 
        help="Start execution of a workflow",
        description="Begin execution of a workflow by its ID. The orchestrator will coordinate all workflow steps and agents."
    )
    workflow_start_parser.add_argument("workflow_id", help="The ID of the workflow to start. Obtain workflow IDs from 'workflow-list' command.")

    orchestrator_subparsers.add_parser(
        "workflow-status",
        aliases=["*workflow-status"],
        help="Show current status of running workflows",
        description="Display the current status of all active workflows including current step, progress, and any errors or warnings."
    )

    orchestrator_subparsers.add_parser(
        "workflow-next", 
        aliases=["*workflow-next"], 
        help="Show the next step in the current workflow",
        description="Display information about the next step that will be executed in the current workflow, including what agent will run and what it will do."
    )

    workflow_skip_parser = orchestrator_subparsers.add_parser(
        "workflow-skip", 
        aliases=["*workflow-skip"], 
        help="Skip an optional step in the current workflow",
        description="Skip an optional workflow step that is not required for workflow completion. Use this to bypass steps that are not needed for your use case."
    )
    workflow_skip_parser.add_argument("step_id", help="The ID of the workflow step to skip. Obtain step IDs from workflow status or workflow definition.")

    orchestrator_subparsers.add_parser(
        "workflow-resume",
        aliases=["*workflow-resume"],
        help="Resume an interrupted or paused workflow",
        description="Resume execution of a workflow that was interrupted, paused, or failed. Continues from the last completed step."
    )

    workflow_parser = orchestrator_subparsers.add_parser(
        "workflow",
        aliases=["*workflow"],
        help="Execute a workflow from a YAML file path",
        description="Execute a workflow directly from a YAML file path. Supports both relative and absolute paths."
    )
    workflow_parser.add_argument(
        "workflow_file",
        help="Path to the workflow YAML file (e.g., 'workflows/custom/my-workflow.yaml' or absolute path)"
    )

    gate_parser = orchestrator_subparsers.add_parser(
        "gate", 
        aliases=["*gate"], 
        help="Make a gate decision for workflow control flow",
        description="""Evaluate a gate condition to determine workflow control flow.
        
Gates are decision points in workflows that determine whether to proceed, skip, or take alternative paths based on conditions. Use this to manually evaluate gates or provide gate decision data.""",
    )
    gate_parser.add_argument("--condition", help="Gate condition expression to evaluate (e.g., 'score > 80', 'tests_passed == true'). Used to determine workflow path.")
    gate_parser.add_argument(
        "--scoring-data", help="JSON string containing scoring or evaluation data to use in gate condition evaluation. Defaults to empty object if not provided.", default="{}"
    )

    orchestrator_subparsers.add_parser(
        "help", aliases=["*help"], help="Show orchestrator commands"
    )

