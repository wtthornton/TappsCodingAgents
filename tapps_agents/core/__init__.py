"""Core framework components"""

from .agent_base import BaseAgent
from .mal import MAL
from .config import ProjectConfig, load_config
from .context_manager import ContextManager
from .tiered_context import ContextTier, TieredContextBuilder
from .ast_parser import ASTParser
from .unified_cache import UnifiedCache, create_unified_cache, UnifiedCacheStats
from .cache_router import CacheType, CacheRequest, CacheResponse
from .hardware_profiler import HardwareProfile, HardwareProfiler, CacheOptimizationProfile
from .unified_cache_config import UnifiedCacheConfig, UnifiedCacheConfigManager
from .adaptive_cache_config import AdaptiveCacheConfig, AdaptiveCacheSettings, ConfigurationChange
from .session_manager import (
    SessionManager, AgentSession, SessionState, HealthStatus,
    SessionStorage, SessionMonitor, SessionRecovery
)
from .resource_aware_executor import (
    ResourceAwareExecutor, ExecutionConfig, ExecutionState, ExecutionMode,
    AutoPause, ResourceOptimizer
)
from .long_duration_support import (
    LongDurationManager, DurabilityGuarantee, FailureRecovery, ProgressTracker,
    DurabilityLevel, ProgressSnapshot, FailureRecord
)
from .task_state import TaskState, TaskStateManager, StateTransition
from .checkpoint_manager import CheckpointManager, CheckpointStorage, TaskCheckpoint
from .resume_handler import ResumeHandler, ArtifactValidator, ContextRestorer
from .task_memory import (
    TaskMemorySystem, TaskMemory, TaskOutcome, MemoryIndex,
    MemoryCompressor, MemoryStorage, MemoryRetriever
)
from .knowledge_graph import (
    KnowledgeGraph, RelationshipType, RelationshipEdge,
    TaskNode, GraphQuery
)
from .memory_integration import (
    MemoryAwareMixin, MemoryContextInjector, MemoryUpdater
)
from .capability_registry import (
    CapabilityRegistry, CapabilityMetric, RefinementRecord, LearningIntensity
)
from .agent_learning import (
    AgentLearner, PatternExtractor, PromptOptimizer, FeedbackAnalyzer,
    CodePattern, PromptVariant
)
from .learning_integration import LearningAwareMixin
from .learning_confidence import (
    LearningConfidenceCalculator, LearnedExperienceMetrics, ConfidenceFactors
)
from .best_practice_consultant import (
    BestPracticeConsultant, BestPracticeAdvice, CachedAdvice
)
from .learning_decision import (
    LearningDecisionEngine, LearningDecision, DecisionResult, DecisionSource
)
from .visual_feedback import (
    VisualFeedbackCollector, VisualAnalyzer, UIComparator, VisualPatternLearner,
    VisualFeedback, VisualElement, LayoutMetrics, AccessibilityMetrics,
    RenderingMode as VisualRenderingMode, VisualElementType
)
from .browser_controller import (
    BrowserController, BrowserType, RenderingMode, ScreenshotOptions, InteractionEvent
)

__all__ = [
    "BaseAgent", "MAL", "ContextManager", "ContextTier", "TieredContextBuilder", "ASTParser",
    "UnifiedCache", "create_unified_cache", "UnifiedCacheStats",
    "CacheType", "CacheRequest", "CacheResponse",
    "HardwareProfile", "HardwareProfiler", "CacheOptimizationProfile",
    "UnifiedCacheConfig", "UnifiedCacheConfigManager",
    "AdaptiveCacheConfig", "AdaptiveCacheSettings", "ConfigurationChange",
    "SessionManager", "AgentSession", "SessionState", "HealthStatus",
    "SessionStorage", "SessionMonitor", "SessionRecovery",
    "ResourceAwareExecutor", "ExecutionConfig", "ExecutionState", "ExecutionMode",
    "AutoPause", "ResourceOptimizer",
    "LongDurationManager", "DurabilityGuarantee", "FailureRecovery", "ProgressTracker",
    "DurabilityLevel", "ProgressSnapshot", "FailureRecord",
    "TaskState", "TaskStateManager", "StateTransition",
    "CheckpointManager", "CheckpointStorage", "TaskCheckpoint",
    "ResumeHandler", "ArtifactValidator", "ContextRestorer",
    "TaskMemorySystem", "TaskMemory", "TaskOutcome", "MemoryIndex",
    "MemoryCompressor", "MemoryStorage", "MemoryRetriever",
    "KnowledgeGraph", "RelationshipType", "RelationshipEdge",
    "TaskNode", "GraphQuery",
    "MemoryAwareMixin", "MemoryContextInjector", "MemoryUpdater",
    "CapabilityRegistry", "CapabilityMetric", "RefinementRecord", "LearningIntensity",
    "AgentLearner", "PatternExtractor", "PromptOptimizer", "FeedbackAnalyzer",
    "CodePattern", "PromptVariant",
    "LearningAwareMixin",
    "LearningConfidenceCalculator", "LearnedExperienceMetrics", "ConfidenceFactors",
    "BestPracticeConsultant", "BestPracticeAdvice", "CachedAdvice",
    "LearningDecisionEngine", "LearningDecision", "DecisionResult", "DecisionSource",
    "VisualFeedbackCollector", "VisualAnalyzer", "UIComparator", "VisualPatternLearner",
    "VisualFeedback", "VisualElement", "LayoutMetrics", "AccessibilityMetrics",
    "VisualRenderingMode", "VisualElementType",
    "BrowserController", "BrowserType", "RenderingMode", "ScreenshotOptions", "InteractionEvent"
]

