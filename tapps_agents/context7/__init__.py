"""
Context7 Integration - Real-time library documentation with KB-first caching.
"""

from .agent_integration import Context7AgentHelper, get_context7_helper
from .analytics import Analytics, CacheMetrics, LibraryMetrics
from .cache_structure import CacheStructure
from .cleanup import CleanupResult, KBCleanup
from .commands import Context7Commands
from .cross_references import CrossReference, CrossReferenceManager, TopicIndex
from .fuzzy_matcher import FuzzyMatch, FuzzyMatcher
from .kb_cache import CacheEntry, KBCache
from .lookup import KBLookup, LookupResult
from .metadata import CacheIndex, LibraryMetadata, MetadataManager
from .refresh_queue import RefreshQueue, RefreshTask
from .staleness_policies import StalenessPolicy, StalenessPolicyManager

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
