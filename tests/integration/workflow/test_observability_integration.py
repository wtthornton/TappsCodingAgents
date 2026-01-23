"""
Integration tests for observability features.

Tests end-to-end observability functionality with real workflow execution.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tapps_agents.workflow.event_log import WorkflowEvent, WorkflowEventLog
from tapps_agents.workflow.execution_graph import ExecutionGraphGenerator
from tapps_agents.workflow.execution_metrics import ExecutionMetricsCollector
from tapps_agents.workflow.observability_dashboard import ObservabilityDashboard
from tapps_agents.workflow.exceptions import (
    EmptyWorkflowError,
    GraphGenerationError,
    InvalidTraceError,
)
from tapps_agents.core.exceptions import WorkflowNotFoundError


@pytest.fixture
def test_workflow_state(tmp_path: Path) -> dict:
    """Create a test workflow state with events."""
    events_dir = tmp_path / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    
    event_log = WorkflowEventLog(events_dir=events_dir)
    workflow_id = "test-workflow-integration"
    
    # Emit workflow start
    event_log.emit_event(
        event_type="workflow_start",
        workflow_id=workflow_id,
    )
    
    # Emit step events
    for i, (agent, action) in enumerate([("planner", "plan"), ("implementer", "implement"), ("reviewer", "review")]):
        step_id = f"step{i+1}"
        event_log.emit_event(
            event_type="step_start",
            workflow_id=workflow_id,
            step_id=step_id,
            agent=agent,
            action=action,
        )
        event_log.emit_event(
            event_type="step_finish",
            workflow_id=workflow_id,
            step_id=step_id,
            agent=agent,
            action=action,
            status="completed",
        )
    
    # Emit workflow end
    event_log.emit_event(
        event_type="workflow_end",
        workflow_id=workflow_id,
        status="completed",
    )
    
    return {
        "workflow_id": workflow_id,
        "event_log": event_log,
        "events_dir": events_dir,
    }


def test_end_to_end_graph_generation(test_workflow_state):
    """Test end-to-end graph generation from real workflow execution."""
    workflow_id = test_workflow_state["workflow_id"]
    event_log = test_workflow_state["event_log"]
    
    generator = ExecutionGraphGenerator(event_log=event_log)
    graph = generator.generate_graph(workflow_id)
    
    assert graph.workflow_id == workflow_id
    assert len(graph.nodes) == 3
    assert len(graph.edges) >= 0
    
    # Verify nodes
    node_ids = [node.id for node in graph.nodes]
    assert "step1" in node_ids
    assert "step2" in node_ids
    assert "step3" in node_ids


def test_end_to_end_dashboard_generation(test_workflow_state, tmp_path: Path):
    """Test end-to-end dashboard generation with real metrics and traces."""
    workflow_id = test_workflow_state["workflow_id"]
    event_log = test_workflow_state["event_log"]
    
    metrics_dir = tmp_path / "metrics"
    metrics_collector = ExecutionMetricsCollector(metrics_dir=metrics_dir)
    
    dashboard = ObservabilityDashboard(
        project_root=tmp_path,
        event_log=event_log,
        metrics_collector=metrics_collector,
    )
    
    result = dashboard.generate_dashboard(workflow_id=workflow_id)
    
    assert result["workflow_id"] == workflow_id
    assert "trace" in result
    assert "graph" in result or "graph_error" in result
    assert "events" in result or "events_error" in result


def test_gate_evaluation_in_workflow_context(tmp_path: Path):
    """Test gate evaluation in actual workflow context."""
    from tapps_agents.quality.gates.registry import get_gate_registry
    from tapps_agents.workflow.gate_integration import GateIntegration
    from tapps_agents.workflow.models import WorkflowStep, WorkflowState
    
    integration = GateIntegration()
    
    step = WorkflowStep(
        id="test-step",
        agent="implementer",
        action="implement",
    )
    step.metadata = {
        "gates": [
            {"name": "security", "config": {"filter_secrets": True}},
        ]
    }
    
    state = WorkflowState(workflow_id="test-workflow", status="running")
    
    context = {
        "content": "api_key = 'sk-test123'",
        "file_path": "src/config.py",
    }
    
    results = integration.evaluate_step_gates(step, state, context)
    
    assert "all_passed" in results
    assert "gate_results" in results
    assert "security" in results["gate_results"]
    
    # Security gate should fail due to secret
    security_result = results["gate_results"]["security"]
    assert security_result["passed"] is False


def test_error_propagation_through_workflow_system(test_workflow_state):
    """Test error propagation through workflow system."""
    workflow_id = "nonexistent-workflow"
    event_log = test_workflow_state["event_log"]
    
    generator = ExecutionGraphGenerator(event_log=event_log)
    
    # Should raise WorkflowNotFoundError
    with pytest.raises(WorkflowNotFoundError):
        generator.generate_graph(workflow_id)


def test_cli_command_error_handling(tmp_path: Path):
    """Test CLI command error handling."""
    from tapps_agents.cli.commands.observability import handle_observability_graph_command
    
    # Test with invalid workflow_id
    with pytest.raises(SystemExit):
        handle_observability_graph_command(
            workflow_id="",  # Invalid
            output_format="dot",
            project_root=tmp_path,
        )
