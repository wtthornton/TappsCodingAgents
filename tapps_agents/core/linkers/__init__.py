"""Knowledge-Expert Linking Module.

This module provides functionality for linking knowledge files to experts
and identifying orphan knowledge files.
"""

from .expert_knowledge_linker import (
    ExpertKnowledgeLinker,
    LinkingResult,
    OrphanFile,
)

__all__ = [
    "ExpertKnowledgeLinker",
    "LinkingResult",
    "OrphanFile",
]
