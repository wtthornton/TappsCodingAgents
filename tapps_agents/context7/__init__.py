"""
Context7 Integration - Real-time library documentation with KB-first caching.
"""

from .kb_cache import KBCache, CacheEntry
from .cache_structure import CacheStructure
from .metadata import MetadataManager, LibraryMetadata, CacheIndex
from .lookup import KBLookup, LookupResult
from .fuzzy_matcher import FuzzyMatcher, FuzzyMatch
from .staleness_policies import StalenessPolicyManager, StalenessPolicy
from .refresh_queue import RefreshQueue, RefreshTask
from .analytics import Analytics, CacheMetrics, LibraryMetrics
from .cross_references import CrossReferenceManager, CrossReference, TopicIndex
from .cleanup import KBCleanup, CleanupResult
from .commands import Context7Commands
from .agent_integration import Context7AgentHelper, get_context7_helper

__all__ = [
    "KBCache",
    "CacheEntry",
    "CacheStructure",
    "MetadataManager",
    "LibraryMetadata",
    "CacheIndex",
    "KBLookup",
    "LookupResult",
    "FuzzyMatcher",
    "FuzzyMatch",
    "StalenessPolicyManager",
    "StalenessPolicy",
    "RefreshQueue",
    "RefreshTask",
    "Analytics",
    "CacheMetrics",
    "LibraryMetrics",
    "CrossReferenceManager",
    "CrossReference",
    "TopicIndex",
    "KBCleanup",
    "CleanupResult",
    "Context7Commands",
    "Context7AgentHelper",
    "get_context7_helper",
]

