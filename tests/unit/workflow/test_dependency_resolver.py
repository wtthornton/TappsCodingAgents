"""
Unit tests for DependencyResolver business logic validation (Story 18.2).

Tests validate:
- Step dependency resolution with known dependency graphs
- Gate condition evaluation with test data
- Artifact requirement checking
- Workflow execution order correctness
- Step completion and state transitions
"""

import pytest

from tapps_agents.workflow.dependency_resolver import DependencyResolver
from tapps_agents.workflow.models import WorkflowStep


@pytest.mark.unit
class TestDependencyResolverBusinessLogic:
    """Business logic validation tests for DependencyResolver (Story 18.2)."""

    def test_resolve_execution_order_simple_chain(self):
        """Test execution order resolution for simple linear chain (Story 18.2)."""
        # Create steps: step1 -> step2 -> step3
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="gather", creates=["artifact1"]),
            WorkflowStep(id="step2", agent="planner", action="plan", requires=["artifact1"], creates=["artifact2"]),
            WorkflowStep(id="step3", agent="implementer", action="implement", requires=["artifact2"]),
        ]
        
        resolver = DependencyResolver(steps)
        execution_order = resolver.resolve_execution_order()
        
        # Should have 3 levels: step1, then step2, then step3
        assert len(execution_order) == 3, \
            f"Expected 3 execution levels for linear chain, got {len(execution_order)}"
        assert execution_order[0] == ["step1"], \
            f"First level should be ['step1'], got {execution_order[0]}"
        assert execution_order[1] == ["step2"], \
            f"Second level should be ['step2'], got {execution_order[1]}"
        assert execution_order[2] == ["step3"], \
            f"Third level should be ['step3'], got {execution_order[2]}"

    def test_resolve_execution_order_parallel_steps(self):
        """Test execution order with parallel independent steps (Story 18.2)."""
        # Create steps where step2 and step3 can run in parallel after step1
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="gather", creates=["artifact1"]),
            WorkflowStep(id="step2", agent="planner", action="plan", requires=["artifact1"]),
            WorkflowStep(id="step3", agent="designer", action="design", requires=["artifact1"]),
            WorkflowStep(id="step4", agent="implementer", action="implement", requires=["artifact1"]),
        ]
        
        resolver = DependencyResolver(steps)
        execution_order = resolver.resolve_execution_order()
        
        # Should have 2 levels: step1, then [step2, step3, step4] in parallel
        assert len(execution_order) == 2, \
            f"Expected 2 execution levels, got {len(execution_order)}"
        assert execution_order[0] == ["step1"], \
            f"First level should be ['step1'], got {execution_order[0]}"
        # All other steps should be in level 2 (can run in parallel)
        assert set(execution_order[1]) == {"step2", "step3", "step4"}, \
            f"Second level should contain step2, step3, step4, got {execution_order[1]}"
        # Should be sorted deterministically
        assert execution_order[1] == sorted(execution_order[1]), \
            "Steps in same level should be sorted deterministically"

    def test_resolve_execution_order_complex_dependencies(self):
        """Test execution order with complex dependency graph (Story 18.2)."""
        # Create a more complex graph:
        # step1 -> step2, step3 (parallel)
        # step2, step3 -> step4
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="gather", creates=["artifact1"]),
            WorkflowStep(id="step2", agent="planner", action="plan", requires=["artifact1"], creates=["artifact2"]),
            WorkflowStep(id="step3", agent="designer", action="design", requires=["artifact1"], creates=["artifact3"]),
            WorkflowStep(id="step4", agent="implementer", action="implement", requires=["artifact2", "artifact3"]),
        ]
        
        resolver = DependencyResolver(steps)
        execution_order = resolver.resolve_execution_order()
        
        # Should have 3 levels: step1, then [step2, step3], then step4
        assert len(execution_order) == 3, \
            f"Expected 3 execution levels, got {len(execution_order)}"
        assert execution_order[0] == ["step1"], \
            f"First level should be ['step1'], got {execution_order[0]}"
        assert set(execution_order[1]) == {"step2", "step3"}, \
            f"Second level should contain step2 and step3, got {execution_order[1]}"
        assert execution_order[2] == ["step4"], \
            f"Third level should be ['step4'], got {execution_order[2]}"

    def test_dependency_resolution_artifact_requirements(self):
        """Test that artifact requirements correctly create dependencies (Story 18.2)."""
        # step2 requires artifact1 created by step1
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="gather", creates=["artifact1"]),
            WorkflowStep(id="step2", agent="planner", action="plan", requires=["artifact1"]),
        ]
        
        resolver = DependencyResolver(steps)
        
        # Verify dependency relationship
        deps = resolver.get_dependencies("step2")
        assert "step1" in deps, \
            f"step2 should depend on step1 (creates artifact1), got dependencies: {deps}"
        
        # Verify dependent relationship
        dependents = resolver.get_dependents("step1")
        assert "step2" in dependents, \
            f"step1 should have step2 as dependent, got dependents: {dependents}"

    def test_dependency_resolution_next_relationships(self):
        """Test that 'next' relationships create dependencies (Story 18.2)."""
        # step1 has next="step2"
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="gather", next="step2"),
            WorkflowStep(id="step2", agent="planner", action="plan"),
        ]
        
        resolver = DependencyResolver(steps)
        
        # Verify dependency: step2 depends on step1 (via next relationship)
        deps = resolver.get_dependencies("step2")
        assert "step1" in deps, \
            f"step2 should depend on step1 (via next), got dependencies: {deps}"

    def test_get_ready_steps_returns_correct_steps(self):
        """Test that get_ready_steps returns steps with all dependencies satisfied (Story 18.2)."""
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="gather", creates=["artifact1"]),
            WorkflowStep(id="step2", agent="planner", action="plan", requires=["artifact1"], creates=["artifact2"]),
            WorkflowStep(id="step3", agent="designer", action="design", requires=["artifact1"]),
            WorkflowStep(id="step4", agent="implementer", action="implement", requires=["artifact2"]),
        ]
        
        resolver = DependencyResolver(steps)
        
        # Initially, only step1 should be ready
        ready = resolver.get_ready_steps(set())
        assert ready == ["step1"], \
            f"Initially only step1 should be ready, got {ready}"
        
        # After step1 completes, step2 and step3 should be ready
        ready = resolver.get_ready_steps({"step1"})
        assert set(ready) == {"step2", "step3"}, \
            f"After step1, step2 and step3 should be ready, got {ready}"
        
        # After step1 and step2 complete, step3 and step4 should be ready
        # (step3 requires artifact1 from step1, step4 requires artifact2 from step2)
        ready = resolver.get_ready_steps({"step1", "step2"})
        assert set(ready) == {"step3", "step4"}, \
            f"After step1 and step2, step3 and step4 should be ready, got {ready}"
        
        # After all steps complete, nothing should be ready
        ready = resolver.get_ready_steps({"step1", "step2", "step3", "step4"})
        assert ready == [], \
            f"After all steps complete, nothing should be ready, got {ready}"

    def test_detect_cycles_raises_error(self):
        """Test that circular dependencies are detected (Story 18.2)."""
        # Create circular dependency: step1 -> step2 -> step3 -> step1 (via next)
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="gather", next="step2"),
            WorkflowStep(id="step2", agent="planner", action="plan", next="step3"),
            WorkflowStep(id="step3", agent="designer", action="design", next="step1"),
        ]
        
        resolver = DependencyResolver(steps)
        
        # Should raise ValueError when resolving execution order
        with pytest.raises(ValueError, match="Circular dependency"):
            resolver.resolve_execution_order()

    def test_detect_cycles_artifact_cycle(self):
        """Test that cycles via artifacts are detected (Story 18.2)."""
        # Create cycle via artifacts: step1 creates artifact1 required by step2,
        # step2 creates artifact2 required by step1
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="gather", creates=["artifact1"], requires=["artifact2"]),
            WorkflowStep(id="step2", agent="planner", action="plan", creates=["artifact2"], requires=["artifact1"]),
        ]
        
        resolver = DependencyResolver(steps)
        
        # Should raise ValueError when resolving execution order
        with pytest.raises(ValueError, match="Circular dependency"):
            resolver.resolve_execution_order()

    def test_deterministic_ordering(self):
        """Test that execution order is deterministic (sorted by step.id) (Story 18.2)."""
        # Create multiple steps that can run in parallel
        steps = [
            WorkflowStep(id="step_c", agent="analyst", action="gather", creates=["artifact1"]),
            WorkflowStep(id="step_a", agent="planner", action="plan", requires=["artifact1"]),
            WorkflowStep(id="step_b", agent="designer", action="design", requires=["artifact1"]),
            WorkflowStep(id="step_d", agent="implementer", action="implement", requires=["artifact1"]),
        ]
        
        resolver = DependencyResolver(steps)
        execution_order = resolver.resolve_execution_order()
        
        # First level should be sorted
        assert execution_order[0] == ["step_c"], \
            "First level should be sorted: step_c comes first alphabetically"
        
        # Second level should be sorted alphabetically
        assert execution_order[1] == ["step_a", "step_b", "step_d"], \
            f"Second level should be sorted alphabetically, got {execution_order[1]}"

    def test_multiple_artifact_dependencies(self):
        """Test steps that require multiple artifacts (Story 18.2)."""
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="gather", creates=["artifact1"]),
            WorkflowStep(id="step2", agent="planner", action="plan", creates=["artifact2"]),
            WorkflowStep(id="step3", agent="designer", action="design", creates=["artifact3"]),
            WorkflowStep(id="step4", agent="implementer", action="implement", 
                        requires=["artifact1", "artifact2", "artifact3"]),
        ]
        
        resolver = DependencyResolver(steps)
        execution_order = resolver.resolve_execution_order()
        
        # step1, step2, step3 can run in parallel
        # step4 requires all three
        assert len(execution_order) == 2, \
            f"Expected 2 execution levels, got {len(execution_order)}"
        assert set(execution_order[0]) == {"step1", "step2", "step3"}, \
            f"First level should contain step1, step2, step3, got {execution_order[0]}"
        assert execution_order[1] == ["step4"], \
            f"Second level should be ['step4'], got {execution_order[1]}"
        
        # Verify step4 depends on all three
        deps = resolver.get_dependencies("step4")
        assert deps == {"step1", "step2", "step3"}, \
            f"step4 should depend on step1, step2, step3, got {deps}"

    def test_no_dependencies_parallel_execution(self):
        """Test that steps with no dependencies can run in parallel (Story 18.2)."""
        # All steps are independent
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="gather"),
            WorkflowStep(id="step2", agent="planner", action="plan"),
            WorkflowStep(id="step3", agent="designer", action="design"),
        ]
        
        resolver = DependencyResolver(steps)
        execution_order = resolver.resolve_execution_order()
        
        # All steps should be in the first level (can run in parallel)
        assert len(execution_order) == 1, \
            f"Expected 1 execution level for independent steps, got {len(execution_order)}"
        assert set(execution_order[0]) == {"step1", "step2", "step3"}, \
            f"All steps should be in first level, got {execution_order[0]}"
        # Should be sorted deterministically
        assert execution_order[0] == sorted(execution_order[0]), \
            "Steps should be sorted deterministically"

