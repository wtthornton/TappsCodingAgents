"""
TappsCodingAgents Performance Insight Dashboard.

Generates a self-contained HTML dashboard showing metrics from all
tapps-agents subsystems: agents, experts, cache/RAG, quality gates,
workflows, adaptive learning, and health checks.

Usage:
    tapps-agents dashboard              # Generate and open in browser
    tapps-agents dashboard --no-open    # Generate only
    tapps-agents dashboard --days 60    # Custom time range
"""

from .generator import DashboardGenerator

__all__ = ["DashboardGenerator"]
