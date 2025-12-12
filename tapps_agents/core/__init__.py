"""Core framework components"""

from .adaptive_cache_config import (
    AdaptiveCacheConfig,
    AdaptiveCacheSettings,
    ConfigurationChange,
)
from .agent_base import BaseAgent
from .agent_learning import (
    AgentLearner,
    CodePattern,
    FeedbackAnalyzer,
    PatternExtractor,
    PromptOptimizer,
    PromptVariant,
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
from .hardware_profiler import (
    CacheOptimizationProfile,
    HardwareProfile,
    HardwareProfiler,
)
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
from .learning_integration import LearningAwareMixin
from .long_duration_support import (
    DurabilityGuarantee,
    DurabilityLevel,
    FailureRecord,
    FailureRecovery,
    LongDurationManager,
    ProgressSnapshot,
    ProgressTracker,
)
from .mal import MAL
from .memory_integration import MemoryAwareMixin, MemoryContextInjector, MemoryUpdater
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
    "MAL",
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
]
