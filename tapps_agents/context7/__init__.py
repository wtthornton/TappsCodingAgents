"""
Context7 Integration - Real-time library documentation with KB-first caching.

2025 Architecture Enhancements:
- AsyncCacheManager: Lock-free caching with in-memory LRU and background writes
- CircuitBreaker: Resilient parallel operations with fail-fast semantics
- ParallelExecutor: Bounded concurrency for batch operations
"""

from .agent_integration import Context7AgentHelper, get_context7_helper
from .bundle_loader import try_copy_context7_bundle
from .analytics import Analytics, CacheMetrics, LibraryMetrics
from .async_cache import (
    AsyncCacheEntry,
    AsyncCacheManager,
    get_async_cache,
    init_async_cache,
)
from .cache_locking import CacheLock, cache_lock, get_cache_lock_file
from .cache_structure import CacheStructure
from .cache_warming import (
    CacheWarmer,
    WarmingResult,
    WarmingStrategy,
    run_predictive_warming,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpen,
    CircuitState,
    ParallelExecutor,
    get_context7_circuit_breaker,
    get_parallel_executor,
)
from .cleanup import CleanupResult, KBCleanup
from .commands import Context7Commands
from .credential_validation import (
    CredentialValidationResult,
    CredentialValidator,
    test_context7_credentials,
    validate_context7_credentials,
)
from .cross_references import CrossReference, CrossReferenceManager, TopicIndex
from .fuzzy_matcher import FuzzyMatch, FuzzyMatcher
from .kb_cache import CacheEntry, KBCache
from .lookup import KBLookup, LookupResult
from .metadata import CacheIndex, LibraryMetadata, MetadataManager
from .refresh_queue import RefreshQueue, RefreshTask
from .staleness_policies import StalenessPolicy, StalenessPolicyManager

__all__ = [
    # Core Cache
    "KBCache",
    "CacheEntry",
    "CacheStructure",
    "MetadataManager",
    "LibraryMetadata",
    "CacheIndex",
    # 2025 Async Cache (Lock-Free)
    "AsyncCacheManager",
    "AsyncCacheEntry",
    "get_async_cache",
    "init_async_cache",
    # 2025 Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerOpen",
    "CircuitState",
    "ParallelExecutor",
    "get_context7_circuit_breaker",
    "get_parallel_executor",
    # Lookup
    "KBLookup",
    "LookupResult",
    "FuzzyMatcher",
    "FuzzyMatch",
    # Policies
    "StalenessPolicyManager",
    "StalenessPolicy",
    "RefreshQueue",
    "RefreshTask",
    # Analytics
    "Analytics",
    "CacheMetrics",
    "LibraryMetrics",
    # Cross-references
    "CrossReferenceManager",
    "CrossReference",
    "TopicIndex",
    # Cleanup
    "KBCleanup",
    "CleanupResult",
    # Commands
    "Context7Commands",
    # Agent Integration
    "Context7AgentHelper",
    "get_context7_helper",
    # Cache Warming
    "CacheWarmer",
    "WarmingStrategy",
    "WarmingResult",
    "run_predictive_warming",
    # Legacy Locking (still available for backward compatibility)
    "CacheLock",
    "cache_lock",
    "get_cache_lock_file",
    # Credentials
    "CredentialValidator",
    "CredentialValidationResult",
    "validate_context7_credentials",
    "test_context7_credentials",
]
