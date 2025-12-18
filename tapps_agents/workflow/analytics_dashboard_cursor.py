"""
Analytics Dashboard for Cursor Chat Integration

Epic 15 / Story 15.2: Dashboard Rendering in Cursor
Renders analytics dashboard in Cursor chat with formatted display.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from .analytics_accessor import CursorAnalyticsAccessor
from .analytics_visualizer import AnalyticsVisualizer
from .cursor_chat import ChatUpdateSender
from .visual_feedback import VisualFeedbackGenerator


class CursorAnalyticsDashboard:
    """
    Analytics dashboard for Cursor chat integration.
    
    Formats and displays analytics data in Cursor chat interface.
    """

    def __init__(
        self,
        analytics_dir: Path | None = None,
        enable_visual: bool = True,
    ):
        """
        Initialize Cursor analytics dashboard.
        
        Args:
            analytics_dir: Directory for analytics data
            enable_visual: Whether to enable visual enhancements
        """
        self.accessor = CursorAnalyticsAccessor(analytics_dir=analytics_dir)
        self.visualizer = AnalyticsVisualizer(enable_visual=enable_visual)
        self.visual = VisualFeedbackGenerator(enable_visual=enable_visual)
        self.chat_sender = ChatUpdateSender(enable_updates=True)
        
        # Check environment variable
        if os.getenv("TAPPS_AGENTS_ANALYTICS_ENABLED", "true").lower() == "false":
            self.enabled = False
        else:
            self.enabled = True
    
    def render_dashboard(self, days: int = 30) -> str:
        """
        Render full analytics dashboard.
        
        Args:
            days: Number of days to include in dashboard
            
        Returns:
            Formatted dashboard markdown string
        """
        if not self.enabled:
            return "Analytics are disabled. Set TAPPS_AGENTS_ANALYTICS_ENABLED=true to enable."
        
        data = self.accessor.get_dashboard_data()
        
        lines = []
        lines.append("# 📊 Analytics Dashboard")
        lines.append("")
        lines.append(f"**Last Updated:** {data.get('timestamp', datetime.now().isoformat())}")
        lines.append("")
        
        # System Metrics
        lines.append("## 🖥️ System Status")
        lines.append("")
        sys_data = data.get("system", {})
        lines.append(f"- **Total Agents:** {sys_data.get('total_agents', 0)}")
        lines.append(f"- **Active Workflows:** {sys_data.get('active_workflows', 0)}")
        lines.append(f"- **Completed Today:** {sys_data.get('completed_workflows_today', 0)}")
        lines.append(f"- **Failed Today:** {sys_data.get('failed_workflows_today', 0)}")
        lines.append(f"- **Avg Workflow Duration:** {sys_data.get('average_workflow_duration', 0.0):.2f}s")
        lines.append(f"- **CPU Usage:** {sys_data.get('cpu_usage', 0.0):.1f}%")
        lines.append(f"- **Memory Usage:** {sys_data.get('memory_usage', 0.0):.1f}%")
        lines.append(f"- **Disk Usage:** {sys_data.get('disk_usage', 0.0):.1f}%")
        lines.append("")
        
        # Agent Performance
        lines.append("## 🤖 Agent Performance (Top 10)")
        lines.append("")
        agents = sorted(
            data.get("agents", []),
            key=lambda x: x.get("total_executions", 0),
            reverse=True,
        )[:10]
        
        if agents:
            agent_table = self.visualizer.create_metric_table(
                agents,
                columns=["agent_name", "total_executions", "success_rate", "average_duration"],
                title=None,
            )
            lines.append(agent_table)
        else:
            lines.append("No agent data available")
        lines.append("")
        
        # Workflow Performance
        lines.append("## 🔄 Workflow Performance")
        lines.append("")
        workflows = sorted(
            data.get("workflows", []),
            key=lambda x: x.get("total_executions", 0),
            reverse=True,
        )[:10]
        
        if workflows:
            workflow_table = self.visualizer.create_metric_table(
                workflows,
                columns=["workflow_name", "total_executions", "success_rate", "average_duration"],
                title=None,
            )
            lines.append(workflow_table)
        else:
            lines.append("No workflow data available")
        lines.append("")
        
        # Trends Summary
        trends = data.get("trends", {})
        if trends:
            lines.append("## 📈 Trends (Last 30 Days)")
            lines.append("")
            
            # Agent duration trend
            agent_duration_trend = trends.get("agent_duration", [])
            if agent_duration_trend and len(agent_duration_trend) >= 2:
                current = agent_duration_trend[-1].get("values", [0])[-1] if agent_duration_trend[-1].get("values") else 0
                previous = agent_duration_trend[-2].get("values", [0])[-1] if len(agent_duration_trend) >= 2 and agent_duration_trend[-2].get("values") else 0
                lines.append(f"- **Agent Duration:** {self.visualizer.format_trend(current, previous, 's')}")
            
            # Workflow success rate trend
            workflow_success_trend = trends.get("workflow_success_rate", [])
            if workflow_success_trend and len(workflow_success_trend) >= 2:
                current = workflow_success_trend[-1].get("values", [0])[-1] if workflow_success_trend[-1].get("values") else 0
                previous = workflow_success_trend[-2].get("values", [0])[-1] if len(workflow_success_trend) >= 2 and workflow_success_trend[-2].get("values") else 0
                lines.append(f"- **Workflow Success Rate:** {self.visualizer.format_trend(current, previous, '%')}")
        
        return "\n".join(lines)
    
    def display_dashboard(self, days: int = 30) -> None:
        """
        Display dashboard in Cursor chat.
        
        Args:
            days: Number of days to include
        """
        dashboard = self.render_dashboard(days=days)
        self.chat_sender.send_update(dashboard)
    
    def get_agent_summary(self, agent_id: str | None = None, days: int = 30) -> str:
        """
        Get formatted agent performance summary.
        
        Args:
            agent_id: Optional agent ID to filter
            days: Number of days to look back
            
        Returns:
            Formatted agent summary
        """
        if not self.enabled:
            return "Analytics are disabled."
        
        agents = self.accessor.get_agent_metrics(agent_id=agent_id, days=days)
        
        if not agents:
            return f"No agent data available for the last {days} days."
        
        lines = []
        lines.append(f"## 🤖 Agent Performance Summary ({days} days)")
        lines.append("")
        
        # Aggregate summary
        summary = self.accessor.aggregate_metrics(agents, aggregation_type="summary")
        lines.append(f"- **Total Agents:** {summary.get('count', 0)}")
        lines.append(f"- **Total Executions:** {summary.get('total_executions', 0)}")
        lines.append(f"- **Success Rate:** {summary.get('success_rate', 0.0) * 100:.1f}%")
        lines.append(f"- **Avg Duration:** {summary.get('average_duration', 0.0):.2f}s")
        lines.append("")
        
        # Top agents table
        top_agents = sorted(agents, key=lambda x: x.get("total_executions", 0), reverse=True)[:5]
        if top_agents:
            lines.append("### Top 5 Agents by Execution Count")
            lines.append("")
            table = self.visualizer.create_metric_table(
                top_agents,
                columns=["agent_name", "total_executions", "success_rate", "average_duration"],
            )
            lines.append(table)
        
        return "\n".join(lines)
    
    def get_workflow_summary(self, workflow_id: str | None = None, days: int = 30) -> str:
        """
        Get formatted workflow performance summary.
        
        Args:
            workflow_id: Optional workflow ID to filter
            days: Number of days to look back
            
        Returns:
            Formatted workflow summary
        """
        if not self.enabled:
            return "Analytics are disabled."
        
        workflows = self.accessor.get_workflow_metrics(workflow_id=workflow_id, days=days)
        
        if not workflows:
            return f"No workflow data available for the last {days} days."
        
        lines = []
        lines.append(f"## 🔄 Workflow Performance Summary ({days} days)")
        lines.append("")
        
        # Aggregate summary
        summary = self.accessor.aggregate_metrics(workflows, aggregation_type="summary")
        lines.append(f"- **Total Workflows:** {summary.get('count', 0)}")
        lines.append(f"- **Total Executions:** {summary.get('total_executions', 0)}")
        lines.append(f"- **Success Rate:** {summary.get('success_rate', 0.0) * 100:.1f}%")
        lines.append(f"- **Avg Duration:** {summary.get('average_duration', 0.0):.2f}s")
        lines.append("")
        
        # Top workflows table
        top_workflows = sorted(workflows, key=lambda x: x.get("total_executions", 0), reverse=True)[:5]
        if top_workflows:
            lines.append("### Top 5 Workflows by Execution Count")
            lines.append("")
            table = self.visualizer.create_metric_table(
                top_workflows,
                columns=["workflow_name", "total_executions", "success_rate", "average_duration"],
            )
            lines.append(table)
        
        return "\n".join(lines)

