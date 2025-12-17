"""
Analytics Query Parser for Natural Language Queries

Epic 15 / Story 15.4: Analytics Queries and Natural Language
Parses natural language queries about analytics data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .analytics_accessor import CursorAnalyticsAccessor


@dataclass
class AnalyticsQuery:
    """Parsed analytics query."""
    
    query_type: str  # "agent", "workflow", "system", "trend", "dashboard"
    metric: str | None = None  # "performance", "duration", "success_rate", etc.
    filter_agent_id: str | None = None
    filter_workflow_id: str | None = None
    time_range: int = 30  # days
    aggregation: str | None = None  # "summary", "totals", "averages"
    comparison: bool = False  # Whether to compare periods


class AnalyticsQueryParser:
    """
    Parses natural language queries about analytics.
    
    Supports common question patterns and extracts query parameters.
    """

    def __init__(self, accessor: CursorAnalyticsAccessor | None = None):
        """
        Initialize query parser.
        
        Args:
            accessor: Analytics accessor instance
        """
        self.accessor = accessor or CursorAnalyticsAccessor()
        
        # Query patterns
        self.patterns = {
            "agent": [
                r"agent",
                r"agents?",
                r"how (many|much|are) (the )?agents?",
                r"agent performance",
                r"agent metrics",
            ],
            "workflow": [
                r"workflow",
                r"workflows?",
                r"how (many|much|are) (the )?workflows?",
                r"workflow performance",
                r"workflow metrics",
            ],
            "system": [
                r"system",
                r"system status",
                r"system metrics",
                r"how (is|are) (the )?system",
            ],
            "trend": [
                r"trend",
                r"trends?",
                r"how (are|is) (things|metrics) (changing|trending)",
                r"performance (over time|trend)",
            ],
            "dashboard": [
                r"dashboard",
                r"analytics",
                r"show (me )?(the )?(analytics|dashboard)",
                r"what (are|is) (the )?(analytics|metrics)",
            ],
        }
        
        # Metric patterns
        self.metric_patterns = {
            "performance": [r"performance", r"how (well|good)"],
            "duration": [r"duration", r"how long", r"time"],
            "success_rate": [r"success", r"success rate", r"how (many|much) (succeed|success)"],
            "executions": [r"executions?", r"how many", r"count"],
        }
        
        # Time range patterns
        self.time_patterns = {
            7: [r"last week", r"7 days", r"week"],
            30: [r"last month", r"30 days", r"month"],
            90: [r"last (3 months|quarter)", r"90 days", r"quarter"],
        }
    
    def parse(self, query: str) -> AnalyticsQuery:
        """
        Parse natural language query.
        
        Args:
            query: Natural language query string
            
        Returns:
            Parsed AnalyticsQuery
        """
        query_lower = query.lower().strip()
        
        # Determine query type
        query_type = "dashboard"  # default
        for qtype, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    query_type = qtype
                    break
            if query_type != "dashboard":
                break
        
        # Extract metric
        metric = None
        for metric_name, patterns in self.metric_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    metric = metric_name
                    break
            if metric:
                break
        
        # Extract time range
        time_range = 30  # default
        for days, patterns in self.time_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    time_range = days
                    break
            if time_range != 30:
                break
        
        # Extract agent ID (simple pattern)
        filter_agent_id = None
        agent_match = re.search(r"agent[:\s]+([a-z0-9_-]+)", query_lower)
        if agent_match:
            filter_agent_id = agent_match.group(1)
        
        # Extract workflow ID
        filter_workflow_id = None
        workflow_match = re.search(r"workflow[:\s]+([a-z0-9_-]+)", query_lower)
        if workflow_match:
            filter_workflow_id = workflow_match.group(1)
        
        # Check for comparison
        comparison = bool(re.search(r"compare|vs|versus|difference", query_lower))
        
        # Determine aggregation
        aggregation = None
        if re.search(r"summary|overall|total", query_lower):
            aggregation = "summary"
        elif re.search(r"average|avg|mean", query_lower):
            aggregation = "averages"
        elif re.search(r"total|sum", query_lower):
            aggregation = "totals"
        
        return AnalyticsQuery(
            query_type=query_type,
            metric=metric,
            filter_agent_id=filter_agent_id,
            filter_workflow_id=filter_workflow_id,
            time_range=time_range,
            aggregation=aggregation,
            comparison=comparison,
        )
    
    def execute_query(self, query: str) -> dict[str, Any]:
        """
        Parse and execute query.
        
        Args:
            query: Natural language query string
            
        Returns:
            Query result dictionary
        """
        parsed = self.parse(query)
        
        result = {
            "query": query,
            "parsed": parsed,
            "data": None,
            "formatted": "",
        }
        
        if parsed.query_type == "agent":
            data = self.accessor.get_agent_metrics(
                agent_id=parsed.filter_agent_id,
                days=parsed.time_range,
            )
            result["data"] = data
            
            if parsed.aggregation:
                aggregated = self.accessor.aggregate_metrics(data, parsed.aggregation)
                result["aggregated"] = aggregated
        
        elif parsed.query_type == "workflow":
            data = self.accessor.get_workflow_metrics(
                workflow_id=parsed.filter_workflow_id,
                days=parsed.time_range,
            )
            result["data"] = data
            
            if parsed.aggregation:
                aggregated = self.accessor.aggregate_metrics(data, parsed.aggregation)
                result["aggregated"] = aggregated
        
        elif parsed.query_type == "system":
            data = self.accessor.get_system_metrics()
            result["data"] = data
        
        elif parsed.query_type == "trend":
            # Get trends for common metrics
            trends = {}
            for metric_type in ["agent_duration", "workflow_duration", "agent_success_rate", "workflow_success_rate"]:
                trend_data = self.accessor.get_trends(metric_type, days=parsed.time_range)
                trends[metric_type] = trend_data
            result["data"] = trends
        
        elif parsed.query_type == "dashboard":
            data = self.accessor.get_dashboard_data()
            result["data"] = data
        
        return result
    
    def get_suggestions(self, query: str) -> list[str]:
        """
        Get query suggestions based on input.
        
        Args:
            query: Partial or ambiguous query
            
        Returns:
            List of suggested queries
        """
        suggestions = []
        
        query_lower = query.lower().strip()
        
        # If query is very short or empty, suggest common queries
        if len(query_lower) < 3:
            suggestions = [
                "show analytics dashboard",
                "agent performance",
                "workflow performance",
                "system status",
                "trends last 30 days",
            ]
        # If query mentions agent but no specific agent, suggest agent queries
        elif "agent" in query_lower and not re.search(r"agent[:\s]+[a-z0-9_-]+", query_lower):
            suggestions = [
                "agent performance last 30 days",
                "top agents by execution count",
                "agent success rate",
            ]
        # If query mentions workflow but no specific workflow, suggest workflow queries
        elif "workflow" in query_lower and not re.search(r"workflow[:\s]+[a-z0-9_-]+", query_lower):
            suggestions = [
                "workflow performance last 30 days",
                "top workflows by execution count",
                "workflow success rate",
            ]
        else:
            suggestions = [
                "Try: 'show analytics dashboard'",
                "Try: 'agent performance'",
                "Try: 'workflow performance'",
                "Try: 'system status'",
            ]
        
        return suggestions

