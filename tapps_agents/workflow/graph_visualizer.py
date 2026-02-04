"""
Graph Visualizer

Provides visualization utilities for execution graphs.
"""

from __future__ import annotations

from pathlib import Path

from .execution_graph import ExecutionGraph


class GraphVisualizer:
    """Visualization utilities for execution graphs."""

    @staticmethod
    def generate_html_view(graph: ExecutionGraph, output_path: Path) -> None:
        """
        Generate HTML view of execution graph.

        Args:
            graph: ExecutionGraph instance
            output_path: Output HTML file path
        """
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Execution Graph - {graph.workflow_id}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        .graph-container {{
            border: 1px solid #ddd;
            padding: 20px;
            margin: 20px 0;
        }}
        .metadata {{
            background: #f5f5f5;
            padding: 10px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <h1>Execution Graph: {graph.workflow_id}</h1>
    
    <div class="metadata">
        <h3>Metadata</h3>
        <ul>
            <li>Total Steps: {graph.metadata.get('total_steps', 0)}</li>
            <li>Started: {graph.metadata.get('started_at', 'N/A')}</li>
            <li>Ended: {graph.metadata.get('ended_at', 'N/A')}</li>
        </ul>
    </div>
    
    <div class="graph-container">
        <div class="mermaid">
{graph.to_mermaid()}
        </div>
    </div>
    
    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
</body>
</html>"""
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding="utf-8")

    @staticmethod
    def generate_summary(graph: ExecutionGraph) -> str:
        """
        Generate text summary of execution graph.

        Args:
            graph: ExecutionGraph instance

        Returns:
            Text summary string
        """
        lines = [
            f"Execution Graph: {graph.workflow_id}",
            "=" * 50,
            "",
            f"Total Steps: {len(graph.nodes)}",
            f"Total Edges: {len(graph.edges)}",
            "",
        ]
        
        if graph.metadata:
            lines.append("Metadata:")
            for key, value in graph.metadata.items():
                lines.append(f"  {key}: {value}")
            lines.append("")
        
        lines.append("Nodes:")
        for node in graph.nodes:
            status_indicator = f" [{node.status}]" if node.status else ""
            duration_str = f" ({node.duration_ms:.0f}ms)" if node.duration_ms else ""
            error_str = " [ERROR]" if node.error else ""
            lines.append(
                f"  - {node.id}: {node.label}{status_indicator}{duration_str}{error_str}"
            )
        
        lines.append("")
        lines.append("Edges:")
        for edge in graph.edges:
            label_str = f" ({edge.label})" if edge.label else ""
            lines.append(f"  - {edge.source} -> {edge.target}{label_str}")
        
        return "\n".join(lines)

    @staticmethod
    def save_summary(graph: ExecutionGraph, output_path: Path) -> None:
        """
        Save text summary to file.

        Args:
            graph: ExecutionGraph instance
            output_path: Output file path
        """
        summary = GraphVisualizer.generate_summary(graph)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(summary, encoding="utf-8")
