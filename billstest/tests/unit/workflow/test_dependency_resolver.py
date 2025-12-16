"""
Unit tests for Dependency Resolver.
"""

import pytest

from tapps_agents.workflow.dependency_resolver import DependencyGraph, DependencyResolver
from tapps_agents.workflow.models import WorkflowStep

pytestmark = pytest.mark.unit


class TestDependencyGraph:
    """Test cases for DependencyGraph."""

    def test_get_ready_steps(self):
        """Test getting ready steps."""
        step1 = WorkflowStep(id="step1", agent="analyst", action="analyze", requires=[], creates=["req"])
        step2 = WorkflowStep(id="step2", agent="planner", action="plan", requires=["req"], creates=["plan"])
        
        graph = DependencyGraph(
            nodes={"step1": step1, "step2": step2},
            dependencies={"step2": {"step1"}},
            dependents={"step1": {"step2"}}
        )
        
        # Initially, only step1 is ready
        ready = graph.get_ready_steps(set())
        assert "step1" in ready
        assert "step2" not in ready
        
        # After step1 completes, step2 is ready
        ready = graph.get_ready_steps({"step1"})
        assert "step2" in ready


class TestDependencyResolver:
    """Test cases for DependencyResolver."""

    def test_resolver_initialization(self):
        """Test resolver initialization."""
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="analyze", requires=[], creates=["req"])
        ]
        
        resolver = DependencyResolver(steps)
        
        assert resolver.graph is not None
        assert "step1" in resolver.graph.nodes

    def test_build_graph_artifact_dependencies(self):
        """Test building graph from artifact dependencies."""
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="analyze", requires=[], creates=["req"]),
            WorkflowStep(id="step2", agent="planner", action="plan", requires=["req"], creates=["plan"]),
        ]
        
        resolver = DependencyResolver(steps)
        graph = resolver.graph
        
        assert "step1" in graph.nodes
        assert "step2" in graph.nodes
        assert "step1" in graph.dependencies["step2"]
        assert "step2" in graph.dependents["step1"]

    def test_resolve_execution_order_linear(self):
        """Test resolving execution order for linear workflow."""
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="analyze", requires=[], creates=["req"]),
            WorkflowStep(id="step2", agent="planner", action="plan", requires=["req"], creates=["plan"]),
            WorkflowStep(id="step3", agent="implementer", action="implement", requires=["plan"], creates=["code"]),
        ]
        
        resolver = DependencyResolver(steps)
        levels = resolver.resolve_execution_order()
        
        assert len(levels) == 3
        assert levels[0] == ["step1"]
        assert levels[1] == ["step2"]
        assert levels[2] == ["step3"]

    def test_resolve_execution_order_parallel(self):
        """Test resolving execution order with parallel steps."""
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="analyze", requires=[], creates=["req"]),
            WorkflowStep(id="step2a", agent="planner", action="plan", requires=["req"], creates=["plan1"]),
            WorkflowStep(id="step2b", agent="designer", action="design", requires=["req"], creates=["design"]),
            WorkflowStep(id="step3", agent="implementer", action="implement", requires=["plan1", "design"], creates=["code"]),
        ]
        
        resolver = DependencyResolver(steps)
        levels = resolver.resolve_execution_order()
        
        assert len(levels) == 3
        assert levels[0] == ["step1"]
        # step2a and step2b can run in parallel
        assert set(levels[1]) == {"step2a", "step2b"}
        assert levels[2] == ["step3"]

    def test_detect_cycles_no_cycles(self):
        """Test cycle detection with no cycles."""
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="analyze", requires=[], creates=["req"]),
            WorkflowStep(id="step2", agent="planner", action="plan", requires=["req"], creates=["plan"]),
        ]
        
        resolver = DependencyResolver(steps)
        cycles = resolver.detect_cycles()
        
        assert len(cycles) == 0

    def test_resolve_execution_order_raises_on_cycle(self):
        """Test that circular dependencies raise an error."""
        # Create a cycle: step1 -> step2 -> step1
        steps = [
            WorkflowStep(id="step1", agent="analyst", action="analyze", requires=["artifact2"], creates=["artifact1"]),
            WorkflowStep(id="step2", agent="planner", action="plan", requires=["artifact1"], creates=["artifact2"]),
        ]
        
        resolver = DependencyResolver(steps)
        
        with pytest.raises(ValueError, match="Circular dependency"):
            resolver.resolve_execution_order()

