"""
Dependency Graph Resolver

Builds dependency graphs from workflow steps and resolves execution order.
Epic 5 / Story 5.2: Dependency Graph Resolver
"""

# @ai-prime-directive: This file implements the dependency graph resolver for workflow step execution ordering.
# The resolver builds dependency graphs from workflow steps and determines which steps can execute in parallel,
# enabling dependency-based parallelism per ADR-004. This is critical for workflow performance optimization.

# @ai-constraints:
# - Must detect circular dependencies and raise errors before execution
# - Topological sort must be deterministic (stable ordering for same dependencies)
# - get_ready_steps() must return steps in stable topological order for parallel execution
# - Dependency resolution must handle both explicit (depends_on) and implicit (artifact-based) dependencies
# - Performance: Graph building and resolution should complete in <10ms for typical workflows

# @note[2025-03-15]: Dependency-based parallelism per ADR-004.
# The resolver enables automatic parallel execution of independent workflow steps.
# See docs/architecture/decisions/ADR-004-yaml-first-workflows.md

from collections import defaultdict, deque
from dataclasses import dataclass

from .models import WorkflowStep


@dataclass
class DependencyGraph:
    """Represents a dependency graph for workflow steps."""

    nodes: dict[str, WorkflowStep]
    dependencies: dict[str, set[str]]  # step_id -> set of step_ids it depends on
    dependents: dict[str, set[str]]  # step_id -> set of step_ids that depend on it

    def get_ready_steps(self, completed: set[str]) -> list[str]:
        """
        Get steps that are ready to execute (all dependencies satisfied).

        Args:
            completed: Set of completed step IDs

        Returns:
            List of step IDs ready to execute, in stable topological order
        """
        ready = []
        for step_id in self.nodes.keys():
            if step_id in completed:
                continue
            # Check if all dependencies are satisfied
            deps = self.dependencies.get(step_id, set())
            if deps.issubset(completed):
                ready.append(step_id)
        # Sort for deterministic ordering
        return sorted(ready)


class DependencyResolver:
    """Resolves workflow step dependencies and execution order."""

    def __init__(self, steps: list[WorkflowStep]):
        """
        Initialize dependency resolver.

        Args:
            steps: List of workflow steps
        """
        self.steps = steps
        self.graph = self._build_graph()

    def _build_graph(self) -> DependencyGraph:
        """Build dependency graph from workflow steps."""
        nodes: dict[str, WorkflowStep] = {}
        dependencies: dict[str, set[str]] = defaultdict(set)
        dependents: dict[str, set[str]] = defaultdict(set)

        # Create node mapping
        for step in self.steps:
            nodes[step.id] = step

        # Build dependency edges based on artifact requirements
        for step in self.steps:
            # Step depends on artifacts created by other steps
            for required_artifact in step.requires:
                # Find steps that create this artifact
                for other_step in self.steps:
                    if other_step.id == step.id:
                        continue
                    if required_artifact in other_step.creates:
                        dependencies[step.id].add(other_step.id)
                        dependents[other_step.id].add(step.id)

            # Also consider explicit 'next' relationships as dependencies
            if step.next:
                # 'next' creates an implicit dependency: next step depends on current step
                if step.next in nodes:
                    dependencies[step.next].add(step.id)
                    dependents[step.id].add(step.next)

        return DependencyGraph(
            nodes=nodes, dependencies=dependencies, dependents=dependents
        )

    def resolve_execution_order(self) -> list[list[str]]:
        """
        Resolve execution order using topological sort.

        Returns:
            List of execution levels, where each level contains step IDs
            that can be executed in parallel. Steps in the same level have
            no dependencies on each other.
        """
        graph = self.graph
        in_degree: dict[str, int] = {}
        ready_queue: deque[str] = deque()

        # Initialize in-degree for each node
        for step_id in graph.nodes.keys():
            deps = graph.dependencies.get(step_id, set())
            in_degree[step_id] = len(deps)
            if in_degree[step_id] == 0:
                ready_queue.append(step_id)

        execution_levels: list[list[str]] = []

        while ready_queue:
            # Process all ready steps at this level
            current_level: list[str] = []
            level_size = len(ready_queue)

            for _ in range(level_size):
                step_id = ready_queue.popleft()
                current_level.append(step_id)

                # Reduce in-degree for dependents
                for dependent_id in graph.dependents.get(step_id, set()):
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        ready_queue.append(dependent_id)

            # Sort for deterministic ordering
            current_level.sort()
            execution_levels.append(current_level)

        # Check for cycles (if any nodes remain unprocessed)
        remaining = [step_id for step_id, degree in in_degree.items() if degree > 0]
        if remaining:
            raise ValueError(
                f"Circular dependency detected. Steps involved: {', '.join(sorted(remaining))}"
            )

        return execution_levels

    def detect_cycles(self) -> list[list[str]]:
        """
        Detect circular dependencies in the workflow.

        Returns:
            List of cycles, where each cycle is a list of step IDs forming a cycle.
            Empty list if no cycles exist.
        """
        graph = self.graph
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> bool:
            """Depth-first search to detect cycles."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # Check dependencies
            for dep_id in graph.dependencies.get(node, set()):
                if dep_id not in visited:
                    if dfs(dep_id):
                        return True
                elif dep_id in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(dep_id)
                    cycle = path[cycle_start:] + [dep_id]
                    cycles.append(cycle)
                    return True

            # Also check dependents (reverse direction)
            for dependent_id in graph.dependents.get(node, set()):
                if dependent_id not in visited:
                    if dfs(dependent_id):
                        return True
                elif dependent_id in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(dependent_id)
                    cycle = path[cycle_start:] + [dependent_id]
                    cycles.append(cycle)
                    return True

            rec_stack.remove(node)
            path.pop()
            return False

        # Check all nodes
        for step_id in graph.nodes.keys():
            if step_id not in visited:
                dfs(step_id)

        return cycles

    def get_dependencies(self, step_id: str) -> set[str]:
        """
        Get direct dependencies for a step.

        Args:
            step_id: Step ID

        Returns:
            Set of step IDs that this step depends on
        """
        return self.graph.dependencies.get(step_id, set()).copy()

    def get_dependents(self, step_id: str) -> set[str]:
        """
        Get steps that depend on this step.

        Args:
            step_id: Step ID

        Returns:
            Set of step IDs that depend on this step
        """
        return self.graph.dependents.get(step_id, set()).copy()

    def get_ready_steps(self, completed: set[str]) -> list[str]:
        """
        Get steps ready to execute given completed steps.

        Args:
            completed: Set of completed step IDs

        Returns:
            List of step IDs ready to execute
        """
        return self.graph.get_ready_steps(completed)
