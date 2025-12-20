"""
Workflow Execution Plan Generator

Generates normalized execution plan JSON from workflow definitions.
Epic 6 / Story 6.7: Workflow Execution Plan Generation
"""

import json
from pathlib import Path
from typing import Any

from .models import Workflow, WorkflowStep


def generate_execution_plan(workflow: Workflow) -> dict[str, Any]:
    """
    Generate normalized execution plan JSON from workflow definition.

    Args:
        workflow: Parsed workflow definition

    Returns:
        Normalized execution plan as dictionary
    """
    # Build step graph with dependencies
    step_graph: dict[str, dict[str, Any]] = {}
    for step in workflow.steps:
        step_graph[step.id] = {
            "id": step.id,
            "agent": step.agent,
            "action": step.action,
            "context_tier": step.context_tier,
            "creates": step.creates,
            "requires": step.requires,
            "consults": step.consults,
            "condition": step.condition,
            "next": step.next,
            "optional_steps": step.optional_steps,
            "repeats": step.repeats,
            "has_gate": step.gate is not None,
            "gate": step.gate if step.gate else None,
            "scoring": step.scoring if step.scoring else None,
            "metadata": step.metadata,
        }

    # Build dependency graph (reverse: which steps depend on this step's artifacts)
    dependency_graph: dict[str, list[str]] = {}
    artifact_to_steps: dict[str, list[str]] = {}
    
    for step in workflow.steps:
        dependency_graph[step.id] = []
        for artifact in step.creates:
            if artifact not in artifact_to_steps:
                artifact_to_steps[artifact] = []
            artifact_to_steps[artifact].append(step.id)
    
    # Build reverse dependencies (which steps wait for this step)
    for step in workflow.steps:
        for required_artifact in step.requires:
            if required_artifact in artifact_to_steps:
                for creating_step_id in artifact_to_steps[required_artifact]:
                    if step.id not in dependency_graph[creating_step_id]:
                        dependency_graph[creating_step_id].append(step.id)

    # Find entry points (steps with no requirements)
    entry_points = [
        step.id for step in workflow.steps if not step.requires
    ]

    # Find exit points (steps with no next and no dependents)
    exit_points = []
    for step in workflow.steps:
        if not step.next:
            # Check if any other step depends on this one
            has_dependents = any(
                step.id in deps for deps in dependency_graph.values()
            )
            if not has_dependents:
                exit_points.append(step.id)

    plan = {
        "workflow_id": workflow.id,
        "workflow_name": workflow.name,
        "workflow_version": workflow.version,
        "workflow_type": workflow.type.value,
        "schema_version": "2.0",
        "settings": {
            "quality_gates": workflow.settings.quality_gates,
            "code_scoring": workflow.settings.code_scoring,
            "context_tier_default": workflow.settings.context_tier_default,
            "auto_detect": workflow.settings.auto_detect,
        },
        "step_graph": step_graph,
        "dependency_graph": dependency_graph,
        "entry_points": entry_points,
        "exit_points": exit_points,
        "total_steps": len(workflow.steps),
        "steps_with_gates": len([s for s in workflow.steps if s.gate]),
        "steps_with_retry": len([s for s in workflow.steps if s.repeats]),
    }

    return plan


def save_execution_plan(
    execution_plan: dict[str, Any], state_dir: Path, workflow_id: str
) -> Path:
    """
    Save execution plan JSON to workflow state directory.

    Args:
        execution_plan: Execution plan dictionary
        state_dir: Directory where workflow state is stored
        workflow_id: Workflow ID

    Returns:
        Path to saved execution plan file
    """
    state_dir.mkdir(parents=True, exist_ok=True)
    plan_path = state_dir / f"{workflow_id}-execution-plan.json"
    
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(execution_plan, f, indent=2)
    
    return plan_path

