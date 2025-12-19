"""
Analytics Integration Helper for Cursor

Epic 15: Analytics Dashboard Integration
Provides easy access to analytics features from Cursor chat.
"""

from __future__ import annotations

from pathlib import Path

from .analytics_alerts import AnalyticsAlertManager, AnalyticsExporter
from .analytics_dashboard_cursor import CursorAnalyticsDashboard
from .analytics_query_parser import AnalyticsQueryParser


def handle_analytics_query(query: str, project_root: Path | None = None) -> str:
    """
    Handle analytics query from natural language.
    
    Args:
        query: Natural language query about analytics
        project_root: Project root directory
        
    Returns:
        Formatted response string
    """
    parser = AnalyticsQueryParser()
    result = parser.execute_query(query)
    
    dashboard = CursorAnalyticsDashboard(analytics_dir=project_root)
    
    # Format response based on query type
    if result["parsed"].query_type == "dashboard":
        return dashboard.render_dashboard()
    
    elif result["parsed"].query_type == "agent":
        return dashboard.get_agent_summary(
            agent_id=result["parsed"].filter_agent_id,
            days=result["parsed"].time_range,
        )
    
    elif result["parsed"].query_type == "workflow":
        return dashboard.get_workflow_summary(
            workflow_id=result["parsed"].filter_workflow_id,
            days=result["parsed"].time_range,
        )
    
    elif result["parsed"].query_type == "system":
        sys_data = result["data"]
        lines = []
        lines.append("## 🖥️ System Status")
        lines.append("")
        lines.append(f"- **Total Agents:** {sys_data.get('total_agents', 0)}")
        lines.append(f"- **Active Workflows:** {sys_data.get('active_workflows', 0)}")
        lines.append(f"- **Completed Today:** {sys_data.get('completed_workflows_today', 0)}")
        lines.append(f"- **Failed Today:** {sys_data.get('failed_workflows_today', 0)}")
        return "\n".join(lines)
    
    else:
        return f"Query executed: {query}\n\nResult: {result.get('data', 'No data')}"


def show_analytics_dashboard(project_root: Path | None = None, days: int = 30) -> None:
    """
    Display analytics dashboard in Cursor chat.
    
    Args:
        project_root: Project root directory
        days: Number of days to include
    """
    dashboard = CursorAnalyticsDashboard(analytics_dir=project_root)
    dashboard.display_dashboard(days=days)


def check_analytics_alerts(project_root: Path | None = None) -> None:
    """
    Check and display analytics alerts.
    
    Args:
        project_root: Project root directory
    """
    manager = AnalyticsAlertManager()
    alerts = manager.check_alerts()
    
    from ..core.unicode_safe import safe_print
    if alerts:
        manager.send_alerts(alerts)
    else:
        safe_print("\n[OK] No alerts triggered.\n")


def export_analytics(
    format: str = "markdown",
    output_file: Path | None = None,
    project_root: Path | None = None,
) -> Path:
    """
    Export analytics data.
    
    Args:
        format: Export format ("json", "markdown", "text")
        output_file: Output file path (auto-generated if None)
        project_root: Project root directory
        
    Returns:
        Path to exported file
    """
    exporter = AnalyticsExporter()
    
    if format == "json":
        return exporter.export_json(output_file=output_file)
    elif format == "markdown":
        return exporter.export_markdown(output_file=output_file)
    elif format == "text":
        return exporter.export_text(output_file=output_file)
    else:
        raise ValueError(f"Unknown export format: {format}")

