"""
Analytics Alerts and Export System

Epic 15 / Story 15.5: Analytics Alerts and Export
Manages alerts for analytics thresholds and exports analytics data.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .analytics_accessor import CursorAnalyticsAccessor
from .cursor_chat import ChatUpdateSender


class AlertSeverity(Enum):
    """Alert severity levels."""
    
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AlertCondition:
    """Alert condition configuration."""
    
    metric_type: str  # "agent_success_rate", "workflow_duration", etc.
    threshold: float
    condition: str  # "above", "below", "change"
    severity: AlertSeverity = AlertSeverity.WARNING
    enabled: bool = True


@dataclass
class Alert:
    """Alert instance."""
    
    condition: AlertCondition
    current_value: float
    threshold: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    severity: AlertSeverity = AlertSeverity.WARNING


class AnalyticsAlertManager:
    """
    Manages analytics alerts and notifications.
    
    Checks metrics against thresholds and triggers alerts.
    """

    def __init__(
        self,
        accessor: CursorAnalyticsAccessor | None = None,
        config_file: Path | None = None,
    ):
        """
        Initialize alert manager.
        
        Args:
            accessor: Analytics accessor instance
            config_file: Path to alert configuration file
        """
        self.accessor = accessor or CursorAnalyticsAccessor()
        self.chat_sender = ChatUpdateSender(enable_updates=True)
        
        if config_file is None:
            config_file = Path(".tapps-agents/analytics_alerts.json")
        self.config_file = config_file
        
        self.conditions: list[AlertCondition] = []
        self.load_config()
    
    def load_config(self) -> None:
        """Load alert configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    data = json.load(f)
                    self.conditions = [
                        AlertCondition(
                            metric_type=c["metric_type"],
                            threshold=c["threshold"],
                            condition=c["condition"],
                            severity=AlertSeverity(c.get("severity", "warning")),
                            enabled=c.get("enabled", True),
                        )
                        for c in data.get("conditions", [])
                    ]
            except Exception as e:
                print(f"Error loading alert config: {e}")
                self.conditions = []
        else:
            # Default conditions
            self.conditions = [
                AlertCondition(
                    metric_type="agent_success_rate",
                    threshold=0.8,
                    condition="below",
                    severity=AlertSeverity.WARNING,
                ),
                AlertCondition(
                    metric_type="workflow_success_rate",
                    threshold=0.7,
                    condition="below",
                    severity=AlertSeverity.CRITICAL,
                ),
            ]
            self.save_config()
    
    def save_config(self) -> None:
        """Save alert configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "conditions": [
                {
                    "metric_type": c.metric_type,
                    "threshold": c.threshold,
                    "condition": c.condition,
                    "severity": c.severity.value,
                    "enabled": c.enabled,
                }
                for c in self.conditions
            ]
        }
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def check_alerts(self) -> list[Alert]:
        """
        Check all alert conditions and return triggered alerts.
        
        Returns:
            List of triggered alerts
        """
        alerts = []
        
        for condition in self.conditions:
            if not condition.enabled:
                continue
            
            alert = self._check_condition(condition)
            if alert:
                alerts.append(alert)
        
        return alerts
    
    def _check_condition(self, condition: AlertCondition) -> Alert | None:
        """
        Check a single alert condition.
        
        Args:
            condition: Alert condition to check
            
        Returns:
            Alert if condition triggered, None otherwise
        """
        try:
            # Get current metric value
            current_value = self._get_metric_value(condition.metric_type)
            
            if current_value is None:
                return None
            
            # Check condition
            triggered = False
            if condition.condition == "below" and current_value < condition.threshold:
                triggered = True
            elif condition.condition == "above" and current_value > condition.threshold:
                triggered = True
            
            if triggered:
                message = self._format_alert_message(condition, current_value)
                return Alert(
                    condition=condition,
                    current_value=current_value,
                    threshold=condition.threshold,
                    message=message,
                    severity=condition.severity,
                )
        
        except Exception as e:
            print(f"Error checking alert condition: {e}")
        
        return None
    
    def _get_metric_value(self, metric_type: str) -> float | None:
        """
        Get current value for a metric type.
        
        Args:
            metric_type: Type of metric
            
        Returns:
            Current metric value or None
        """
        if metric_type == "agent_success_rate":
            agents = self.accessor.get_agent_metrics(days=7)
            if agents:
                summary = self.accessor.aggregate_metrics(agents, "summary")
                return summary.get("success_rate", 0.0)
        
        elif metric_type == "workflow_success_rate":
            workflows = self.accessor.get_workflow_metrics(days=7)
            if workflows:
                summary = self.accessor.aggregate_metrics(workflows, "summary")
                return summary.get("success_rate", 0.0)
        
        elif metric_type == "agent_duration":
            agents = self.accessor.get_agent_metrics(days=7)
            if agents:
                summary = self.accessor.aggregate_metrics(agents, "summary")
                return summary.get("average_duration", 0.0)
        
        elif metric_type == "workflow_duration":
            workflows = self.accessor.get_workflow_metrics(days=7)
            if workflows:
                summary = self.accessor.aggregate_metrics(workflows, "summary")
                return summary.get("average_duration", 0.0)
        
        return None
    
    def _format_alert_message(self, condition: AlertCondition, current_value: float) -> str:
        """
        Format alert message.
        
        Args:
            condition: Alert condition
            current_value: Current metric value
            
        Returns:
            Formatted alert message
        """
        severity_emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.CRITICAL: "🚨",
        }
        
        emoji = severity_emoji.get(condition.severity, "⚠️")
        
        if condition.condition == "below":
            message = (
                f"{emoji} **Alert:** {condition.metric_type} is {current_value:.2%} "
                f"(below threshold of {condition.threshold:.2%})"
            )
        else:
            message = (
                f"{emoji} **Alert:** {condition.metric_type} is {current_value:.2%} "
                f"(above threshold of {condition.threshold:.2%})"
            )
        
        return message
    
    def send_alerts(self, alerts: list[Alert] | None = None) -> None:
        """
        Send alerts to Cursor chat.
        
        Args:
            alerts: List of alerts to send (checks all if None)
        """
        if alerts is None:
            alerts = self.check_alerts()
        
        for alert in alerts:
            self.chat_sender.send_update(alert.message)


class AnalyticsExporter:
    """
    Exports analytics data to various formats.
    """

    def __init__(self, accessor: CursorAnalyticsAccessor | None = None):
        """
        Initialize exporter.
        
        Args:
            accessor: Analytics accessor instance
        """
        self.accessor = accessor or CursorAnalyticsAccessor()
    
    def export_json(
        self,
        output_file: Path | None = None,
        include_trends: bool = True,
    ) -> Path:
        """
        Export analytics data as JSON.
        
        Args:
            output_file: Output file path (auto-generated if None)
            include_trends: Whether to include trend data
            
        Returns:
            Path to exported file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(f".tapps-agents/analytics_export_{timestamp}.json")
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.accessor.get_dashboard_data()
        
        if not include_trends:
            data.pop("trends", None)
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "data": data,
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return output_file
    
    def export_markdown(
        self,
        output_file: Path | None = None,
    ) -> Path:
        """
        Export analytics data as formatted markdown report.
        
        Args:
            output_file: Output file path (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(f".tapps-agents/analytics_report_{timestamp}.md")
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        from .analytics_dashboard_cursor import CursorAnalyticsDashboard
        
        dashboard = CursorAnalyticsDashboard()
        report = dashboard.render_dashboard()
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        return output_file
    
    def export_text(
        self,
        output_file: Path | None = None,
    ) -> Path:
        """
        Export analytics data as plain text report.
        
        Args:
            output_file: Output file path (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(f".tapps-agents/analytics_report_{timestamp}.txt")
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.accessor.get_dashboard_data()
        
        lines = []
        lines.append("Analytics Report")
        lines.append("=" * 60)
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append("")
        
        # System metrics
        sys_data = data.get("system", {})
        lines.append("System Status:")
        lines.append(f"  Total Agents: {sys_data.get('total_agents', 0)}")
        lines.append(f"  Active Workflows: {sys_data.get('active_workflows', 0)}")
        lines.append(f"  Completed Today: {sys_data.get('completed_workflows_today', 0)}")
        lines.append("")
        
        # Agent metrics
        agents = data.get("agents", [])
        lines.append(f"Agent Performance ({len(agents)} agents):")
        for agent in sorted(agents, key=lambda x: x.get("total_executions", 0), reverse=True)[:10]:
            lines.append(
                f"  {agent.get('agent_name', 'Unknown')}: "
                f"{agent.get('total_executions', 0)} executions, "
                f"{agent.get('success_rate', 0.0) * 100:.1f}% success"
            )
        lines.append("")
        
        # Workflow metrics
        workflows = data.get("workflows", [])
        lines.append(f"Workflow Performance ({len(workflows)} workflows):")
        for workflow in sorted(workflows, key=lambda x: x.get("total_executions", 0), reverse=True)[:10]:
            lines.append(
                f"  {workflow.get('workflow_name', 'Unknown')}: "
                f"{workflow.get('total_executions', 0)} executions, "
                f"{workflow.get('success_rate', 0.0) * 100:.1f}% success"
            )
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        return output_file

