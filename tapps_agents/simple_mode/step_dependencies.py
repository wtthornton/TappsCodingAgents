"""
Step Dependency Management for Simple Mode Workflows.

Models workflow step dependencies as a DAG (Directed Acyclic Graph)
and handles failure cascades using Python 3.10+ pattern matching.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowStep(IntEnum):
    """Workflow steps with explicit ordering."""

    ENHANCER = 1
    PLANNER = 2
    ARCHITECT = 3
    DESIGNER = 4
    IMPLEMENTER = 5
    REVIEWER = 6
    TESTER = 7
    VERIFICATION = 8


class StepDefinition(BaseModel):
    """Definition of a workflow step with dependencies."""

    step: WorkflowStep
    agent_name: str
    command: str
    dependencies: list[WorkflowStep] = Field(default_factory=list)
    can_run_parallel: bool = False  # Can run in parallel with siblings
    required_for_workflow: bool = True  # Failure blocks workflow


# Build workflow DAG - defines the standard build workflow steps
WORKFLOW_STEPS: list[StepDefinition] = [
    StepDefinition(
        step=WorkflowStep.ENHANCER,
        agent_name="enhancer",
        command="enhance",
    ),
    StepDefinition(
        step=WorkflowStep.PLANNER,
        agent_name="planner",
        command="create-story",
        dependencies=[WorkflowStep.ENHANCER],
    ),
    StepDefinition(
        step=WorkflowStep.ARCHITECT,
        agent_name="architect",
        command="design-system",
        dependencies=[WorkflowStep.ENHANCER],
    ),
    StepDefinition(
        step=WorkflowStep.DESIGNER,
        agent_name="designer",
        command="design-api",
        dependencies=[WorkflowStep.ARCHITECT],
    ),
    StepDefinition(
        step=WorkflowStep.IMPLEMENTER,
        agent_name="implementer",
        command="implement",
        dependencies=[WorkflowStep.PLANNER, WorkflowStep.DESIGNER],
    ),
    StepDefinition(
        step=WorkflowStep.REVIEWER,
        agent_name="reviewer",
        command="score",
        dependencies=[WorkflowStep.IMPLEMENTER],
        can_run_parallel=True,
    ),
    StepDefinition(
        step=WorkflowStep.TESTER,
        agent_name="tester",
        command="generate-tests",
        dependencies=[WorkflowStep.IMPLEMENTER],
        can_run_parallel=True,
    ),
    StepDefinition(
        step=WorkflowStep.VERIFICATION,
        agent_name="verification",
        command="verify",
        dependencies=[WorkflowStep.REVIEWER, WorkflowStep.TESTER],
    ),
]

# Index for fast lookup
STEP_BY_NUMBER: dict[WorkflowStep, StepDefinition] = {s.step: s for s in WORKFLOW_STEPS}

# Index by agent name
STEP_BY_AGENT: dict[str, StepDefinition] = {s.agent_name: s for s in WORKFLOW_STEPS}


@dataclass
class StepExecutionState:
    """Track step execution state during workflow."""

    completed: set[WorkflowStep] = field(default_factory=set)
    failed: set[WorkflowStep] = field(default_factory=set)
    skipped: set[WorkflowStep] = field(default_factory=set)
    running: set[WorkflowStep] = field(default_factory=set)
    results: dict[WorkflowStep, Any] = field(default_factory=dict)

    @property
    def all_processed(self) -> set[WorkflowStep]:
        """Get all steps that have been processed (completed, failed, or skipped)."""
        return self.completed | self.failed | self.skipped

    def mark_completed(self, step: WorkflowStep, result: Any = None) -> None:
        """Mark step as completed."""
        self.running.discard(step)
        self.completed.add(step)
        if result is not None:
            self.results[step] = result

    def mark_failed(self, step: WorkflowStep, error: str | None = None) -> None:
        """Mark step as failed."""
        self.running.discard(step)
        self.failed.add(step)
        if error:
            self.results[step] = {"error": error}

    def mark_skipped(self, step: WorkflowStep, reason: str | None = None) -> None:
        """Mark step as skipped."""
        self.running.discard(step)
        self.skipped.add(step)
        if reason:
            self.results[step] = {"skipped": reason}

    def mark_running(self, step: WorkflowStep) -> None:
        """Mark step as running."""
        self.running.add(step)

    def is_complete(self) -> bool:
        """Check if workflow is complete (all steps processed)."""
        all_steps = set(WorkflowStep)
        return self.all_processed >= all_steps

    def has_critical_failures(self) -> bool:
        """Check if there are failures in required steps."""
        for step in self.failed:
            step_def = STEP_BY_NUMBER.get(step)
            if step_def and step_def.required_for_workflow:
                return True
        return False


class StepDependencyManager:
    """Manages step dependencies and failure cascades."""

    def __init__(self, steps: list[StepDefinition] | None = None):
        """Initialize with step definitions.

        Args:
            steps: Optional custom step definitions (defaults to WORKFLOW_STEPS)
        """
        steps = steps or WORKFLOW_STEPS
        self.steps: dict[WorkflowStep, StepDefinition] = {s.step: s for s in steps}

    def should_skip_step(
        self,
        step: WorkflowStep,
        state: StepExecutionState,
    ) -> bool:
        """Check if step should be skipped due to failed dependencies.

        Args:
            step: Step to check
            state: Current execution state

        Returns:
            True if step should be skipped
        """
        step_def = self.steps.get(step)
        if not step_def:
            return True

        # Check if any dependency failed
        return bool(state.failed & set(step_def.dependencies))

    def get_skip_reason(
        self,
        step: WorkflowStep,
        state: StepExecutionState,
    ) -> str:
        """Get human-readable skip reason using pattern matching.

        Args:
            step: Step to check
            state: Current execution state

        Returns:
            Skip reason string
        """
        step_def = self.steps.get(step)
        if not step_def:
            return "Unknown step"

        failed_deps = state.failed & set(step_def.dependencies)

        # Use match/case for clear failure handling (Python 3.10+)
        match len(failed_deps):
            case 0:
                return "No failed dependencies"
            case 1:
                dep = next(iter(failed_deps))
                return f"Dependency step {dep.value} ({dep.name}) failed"
            case _:
                dep_names = ", ".join(f"{d.value} ({d.name})" for d in failed_deps)
                return f"Multiple dependencies failed: {dep_names}"

    def get_executable_steps(
        self,
        state: StepExecutionState,
    ) -> list[WorkflowStep]:
        """Get steps that can be executed now (dependencies satisfied).

        Args:
            state: Current execution state

        Returns:
            List of executable steps
        """
        executable = []
        for step, step_def in self.steps.items():
            # Skip if already processed
            if step in state.all_processed | state.running:
                continue
            # Check if all dependencies completed
            if set(step_def.dependencies) <= state.completed:
                executable.append(step)
        return executable

    def get_parallel_steps(
        self,
        state: StepExecutionState,
    ) -> list[WorkflowStep]:
        """Get steps that can run in parallel now.

        Args:
            state: Current execution state

        Returns:
            List of steps that can run in parallel
        """
        executable = self.get_executable_steps(state)
        return [
            step
            for step in executable
            if self.steps[step].can_run_parallel
        ]

    def get_dependent_steps(
        self,
        step: WorkflowStep,
    ) -> list[WorkflowStep]:
        """Get steps that depend on the given step.

        Args:
            step: Step to find dependents for

        Returns:
            List of dependent steps
        """
        dependents = []
        for s, step_def in self.steps.items():
            if step in step_def.dependencies:
                dependents.append(s)
        return dependents

    def get_steps_to_skip_on_failure(
        self,
        failed_step: WorkflowStep,
    ) -> list[WorkflowStep]:
        """Get all steps that should be skipped if a step fails.

        Uses transitive dependency resolution.

        Args:
            failed_step: The step that failed

        Returns:
            List of steps to skip
        """
        to_skip: set[WorkflowStep] = set()
        to_check = [failed_step]

        while to_check:
            current = to_check.pop()
            for dependent in self.get_dependent_steps(current):
                if dependent not in to_skip:
                    to_skip.add(dependent)
                    to_check.append(dependent)

        return list(to_skip)

    def get_step_order(self) -> list[WorkflowStep]:
        """Get topologically sorted step order.

        Returns:
            List of steps in execution order
        """
        # Kahn's algorithm for topological sort
        in_degree: dict[WorkflowStep, int] = {step: 0 for step in self.steps}
        for step_def in self.steps.values():
            for dep in step_def.dependencies:
                if dep in in_degree:
                    in_degree[step_def.step] += 1

        queue = [step for step, deg in in_degree.items() if deg == 0]
        result = []

        while queue:
            step = queue.pop(0)
            result.append(step)
            for dependent in self.get_dependent_steps(step):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        return result

    def validate_dag(self) -> list[str]:
        """Validate that step definitions form a valid DAG.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check for undefined dependencies
        for step, step_def in self.steps.items():
            for dep in step_def.dependencies:
                if dep not in self.steps:
                    errors.append(
                        f"Step {step.name} depends on undefined step {dep.name}"
                    )

        # Check for cycles (should match step count after toposort)
        sorted_steps = self.get_step_order()
        if len(sorted_steps) != len(self.steps):
            errors.append("Circular dependency detected in workflow steps")

        # Check for self-dependencies
        for step, step_def in self.steps.items():
            if step in step_def.dependencies:
                errors.append(f"Step {step.name} depends on itself")

        return errors


def get_step_for_agent(agent_name: str) -> WorkflowStep | None:
    """Get workflow step for an agent name.

    Args:
        agent_name: Name of the agent

    Returns:
        WorkflowStep or None if not found
    """
    step_def = STEP_BY_AGENT.get(agent_name)
    return step_def.step if step_def else None


def get_agent_for_step(step: WorkflowStep) -> str | None:
    """Get agent name for a workflow step.

    Args:
        step: Workflow step

    Returns:
        Agent name or None if not found
    """
    step_def = STEP_BY_NUMBER.get(step)
    return step_def.agent_name if step_def else None
