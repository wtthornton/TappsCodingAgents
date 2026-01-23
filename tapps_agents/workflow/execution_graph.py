"""
Execution Graph Generator

Converts workflow event log traces into graph structures for visualization.
Supports DOT/Graphviz export and Mermaid diagram generation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .event_log import WorkflowEventLog
from .exceptions import (
    EmptyWorkflowError,
    GraphGenerationError,
    InvalidTraceError,
)
from ..core.exceptions import WorkflowNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """A node in the execution graph."""

    id: str
    label: str
    agent: str | None = None
    action: str | None = None
    status: str | None = None
    duration_ms: float | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    """An edge in the execution graph."""

    source: str
    target: str
    label: str | None = None
    edge_type: str = "default"  # default, gate_pass, gate_fail, dependency
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionGraph:
    """Execution graph structure."""

    workflow_id: str
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dot(self) -> str:
        """
        Export graph to DOT format for Graphviz.

        Returns:
            DOT format string
        """
        lines = ["digraph ExecutionGraph {", "  rankdir=LR;", "  node [shape=box];"]
        
        # Add nodes
        for node in self.nodes:
            label = node.label.replace('"', '\\"')
            color = self._get_node_color(node.status)
            style = "filled" if node.error else "solid"
            
            node_attrs = [
                f'label="{label}"',
                f'fillcolor="{color}"',
                f'style="{style}"',
            ]
            
            if node.duration_ms:
                node_attrs.append(f'tooltip="Duration: {node.duration_ms:.0f}ms"')
            
            if node.error:
                node_attrs.append('fontcolor="red"')
            
            lines.append(f'  "{node.id}" [{", ".join(node_attrs)}];')
        
        # Add edges
        for edge in self.edges:
            edge_attrs = []
            
            if edge.label:
                edge_attrs.append(f'label="{edge.label.replace(chr(34), chr(92)+chr(34))}"')
            
            color = self._get_edge_color(edge.edge_type)
            if color:
                edge_attrs.append(f'color="{color}"')
            
            style = self._get_edge_style(edge.edge_type)
            if style:
                edge_attrs.append(f'style="{style}"')
            
            attrs_str = f" [{', '.join(edge_attrs)}]" if edge_attrs else ""
            lines.append(f'  "{edge.source}" -> "{edge.target}"{attrs_str};')
        
        lines.append("}")
        return "\n".join(lines)

    def to_mermaid(self) -> str:
        """
        Export graph to Mermaid diagram format.

        Returns:
            Mermaid diagram string
        """
        lines = ["graph LR"]
        
        # Add nodes with styling
        for node in self.nodes:
            label = node.label.replace('"', "'")
            shape = self._get_mermaid_shape(node.status)
            lines.append(f'    {node.id}["{label}"]')
        
        # Add edges
        for edge in self.edges:
            label_str = f'|"{edge.label}"|' if edge.label else "|"
            style = self._get_mermaid_edge_style(edge.edge_type)
            lines.append(f"    {edge.source} {label_str} {edge.target}{style}")
        
        return "\n".join(lines)

    def _get_node_color(self, status: str | None) -> str:
        """Get node color based on status."""
        color_map = {
            "completed": "lightgreen",
            "failed": "lightcoral",
            "running": "lightblue",
            "skipped": "lightgray",
            None: "white",
        }
        return color_map.get(status, "white")

    def _get_edge_color(self, edge_type: str) -> str | None:
        """Get edge color based on type."""
        color_map = {
            "gate_pass": "green",
            "gate_fail": "red",
            "dependency": "blue",
            "default": None,
        }
        return color_map.get(edge_type)

    def _get_edge_style(self, edge_type: str) -> str | None:
        """Get edge style based on type."""
        style_map = {
            "gate_pass": "solid",
            "gate_fail": "dashed",
            "dependency": "dotted",
            "default": None,
        }
        return style_map.get(edge_type)

    def _get_mermaid_shape(self, status: str | None) -> str:
        """Get Mermaid shape based on status."""
        # Mermaid shapes are handled via classDef, but for simplicity
        # we'll use standard shapes
        return ""

    def _get_mermaid_edge_style(self, edge_type: str) -> str:
        """Get Mermaid edge style."""
        style_map = {
            "gate_pass": ':::gatePass',
            "gate_fail": ':::gateFail',
            "dependency": ':::dependency',
            "default": "",
        }
        return style_map.get(edge_type, "")


class ExecutionGraphGenerator:
    """Generates execution graphs from workflow event logs."""

    def __init__(self, event_log: WorkflowEventLog | None = None):
        """
        Initialize graph generator.

        Args:
            event_log: Optional WorkflowEventLog instance
        """
        self.event_log = event_log

    def generate_graph(
        self, workflow_id: str, event_log: WorkflowEventLog | None = None
    ) -> ExecutionGraph:
        """
        Generate execution graph from workflow event log.

        Args:
            workflow_id: Workflow ID
            event_log: Optional WorkflowEventLog instance (uses self.event_log if not provided)

        Returns:
            ExecutionGraph instance

        Raises:
            ValueError: If workflow_id is invalid
            WorkflowNotFoundError: If workflow does not exist
            GraphGenerationError: If graph generation fails
            InvalidTraceError: If trace structure is invalid
            EmptyWorkflowError: If workflow has no steps
        """
        # Validate inputs
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        log = event_log or self.event_log
        if not log:
            raise ValueError("WorkflowEventLog instance required")

        # Validate workflow exists
        if not self._workflow_exists(workflow_id, log):
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        # Get execution trace with error handling
        try:
            trace = log.get_execution_trace(workflow_id)
        except FileNotFoundError as e:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found") from e
        except Exception as e:
            raise GraphGenerationError(f"Failed to load trace for workflow {workflow_id}: {e}") from e

        # Validate trace structure
        if not trace or not isinstance(trace, dict):
            raise InvalidTraceError(f"Invalid trace structure for workflow {workflow_id}")

        if not trace.get("steps"):
            raise EmptyWorkflowError(f"Workflow {workflow_id} has no steps")

        # Read events for additional context (non-critical, continue if fails)
        try:
            events = log.read_events(workflow_id)
        except Exception as e:
            logger.warning(f"Failed to read events for workflow {workflow_id}: {e}")
            events = []
        
        # Build graph with error handling
        try:
            graph = ExecutionGraph(workflow_id=workflow_id)
            
            # Create nodes from steps
            steps = trace.get("steps", [])
            if not steps:
                raise EmptyWorkflowError(f"Workflow {workflow_id} has no steps")
            
            for step in steps:
                if not isinstance(step, dict):
                    logger.warning(f"Invalid step structure in workflow {workflow_id}, skipping")
                    continue
                
                step_id = step.get("step_id")
                if not step_id:
                    logger.warning(f"Step missing step_id in workflow {workflow_id}, skipping")
                    continue
                
                try:
                    node = GraphNode(
                        id=step_id,
                        label=self._format_node_label(step),
                        agent=step.get("agent"),
                        action=step.get("action"),
                        status=step.get("status"),
                        duration_ms=step.get("duration_ms"),
                        error=step.get("error"),
                        metadata={
                            "skill_name": step.get("skill_name"),
                            "artifact_paths": step.get("artifact_paths", []),
                        },
                    )
                    graph.nodes.append(node)
                except Exception as e:
                    logger.warning(f"Failed to create node for step {step_id}: {e}")
                    continue
            
            if not graph.nodes:
                raise EmptyWorkflowError(f"Workflow {workflow_id} has no valid steps")
            
            # Create edges from workflow structure and events
            try:
                edges = self._build_edges(trace, events)
                graph.edges.extend(edges)
            except Exception as e:
                logger.warning(f"Failed to build edges for workflow {workflow_id}: {e}")
                # Continue with empty edges rather than failing
        
            # Add metadata
            graph.metadata = {
                "started_at": trace.get("started_at"),
                "ended_at": trace.get("ended_at"),
                "total_steps": len(graph.nodes),
            }
            
            return graph
        except (EmptyWorkflowError, InvalidTraceError):
            # Re-raise these specific errors
            raise
        except Exception as e:
            raise GraphGenerationError(f"Failed to generate graph for workflow {workflow_id}: {e}") from e

    def _format_node_label(self, step: dict[str, Any]) -> str:
        """Format node label from step data."""
        step_id = step.get("step_id", "unknown")
        agent = step.get("agent", "unknown")
        action = step.get("action", "")
        
        # Create readable label
        if action:
            label = f"{step_id}\\n{agent}: {action}"
        else:
            label = f"{step_id}\\n{agent}"
        
        # Add status indicator
        status = step.get("status", "")
        if status and status != "completed":
            label += f"\\n[{status}]"
        
        return label

    def _build_edges(
        self, trace: dict[str, Any], events: list[Any]
    ) -> list[GraphEdge]:
        """
        Build edges from trace and events, handling parallel execution and dependencies.

        Args:
            trace: Execution trace dictionary
            events: List of workflow events

        Returns:
            List of GraphEdge instances
        """
        edges: list[GraphEdge] = []
        steps = trace.get("steps", [])
        
        if not steps:
            return edges
        
        # Build step dependency graph from step.requires fields
        step_deps: dict[str, list[str]] = {}
        step_map: dict[str, dict[str, Any]] = {}
        
        for step in steps:
            step_id = step.get("step_id")
            if not step_id:
                continue
            
            step_map[step_id] = step
            requires = step.get("requires", [])
            if requires:
                step_deps[step_id] = requires
        
        # Create dependency edges from step.requires
        for step_id, deps in step_deps.items():
            for dep in deps:
                # Only create edge if dependency step exists
                if dep in step_map:
                    edges.append(GraphEdge(
                        source=dep,
                        target=step_id,
                        edge_type="dependency",
                        label="requires"
                    ))
        
        # Build step order from events (for sequential fallback)
        step_order: list[str] = []
        for event in events:
            if hasattr(event, "event_type") and event.event_type == "step_start":
                step_id = getattr(event, "step_id", None)
                if step_id and step_id not in step_order:
                    step_order.append(step_id)
        
        # Create sequential edges from event order (fallback when no dependencies)
        for i in range(len(step_order) - 1):
            source = step_order[i]
            target = step_order[i + 1]
            
            # Skip if dependency edge already exists
            if any(e.source == source and e.target == target for e in edges):
                continue
            
            # Check if this is a gate transition
            edge_type = "default"
            label = None
            
            # Look for gate events between steps
            source_step = step_map.get(source)
            if source_step:
                status = source_step.get("status")
                if status == "completed":
                    # Check if gate passed
                    edge_type = "gate_pass"
                    label = "pass"
                elif status == "failed":
                    edge_type = "gate_fail"
                    label = "fail"
            
            edges.append(GraphEdge(
                source=source,
                target=target,
                label=label,
                edge_type=edge_type,
            ))
        
        return edges

    def _workflow_exists(self, workflow_id: str, event_log: WorkflowEventLog) -> bool:
        """
        Check if workflow exists in event log.

        Args:
            workflow_id: Workflow ID to check
            event_log: WorkflowEventLog instance

        Returns:
            True if workflow exists, False otherwise
        """
        try:
            # Try to get trace - if it succeeds, workflow exists
            trace = event_log.get_execution_trace(workflow_id)
            return trace is not None and isinstance(trace, dict)
        except (FileNotFoundError, KeyError):
            return False
        except Exception:
            # For other exceptions, assume workflow might exist
            # Let the actual operation handle the error
            return True

    def save_dot(self, graph: ExecutionGraph, output_path: Path) -> None:
        """
        Save graph to DOT file.

        Args:
            graph: ExecutionGraph instance
            output_path: Output file path

        Raises:
            ValueError: If graph or output_path is invalid
            OSError: If file cannot be written
        """
        if not graph:
            raise ValueError("Graph instance required")
        
        if not output_path:
            raise ValueError("Output path required")
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"Cannot create directory for {output_path}: {e}") from e
        
        try:
            dot_content = graph.to_dot()
            output_path.write_text(dot_content, encoding="utf-8")
        except OSError as e:
            raise OSError(f"Cannot write DOT file to {output_path}: {e}") from e
        except Exception as e:
            raise GraphGenerationError(f"Failed to save DOT file: {e}") from e

    def save_mermaid(self, graph: ExecutionGraph, output_path: Path) -> None:
        """
        Save graph to Mermaid file.

        Args:
            graph: ExecutionGraph instance
            output_path: Output file path

        Raises:
            ValueError: If graph or output_path is invalid
            OSError: If file cannot be written
        """
        if not graph:
            raise ValueError("Graph instance required")
        
        if not output_path:
            raise ValueError("Output path required")
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"Cannot create directory for {output_path}: {e}") from e
        
        try:
            mermaid_content = graph.to_mermaid()
            output_path.write_text(mermaid_content, encoding="utf-8")
        except OSError as e:
            raise OSError(f"Cannot write Mermaid file to {output_path}: {e}") from e
        except Exception as e:
            raise GraphGenerationError(f"Failed to save Mermaid file: {e}") from e
