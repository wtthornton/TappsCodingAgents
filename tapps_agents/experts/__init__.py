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
from .simple_rag import KnowledgeChunk, SimpleKnowledgeBase
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
    "ExpertConfigModel",
    "ExpertsConfig",
    "load_expert_configs",
    "BuiltinExpertRegistry",
    "ExpertSupportMixin",
    "create_agent_with_expert_support",
]
