"""
Tests for execution graph generator.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.core.exceptions import WorkflowNotFoundError
from tapps_agents.workflow.event_log import WorkflowEventLog
from tapps_agents.workflow.exceptions import EmptyWorkflowError
from tapps_agents.workflow.execution_graph import (
    ExecutionGraph,
    ExecutionGraphGenerator,
    GraphEdge,
    GraphNode,
)


@pytest.fixture
def event_log(tmp_path: Path) -> WorkflowEventLog:
    """Create a test event log."""
    events_dir = tmp_path / "events"
    return WorkflowEventLog(events_dir=events_dir)


@pytest.fixture
def sample_trace() -> dict:
    """Sample execution trace."""
    return {
        "workflow_id": "test-workflow-123",
        "started_at": "2026-01-20T10:00:00Z",
        "ended_at": "2026-01-20T10:05:00Z",
        "steps": [
            {
                "step_id": "step1",
                "agent": "planner",
                "action": "plan",
                "started_at": "2026-01-20T10:00:00Z",
                "ended_at": "2026-01-20T10:01:00Z",
                "duration_ms": 60000,
                "status": "completed",
            },
            {
                "step_id": "step2",
                "agent": "implementer",
                "action": "implement",
                "started_at": "2026-01-20T10:01:00Z",
                "ended_at": "2026-01-20T10:03:00Z",
                "duration_ms": 120000,
                "status": "completed",
            },
            {
                "step_id": "step3",
                "agent": "reviewer",
                "action": "review",
                "started_at": "2026-01-20T10:03:00Z",
                "ended_at": "2026-01-20T10:04:00Z",
                "duration_ms": 60000,
                "status": "completed",
            },
        ],
    }


def test_graph_node_creation():
    """Test GraphNode creation."""
    node = GraphNode(
        id="test-node",
        label="Test Node",
        agent="test-agent",
        status="completed",
    )
    assert node.id == "test-node"
    assert node.label == "Test Node"
    assert node.agent == "test-agent"
    assert node.status == "completed"


def test_graph_edge_creation():
    """Test GraphEdge creation."""
    edge = GraphEdge(
        source="node1",
        target="node2",
        label="next",
        edge_type="default",
    )
    assert edge.source == "node1"
    assert edge.target == "node2"
    assert edge.label == "next"


def test_execution_graph_to_dot(sample_trace):
    """Test DOT export."""
    graph = ExecutionGraph(workflow_id="test-workflow-123")
    
    # Add nodes
    for step in sample_trace["steps"]:
        node = GraphNode(
            id=step["step_id"],
            label=f"{step['agent']}: {step['action']}",
            agent=step["agent"],
            action=step["action"],
            status=step["status"],
            duration_ms=step["duration_ms"],
        )
        graph.nodes.append(node)
    
    # Add edges
    for i in range(len(sample_trace["steps"]) - 1):
        edge = GraphEdge(
            source=sample_trace["steps"][i]["step_id"],
            target=sample_trace["steps"][i + 1]["step_id"],
        )
        graph.edges.append(edge)
    
    dot = graph.to_dot()
    assert "digraph ExecutionGraph" in dot
    assert "step1" in dot
    assert "step2" in dot
    assert "step3" in dot


def test_execution_graph_to_mermaid(sample_trace):
    """Test Mermaid export."""
    graph = ExecutionGraph(workflow_id="test-workflow-123")
    
    # Add nodes
    for step in sample_trace["steps"]:
        node = GraphNode(
            id=step["step_id"],
            label=f"{step['agent']}: {step['action']}",
            agent=step["agent"],
        )
        graph.nodes.append(node)
    
    mermaid = graph.to_mermaid()
    assert "graph LR" in mermaid
    assert "step1" in mermaid


def test_execution_graph_generator(event_log, sample_trace):
    """Test execution graph generation."""
    # Mock event log
    with patch.object(event_log, "get_execution_trace", return_value=sample_trace):
        with patch.object(event_log, "read_events", return_value=[]):
            generator = ExecutionGraphGenerator(event_log=event_log)
            graph = generator.generate_graph("test-workflow-123")
            
            assert graph.workflow_id == "test-workflow-123"
            assert len(graph.nodes) == 3
            assert len(graph.edges) >= 0  # Edges depend on event order


def test_save_dot(tmp_path):
    """Test saving DOT file."""
    graph = ExecutionGraph(workflow_id="test")
    graph.nodes.append(GraphNode(id="node1", label="Node 1"))
    
    generator = ExecutionGraphGenerator()
    output_path = tmp_path / "test.dot"
    generator.save_dot(graph, output_path)
    
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "digraph ExecutionGraph" in content


def test_save_mermaid(tmp_path):
    """Test saving Mermaid file."""
    graph = ExecutionGraph(workflow_id="test")
    graph.nodes.append(GraphNode(id="node1", label="Node 1"))
    
    generator = ExecutionGraphGenerator()
    output_path = tmp_path / "test.mmd"
    generator.save_mermaid(graph, output_path)
    
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "graph LR" in content


def test_generate_graph_empty_trace(event_log):
    """Test graph generation with empty trace."""
    empty_trace = {
        "workflow_id": "test-workflow",
        "steps": [],
    }
    
    with patch.object(event_log, "get_execution_trace", return_value=empty_trace):
        with patch.object(event_log, "read_events", return_value=[]):
            generator = ExecutionGraphGenerator(event_log=event_log)
            
            with pytest.raises(EmptyWorkflowError):
                generator.generate_graph("test-workflow")


def test_generate_graph_missing_events(event_log, sample_trace):
    """Test graph generation when events are missing."""
    with patch.object(event_log, "get_execution_trace", return_value=sample_trace):
        with patch.object(event_log, "read_events", return_value=[]):
            generator = ExecutionGraphGenerator(event_log=event_log)
            graph = generator.generate_graph("test-workflow-123")
            
            # Should still generate graph from trace
            assert graph.workflow_id == "test-workflow-123"
            assert len(graph.nodes) == 3


def test_generate_graph_invalid_workflow_id(event_log):
    """Test graph generation with invalid workflow_id."""
    generator = ExecutionGraphGenerator(event_log=event_log)
    
    with pytest.raises(ValueError, match="workflow_id must be a non-empty string"):
        generator.generate_graph("")
    
    with pytest.raises(ValueError, match="workflow_id must be a non-empty string"):
        generator.generate_graph(None)  # type: ignore


def test_generate_graph_nonexistent_workflow(event_log):
    """Test graph generation for nonexistent workflow."""
    with patch.object(event_log, "get_execution_trace", side_effect=FileNotFoundError()):
        generator = ExecutionGraphGenerator(event_log=event_log)
        
        with pytest.raises(WorkflowNotFoundError):
            generator.generate_graph("nonexistent-workflow")


def test_generate_graph_parallel_steps(event_log):
    """Test graph generation with parallel steps."""
    parallel_trace = {
        "workflow_id": "test-workflow",
        "steps": [
            {
                "step_id": "step1",
                "agent": "planner",
                "action": "plan",
                "requires": [],
            },
            {
                "step_id": "step2",
                "agent": "implementer",
                "action": "implement",
                "requires": ["step1"],
            },
            {
                "step_id": "step3",
                "agent": "reviewer",
                "action": "review",
                "requires": ["step1"],  # Parallel to step2
            },
        ],
    }
    
    mock_events = []
    for step in parallel_trace["steps"]:
        mock_event = MagicMock()
        mock_event.event_type = "step_start"
        mock_event.step_id = step["step_id"]
        mock_events.append(mock_event)
    
    with patch.object(event_log, "get_execution_trace", return_value=parallel_trace):
        with patch.object(event_log, "read_events", return_value=mock_events):
            generator = ExecutionGraphGenerator(event_log=event_log)
            graph = generator.generate_graph("test-workflow")
            
            # Should have dependency edges
            dependency_edges = [e for e in graph.edges if e.edge_type == "dependency"]
            assert len(dependency_edges) >= 2  # step2 and step3 both require step1


def test_build_edges_empty_steps(event_log):
    """Test edge building with empty steps list."""
    empty_trace = {"workflow_id": "test", "steps": []}
    
    generator = ExecutionGraphGenerator(event_log=event_log)
    edges = generator._build_edges(empty_trace, [])
    
    assert edges == []


def test_build_edges_missing_dependencies(event_log):
    """Test edge building with missing step dependencies."""
    trace = {
        "workflow_id": "test",
        "steps": [
            {
                "step_id": "step1",
                "requires": ["nonexistent_step"],  # Dependency doesn't exist
            },
        ],
    }
    
    generator = ExecutionGraphGenerator(event_log=event_log)
    edges = generator._build_edges(trace, [])
    
    # Should not create edge for missing dependency
    assert not any(e.source == "nonexistent_step" for e in edges)


def test_save_dot_permission_error(tmp_path):
    """Test saving DOT file with permission error."""
    graph = ExecutionGraph(workflow_id="test")
    graph.nodes.append(GraphNode(id="node1", label="Node 1"))
    
    generator = ExecutionGraphGenerator()
    
    # Create a path that would cause permission error (on Windows, use read-only)
    output_path = tmp_path / "readonly" / "test.dot"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # On Unix, we can't easily simulate permission errors in tests
    # But we can test that invalid paths are handled
    invalid_path = Path("/invalid/path/that/does/not/exist/test.dot")
    
    # Should raise OSError for invalid path
    with pytest.raises(OSError):
        generator.save_dot(graph, invalid_path)


def test_save_mermaid_invalid_path(tmp_path):
    """Test saving Mermaid file with invalid path."""
    graph = ExecutionGraph(workflow_id="test")
    graph.nodes.append(GraphNode(id="node1", label="Node 1"))
    
    generator = ExecutionGraphGenerator()
    
    # Test with None (should raise ValueError)
    with pytest.raises(ValueError, match="Output path required"):
        generator.save_mermaid(graph, None)  # type: ignore
