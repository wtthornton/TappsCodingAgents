"""
Industry Experts Framework

Provides business domain knowledge through expert agents with:
- Weighted decision-making (51% primary authority)
- RAG integration for knowledge retrieval
- Fine-tuning support for domain specialization
- Consultation interface for workflow agents
"""

from .base_expert import BaseExpert
from .weight_distributor import WeightDistributor, ExpertWeightMatrix
from .domain_config import DomainConfig, DomainConfigParser
from .expert_registry import ExpertRegistry
from .simple_rag import SimpleKnowledgeBase, KnowledgeChunk
from .expert_config import ExpertConfigModel, ExpertsConfig, load_expert_configs

__all__ = [
    "BaseExpert",
    "WeightDistributor",
    "ExpertWeightMatrix",
    "DomainConfig",
    "DomainConfigParser",
    "ExpertRegistry",
    "SimpleKnowledgeBase",
    "KnowledgeChunk",
    "ExpertConfigModel",
    "ExpertsConfig",
    "load_expert_configs",
]

