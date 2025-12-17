"""
Industry Experts Framework

Provides business domain knowledge through expert agents with:
- Weighted decision-making (51% primary authority)
- RAG integration for knowledge retrieval
- Fine-tuning support for domain specialization
- Consultation interface for workflow agents
"""

from .agent_integration import ExpertSupportMixin, create_agent_with_expert_support
from .base_expert import BaseExpert
from .builtin_registry import BuiltinExpertRegistry
from .domain_config import DomainConfig, DomainConfigParser
from .expert_config import ExpertConfigModel, ExpertsConfig, load_expert_configs
from .expert_registry import TECHNICAL_DOMAINS, ConsultationResult, ExpertRegistry
from .expert_engine import (
    ExpertEngine,
    ExpertEngineMetrics,
    ExpertRoutingPlan,
    KnowledgeNeed,
    KnowledgeRetrievalPlan,
    KnowledgeWriteRequest,
)
from .domain_detector import (
    DomainMapping,
    DomainStackDetector,
    RepoSignal,
    StackDetectionResult,
)
from .expert_synthesizer import ExpertSynthesizer, ExpertSynthesisResult
from .knowledge_ingestion import (
    IngestionResult,
    KnowledgeEntry,
    KnowledgeIngestionPipeline,
)
from .governance import (
    FilterResult,
    GovernanceLayer,
    GovernancePolicy,
)
from .observability import (
    ConsultationMetrics,
    Context7Metrics,
    KBImprovementProposal,
    ObservabilitySystem,
    RAGMetrics,
    WeakArea,
)
from .rag_chunker import Chunk, Chunker
from .rag_embedder import Embedder, SentenceTransformerEmbedder, create_embedder
from .rag_evaluation import (
    EvaluationMetrics,
    EvaluationQuestion,
    EvaluationResult,
    RAGEvaluator,
    create_default_evaluation_set,
)
from .rag_index import IndexMetadata, VectorIndex
from .rag_safety import RAGSafetyHandler, create_safety_handler
from .simple_rag import KnowledgeChunk, SimpleKnowledgeBase
from .vector_rag import VectorKnowledgeBase
from .weight_distributor import ExpertWeightMatrix, WeightDistributor

__all__ = [
    "BaseExpert",
    "WeightDistributor",
    "ExpertWeightMatrix",
    "DomainConfig",
    "DomainConfigParser",
    "ExpertRegistry",
    "ConsultationResult",
    "TECHNICAL_DOMAINS",
    "SimpleKnowledgeBase",
    "KnowledgeChunk",
    "VectorKnowledgeBase",
    "Chunk",
    "Chunker",
    "Embedder",
    "SentenceTransformerEmbedder",
    "create_embedder",
    "IndexMetadata",
    "VectorIndex",
    "RAGEvaluator",
    "EvaluationMetrics",
    "EvaluationQuestion",
    "EvaluationResult",
    "create_default_evaluation_set",
    "RAGSafetyHandler",
    "create_safety_handler",
    "ExpertConfigModel",
    "ExpertsConfig",
    "load_expert_configs",
    "BuiltinExpertRegistry",
    "ExpertSupportMixin",
    "create_agent_with_expert_support",
    "ExpertEngine",
    "ExpertEngineMetrics",
    "ExpertRoutingPlan",
    "KnowledgeNeed",
    "KnowledgeRetrievalPlan",
    "KnowledgeWriteRequest",
    "DomainStackDetector",
    "DomainMapping",
    "RepoSignal",
    "StackDetectionResult",
    "ExpertSynthesizer",
    "ExpertSynthesisResult",
    "KnowledgeIngestionPipeline",
    "KnowledgeEntry",
    "IngestionResult",
    "GovernanceLayer",
    "GovernancePolicy",
    "FilterResult",
    "ObservabilitySystem",
    "ConsultationMetrics",
    "Context7Metrics",
    "RAGMetrics",
    "WeakArea",
    "KBImprovementProposal",
]
