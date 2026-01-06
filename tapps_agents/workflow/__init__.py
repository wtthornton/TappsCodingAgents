"""Workflow Engine - YAML-based workflow orchestration.

2025 Enhancements:
- DurableWorkflowState: Event-sourced state with checkpoints for resume
- Automatic recovery from any failure point
- Complete audit trail via event log
"""

# Foreground Agent Artifacts (Epic 2)
from .code_artifact import CodeArtifact, CodeChange
from .context_artifact import (
    ContextArtifact,
    ContextQuery,
    LibraryCacheEntry,
    ProjectProfile,
)
from .dependency_resolver import DependencyGraph, DependencyResolver
from .design_artifact import Component, DesignArtifact
from .detector import (
    ProjectCharacteristics,
    ProjectDetector,
    ProjectType,
    WorkflowTrack,
)

# Background Agents removed - Artifact classes remain (data structures only)
# Background Agent Artifacts (data structures, not Background Agent implementations)
from .docs_artifact import DocFileResult, DocumentationArtifact

# 2025: Durable Workflow State Machine
from .durable_state import (
    Checkpoint,
    DurableWorkflowState,
    EventStore,
    EventType,
    WorkflowEvent as DurableWorkflowEvent,
    get_durable_state,
    resume_workflow,
)
from .enhancement_artifact import EnhancementArtifact, EnhancementStage
from .event_log import WorkflowEvent, WorkflowEventLog
from .executor import WorkflowExecutor
from .logging_helper import WorkflowLogger
from .messaging import (
    FileMessageBus,
    StatusUpdateMessage,
    TaskAssignmentMessage,
    TaskCompleteMessage,
)
from .models import (
    Artifact,
    Workflow,
    WorkflowSettings,
    WorkflowState,
    WorkflowStep,
    WorkflowType,
)
from .ops_artifact import (
    ComplianceCheck,
    DeploymentStep,
    InfrastructureFile,
    OperationsArtifact,
    SecurityIssue,
)
from .parser import WorkflowParser
from .planning_artifact import PlanningArtifact, UserStory
from .progress_monitor import ProgressMetrics, WorkflowProgressMonitor
from .quality_artifact import QualityArtifact, ToolResult
from .recommender import (
    WorkflowRecommendation,
    WorkflowRecommender,
)

# Result Aggregation (Epic 2)
from .result_aggregator import Conflict, ResultAggregator
from .review_artifact import ReviewArtifact, ReviewComment
from .schema_validator import SchemaVersion, ValidationError, WorkflowSchemaValidator
from .testing_artifact import CoverageSummary, TestingArtifact, TestResult

__all__ = [
    "WorkflowParser",
    "WorkflowExecutor",
    "Workflow",
    "WorkflowStep",
    "WorkflowState",
    "WorkflowType",
    "Artifact",
    "WorkflowSettings",
    "FileMessageBus",
    "TaskAssignmentMessage",
    "StatusUpdateMessage",
    "TaskCompleteMessage",
    "WorkflowLogger",
    "ProjectDetector",
    "ProjectType",
    "ProjectCharacteristics",
    "WorkflowTrack",
    "WorkflowRecommender",
    "WorkflowRecommendation",
    # Background Agents removed - Artifact classes remain (data structures only)
    "DocumentationArtifact",
    "DocFileResult",
    "OperationsArtifact",
    "SecurityIssue",
    "ComplianceCheck",
    "DeploymentStep",
    "InfrastructureFile",
    "ContextArtifact",
    "LibraryCacheEntry",
    "ContextQuery",
    "ProjectProfile",
    "QualityArtifact",
    "ToolResult",
    "TestingArtifact",
    "TestResult",
    "CoverageSummary",
    # Foreground Agent Artifacts
    "CodeArtifact",
    "CodeChange",
    "DesignArtifact",
    "Component",
    "ReviewArtifact",
    "ReviewComment",
    "PlanningArtifact",
    "UserStory",
    "EnhancementArtifact",
    "EnhancementStage",
    # Result Aggregation
    "ResultAggregator",
    "Conflict",
    # Epic 5: Workflow Engine Enhancements
    "WorkflowSchemaValidator",
    "SchemaVersion",
    "ValidationError",
    "DependencyResolver",
    "DependencyGraph",
    "WorkflowEventLog",
    "WorkflowEvent",
    "WorkflowProgressMonitor",
    "ProgressMetrics",
    # 2025: Durable Workflow State Machine
    "DurableWorkflowState",
    "DurableWorkflowEvent",
    "EventStore",
    "EventType",
    "Checkpoint",
    "get_durable_state",
    "resume_workflow",
]
