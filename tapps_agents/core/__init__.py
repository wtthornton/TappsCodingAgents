"""
Core framework components.

This module provides the foundational components for the TappsCodingAgents framework,
including:

- Base Agent Classes: BaseAgent and related mixins for building custom agents
- Context Management: ContextManager, TieredContextBuilder for managing
  execution context
- Caching: UnifiedCache, AdaptiveCacheConfig for performance optimization
- Learning Systems: AgentLearner, PatternExtractor for agent improvement
- Session Management: SessionManager, TaskMemory for stateful operations
- Resource Management: ResourceAwareExecutor, HardwareProfiler for resource optimization
- Visual Feedback: VisualAnalyzer, UIComparator for UI/UX analysis

All components are designed to work together seamlessly and can be imported
directly from this module.

Example:
    ```python
    from tapps_agents.core import (
        BaseAgent,
        ContextManager,
        UnifiedCache,
        AgentLearner,
    )
    
    # Create agent with learning capabilities
    agent = BaseAgent(name="my_agent")
    learner = AgentLearner(agent=agent)
    ```
"""

from .adaptive_cache_config import (
    AdaptiveCacheConfig,
    AdaptiveCacheSettings,
    ConfigurationChange,
)
from .adaptive_scoring import AdaptiveScoringEngine
from .agent_base import BaseAgent
from .agent_learning import (
    AgentLearner,
    CodePattern,
    FeedbackAnalyzer,
    PatternExtractor,
    PromptOptimizer,
    PromptVariant,
)
from .anonymization import (
    AnonymizationPipeline,
    AnonymizationReport,
)
from .ast_parser import ASTParser
from .best_practice_consultant import (
    BestPracticeAdvice,
    BestPracticeConsultant,
    CachedAdvice,
)
from .browser_controller import (
    BrowserController,
    BrowserType,
    InteractionEvent,
    RenderingMode,
    ScreenshotOptions,
)
from .cache_router import CacheRequest, CacheResponse, CacheType
from .capability_registry import (
    CapabilityMetric,
    CapabilityRegistry,
    LearningIntensity,
    RefinementRecord,
)
from .checkpoint_manager import CheckpointManager, CheckpointStorage, TaskCheckpoint
from .config import ProjectConfig as ProjectConfig
from .config import load_config as load_config
from .context_manager import ContextManager
from .docker_utils import (
    get_container_status,
    run_docker_ps_json,
    run_docker_ps_native,
    run_docker_ps_simple,
)
from .export_schema import (
    ExportSchema,
    ValidationResult,
)
from .hardware_profiler import (
    CacheOptimizationProfile,
    HardwareProfile,
    HardwareProfiler,
)
from .iteration_reducer import IterationPattern, IterationReducer
from .knowledge_graph import (
    GraphQuery,
    KnowledgeGraph,
    RelationshipEdge,
    RelationshipType,
    TaskNode,
)
from .learning_confidence import (
    ConfidenceFactors,
    LearnedExperienceMetrics,
    LearningConfidenceCalculator,
)
from .learning_decision import (
    DecisionResult,
    DecisionSource,
    LearningDecision,
    LearningDecisionEngine,
)
from .learning_export import (
    ExportMetadata,
    LearningDataExporter,
)
from .learning_integration import LearningAwareMixin
from .llm_communicator import LLMCommunicator, LLMHint
from .long_duration_support import (
    DurabilityGuarantee,
    DurabilityLevel,
    FailureRecord,
    FailureRecovery,
    LongDurationManager,
    ProgressSnapshot,
    ProgressTracker,
)
from .memory_integration import MemoryAwareMixin, MemoryContextInjector, MemoryUpdater
from .outcome_tracker import CodeOutcome, OutcomeTracker
from .predictive_gates import FirstPassPrediction, PredictiveQualityGates
from .prompt_quality import PromptQualityAnalyzer, PromptQualityScore
from .resource_aware_executor import (
    AutoPause,
    ExecutionConfig,
    ExecutionMode,
    ExecutionState,
    ResourceAwareExecutor,
    ResourceOptimizer,
)
from .resume_handler import ArtifactValidator, ContextRestorer, ResumeHandler
from .session_manager import (
    AgentSession,
    HealthStatus,
    SessionManager,
    SessionMonitor,
    SessionRecovery,
    SessionState,
    SessionStorage,
)
from .task_memory import (
    MemoryCompressor,
    MemoryIndex,
    MemoryRetriever,
    MemoryStorage,
    TaskMemory,
    TaskMemorySystem,
    TaskOutcome,
)
from .task_state import StateTransition, TaskState, TaskStateManager
from .tiered_context import ContextTier, TieredContextBuilder
from .unified_cache import UnifiedCache, UnifiedCacheStats, create_unified_cache
from .unified_cache_config import UnifiedCacheConfig, UnifiedCacheConfigManager
from .visual_feedback import (
    AccessibilityMetrics,
    LayoutMetrics,
    UIComparator,
    VisualAnalyzer,
    VisualElement,
    VisualElementType,
    VisualFeedback,
    VisualFeedbackCollector,
    VisualPatternLearner,
)
from .visual_feedback import (
    RenderingMode as VisualRenderingMode,
)

