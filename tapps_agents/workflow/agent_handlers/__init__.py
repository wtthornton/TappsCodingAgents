"""
Agent Execution Handlers

This module provides agent-specific execution handlers using the Strategy Pattern
to reduce complexity in WorkflowExecutor._execute_step.

Epic 20: Complexity Reduction - Story 20.1
"""

from .analyst_handler import AnalystHandler
from .architect_handler import ArchitectHandler
from .base import AgentExecutionHandler
from .debugger_handler import DebuggerHandler
from .designer_handler import DesignerHandler
from .documenter_handler import DocumenterHandler
from .enhancer_handler import EnhancerHandler
from .implementer_handler import ImplementerHandler
from .ops_handler import OpsHandler
from .orchestrator_handler import OrchestratorHandler
from .planner_handler import PlannerHandler
from .registry import AgentHandlerRegistry
from .reviewer_handler import ReviewerHandler
from .tester_handler import TesterHandler

__all__ = [
    "AgentExecutionHandler",
    "AgentHandlerRegistry",
    "AnalystHandler",
    "ArchitectHandler",
    "DebuggerHandler",
    "DesignerHandler",
    "DocumenterHandler",
    "EnhancerHandler",
    "ImplementerHandler",
    "OpsHandler",
    "OrchestratorHandler",
    "PlannerHandler",
    "ReviewerHandler",
    "TesterHandler",
]

