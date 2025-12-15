"""Workflow Engine - YAML-based workflow orchestration."""

from .detector import (
    ProjectCharacteristics,
    ProjectDetector,
    ProjectType,
    WorkflowTrack,
)
from .executor import WorkflowExecutor
from .models import (
    Artifact,
    Workflow,
    WorkflowSettings,
    WorkflowState,
    WorkflowStep,
    WorkflowType,
)
from .parser import WorkflowParser
from .recommender import (
    WorkflowRecommendation,
    WorkflowRecommender,
)
from .messaging import (
    FileMessageBus,
    TaskAssignmentMessage,
    StatusUpdateMessage,
    TaskCompleteMessage,
)
from .logging_helper import WorkflowLogger
from .schema_validator import WorkflowSchemaValidator, SchemaVersion, ValidationError
from .dependency_resolver import DependencyResolver, DependencyGraph
from .event_log import WorkflowEventLog, WorkflowEvent
from .progress_monitor import WorkflowProgressMonitor, ProgressMetrics

# Background Agents (Epic 2)
from .background_docs_agent import BackgroundDocsAgent
from .background_ops_agent import BackgroundOpsAgent
from .background_context_agent import BackgroundContextAgent
from .background_quality_agent import BackgroundQualityAgent
from .background_testing_agent import BackgroundTestingAgent

# Background Agent Artifacts
from .docs_artifact import DocumentationArtifact, DocFileResult
from .ops_artifact import (
    OperationsArtifact,
    SecurityIssue,
    ComplianceCheck,
    DeploymentStep,
    InfrastructureFile,
)
from .context_artifact import (
    ContextArtifact,
    LibraryCacheEntry,
    ContextQuery,
    ProjectProfile,
)
from .quality_artifact import QualityArtifact, ToolResult
from .testing_artifact import TestingArtifact, TestResult, CoverageSummary

# Foreground Agent Artifacts (Epic 2)
from .code_artifact import CodeArtifact, CodeChange
from .design_artifact import DesignArtifact, Component
from .review_artifact import ReviewArtifact, ReviewComment
from .planning_artifact import PlanningArtifact, UserStory
from .enhancement_artifact import EnhancementArtifact, EnhancementStage

# Result Aggregation (Epic 2)
from .result_aggregator import Conflict, ResultAggregator

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
    # Background Agents
    "BackgroundDocsAgent",
    "BackgroundOpsAgent",
    "BackgroundContextAgent",
    "BackgroundQualityAgent",
    "BackgroundTestingAgent",
    # Background Agent Artifacts
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
]