__all__ = [
    "BaseAgent",
    "ContextManager",
    "ContextTier",
    "TieredContextBuilder",
    "ASTParser",
    "UnifiedCache",
    "create_unified_cache",
    "UnifiedCacheStats",
    "CacheType",
    "CacheRequest",
    "CacheResponse",
    "HardwareProfile",
    "HardwareProfiler",
    "CacheOptimizationProfile",
    "UnifiedCacheConfig",
    "UnifiedCacheConfigManager",
    "AdaptiveCacheConfig",
    "AdaptiveCacheSettings",
    "ConfigurationChange",
    "SessionManager",
    "AgentSession",
    "SessionState",
    "HealthStatus",
    "SessionStorage",
    "SessionMonitor",
    "SessionRecovery",
    "ResourceAwareExecutor",
    "ExecutionConfig",
    "ExecutionState",
    "ExecutionMode",
    "AutoPause",
    "ResourceOptimizer",
    "LongDurationManager",
    "DurabilityGuarantee",
    "FailureRecovery",
    "ProgressTracker",
    "DurabilityLevel",
    "ProgressSnapshot",
    "FailureRecord",
    "TaskState",
    "TaskStateManager",
    "StateTransition",
    "CheckpointManager",
    "CheckpointStorage",
    "TaskCheckpoint",
    "ResumeHandler",
    "ArtifactValidator",
    "ContextRestorer",
    "TaskMemorySystem",
    "TaskMemory",
    "TaskOutcome",
    "MemoryIndex",
    "MemoryCompressor",
    "MemoryStorage",
    "MemoryRetriever",
    "KnowledgeGraph",
    "RelationshipType",
    "RelationshipEdge",
    "TaskNode",
    "GraphQuery",
    "MemoryAwareMixin",
    "MemoryContextInjector",
    "MemoryUpdater",
    "CapabilityRegistry",
    "CapabilityMetric",
    "RefinementRecord",
    "LearningIntensity",
    "AgentLearner",
    "PatternExtractor",
    "PromptOptimizer",
    "FeedbackAnalyzer",
    "CodePattern",
    "PromptVariant",
    "LearningAwareMixin",
    "LearningConfidenceCalculator",
    "LearnedExperienceMetrics",
    "ConfidenceFactors",
    "BestPracticeConsultant",
    "BestPracticeAdvice",
    "CachedAdvice",
    "LearningDecisionEngine",
    "LearningDecision",
    "DecisionResult",
    "DecisionSource",
    "VisualFeedbackCollector",
    "VisualAnalyzer",
    "UIComparator",
    "VisualPatternLearner",
    "VisualFeedback",
    "VisualElement",
    "LayoutMetrics",
    "AccessibilityMetrics",
    "VisualRenderingMode",
    "VisualElementType",
    "BrowserController",
    "BrowserType",
    "RenderingMode",
    "ScreenshotOptions",
    "InteractionEvent",
    "run_docker_ps_json",
    "run_docker_ps_simple",
    "run_docker_ps_native",
    "get_container_status",
    "LearningDataExporter",
    "ExportMetadata",
    "AnonymizationPipeline",
    "AnonymizationReport",
    "ExportSchema",
    "ValidationResult",
    # Adaptive Learning Components
    "OutcomeTracker",
    "CodeOutcome",
    "AdaptiveScoringEngine",
    "LLMCommunicator",
    "LLMHint",
    "PredictiveQualityGates",
    "FirstPassPrediction",
    "PromptQualityAnalyzer",
    "PromptQualityScore",
    "IterationReducer",
    "IterationPattern",
]
