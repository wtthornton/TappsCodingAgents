"""
Analytics Visualization System

Epic 15 / Story 15.3: Analytics Visualization
Creates text-based charts and visualizations for analytics data in Cursor chat.
"""

from __future__ import annotations

from typing import Any

from .visual_feedback import VisualFeedbackGenerator


class AnalyticsVisualizer:
    """
    Creates visualizations for analytics data.
    
    Supports text-based charts, trend visualization, and metric comparisons.
    """

    def __init__(self, enable_visual: bool = True):
        """
        Initialize analytics visualizer.
        
        Args:
            enable_visual: Whether to enable visual enhancements
        """
        self.enable_visual = enable_visual
        self.visual = VisualFeedbackGenerator(enable_visual=enable_visual)
    
    def create_bar_chart(
        self,
        data: list[tuple[str, float]],
        max_width: int = 40,
        show_values: bool = True,
    ) -> str:
        """
        Create ASCII bar chart.
        
        Args:
            data: List of (label, value) tuples
            max_width: Maximum width of bars
            show_values: Whether to show values
            
        Returns:
            Formatted bar chart string
        """
        if not data:
            return "No data available"
        
        # Find max value for scaling
        max_value = max(v for _, v in data) if data else 1.0
        
        lines = []
        for label, value in data:
            # Calculate bar width
            bar_width = int((value / max_value) * max_width) if max_value > 0 else 0
            # Use ASCII-safe characters for Windows compatibility
            bar = "=" * bar_width + "-" * (max_width - bar_width)
            
            if show_values:
                lines.append(f"{label:20} [{bar}] {value:.2f}")
            else:
                lines.append(f"{label:20} [{bar}]")
        
        return "\n".join(lines)
    
    def create_line_chart(
        self,
        data: list[tuple[str, float]],
        height: int = 10,
        show_values: bool = True,
    ) -> str:
        """
        Create ASCII line chart.
        
        Args:
            data: List of (label, value) tuples
            height: Height of chart in lines
            show_values: Whether to show values
            
        Returns:
            Formatted line chart string
        """
        if not data or len(data) < 2:
            return "Insufficient data for line chart (need at least 2 points)"
        
        # Find min and max values
        values = [v for _, v in data]
        min_value = min(values)
        max_value = max(values)
        value_range = max_value - min_value if max_value > min_value else 1.0
        
        # Create chart grid
        chart_lines = [[" "] * len(data) for _ in range(height)]
        
        # Plot points
        for i, (_, value) in enumerate(data):
            # Normalize value to chart height
            normalized = (value - min_value) / value_range
            y_pos = int(normalized * (height - 1))
            y_pos = height - 1 - y_pos  # Flip Y axis
            
            chart_lines[y_pos][i] = "●"
            
            # Draw line to next point
            if i < len(data) - 1:
                next_value = data[i + 1][1]
                next_normalized = (next_value - min_value) / value_range
                next_y_pos = int(next_normalized * (height - 1))
                next_y_pos = height - 1 - next_y_pos
                
                # Draw line between points
                if abs(next_y_pos - y_pos) > 1:
                    step = 1 if next_y_pos > y_pos else -1
                    for y in range(y_pos, next_y_pos, step):
                        if 0 <= y < height:
                            chart_lines[y][i] = "│"
        
        # Build output
        lines = []
        for row in chart_lines:
            lines.append("".join(row))
        
        if show_values:
            lines.append("")
            lines.append("Values:")
            for label, value in data:
                lines.append(f"  {label}: {value:.2f}")
        
        return "\n".join(lines)
    
    def format_trend(
        self,
        current: float,
        previous: float | None = None,
        unit: str = "",
    ) -> str:
        """
        Format trend indicator.
        
        Args:
            current: Current value
            previous: Previous value (for comparison)
            unit: Unit of measurement
            
        Returns:
            Formatted trend string with emoji
        """
        if previous is None:
            return f"{current:.2f}{unit}"
        
        change = current - previous
        change_pct = (change / previous * 100) if previous != 0 else 0.0
        
        if change > 0:
            emoji = "📈"
            direction = "↑"
        elif change < 0:
            emoji = "📉"
            direction = "↓"
        else:
            emoji = "➡️"
            direction = "→"
        
        return (
            f"{emoji} {current:.2f}{unit} {direction} "
            f"{abs(change):.2f}{unit} ({abs(change_pct):.1f}%)"
        )
    
    def compare_periods(
        self,
        current_period: dict[str, Any],
        previous_period: dict[str, Any],
        metric_name: str,
    ) -> str:
        """
        Compare metrics between two periods.
        
        Args:
            current_period: Current period metrics
            previous_period: Previous period metrics
            metric_name: Name of metric to compare
            
        Returns:
            Formatted comparison string
        """
        current_value = current_period.get(metric_name, 0)
        previous_value = previous_period.get(metric_name, 0)
        
        change = current_value - previous_value
        change_pct = (change / previous_value * 100) if previous_value != 0 else 0.0
        
        if change > 0:
            indicator = "✅"
            trend = "improved"
        elif change < 0:
            indicator = "⚠️"
            trend = "declined"
        else:
            indicator = "➡️"
            trend = "unchanged"
        
        return (
            f"{indicator} **{metric_name}**: {current_value:.2f} "
            f"({trend} by {abs(change):.2f}, {abs(change_pct):.1f}%)"
        )
    
    def create_metric_table(
        self,
        metrics: list[dict[str, Any]],
        columns: list[str],
        title: str | None = None,
    ) -> str:
        """
        Create formatted table from metrics.
        
        Args:
            metrics: List of metric dictionaries
            columns: List of column names to display
            title: Optional table title
            
        Returns:
            Formatted markdown table
        """
        if not metrics:
            return "No data available"
        
        lines = []
        
        if title:
            lines.append(f"### {title}")
            lines.append("")
        
        # Header
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"
        lines.append(header)
        lines.append(separator)
        
        # Rows
        for metric in metrics:
            row_values = []
            for col in columns:
                value = metric.get(col, "")
                if isinstance(value, float):
                    value = f"{value:.2f}"
                elif value is None:
                    value = "-"
                else:
                    value = str(value)
                row_values.append(value)
            
            row = "| " + " | ".join(row_values) + " |"
            lines.append(row)
        
        return "\n".join(lines)

