"""
Example usage of Unified Cache.

This demonstrates how to use the unified cache interface for all three cache types.
"""

from pathlib import Path

from tapps_agents.core import CacheType, ContextTier, create_unified_cache


def main():
    """Example unified cache usage."""

    # Create unified cache instance (auto-detects hardware)
    cache = create_unified_cache()

    print(f"Hardware Profile: {cache.get_hardware_profile().value}")
    print(f"Optimization Profile: {cache.get_optimization_profile()}")
    print()

    # Example 1: Get tiered context
    print("=== Example 1: Tiered Context Cache ===")
    file_path = Path("tapps_agents/core/unified_cache.py")
    response = cache.get(
        CacheType.TIERED_CONTEXT, key=str(file_path), tier=ContextTier.TIER1
    )

    if response:
        print(f"Found cached context: {response.cached}")
        print(f"Token estimate: {response.metadata.get('token_estimate', 0)}")
    else:
        print("No cached context found")
    print()

    # Example 2: Get Context7 KB entry
    print("=== Example 2: Context7 KB Cache ===")
    response = cache.get(
        CacheType.CONTEXT7_KB, key="fastapi", library="fastapi", topic="routing"
    )

    if response:
        print(f"Found cached docs: {response.cached}")
        print(f"Library: {response.metadata.get('library')}")
        print(f"Topic: {response.metadata.get('topic')}")
    else:
        print("No cached docs found")
    print()

    # Example 3: Get RAG knowledge
    print("=== Example 3: RAG Knowledge Base ===")
    response = cache.get(
        CacheType.RAG_KNOWLEDGE,
        key="agent-orchestration",
        query="agent orchestration patterns",
        max_results=3,
    )

    if response:
        print(f"Found knowledge: {response.cached}")
        print(f"Chunks found: {response.metadata.get('chunks_found', 0)}")
        print(f"Sources: {response.metadata.get('sources', [])}")
    else:
        print("No knowledge found")
    print()

    # Example 4: Get unified statistics
    print("=== Example 4: Unified Statistics ===")
    stats = cache.get_stats()
    print(f"Hardware Profile: {stats.hardware_profile}")
    print(f"Total Hits: {stats.total_hits}")
    print(f"Total Misses: {stats.total_misses}")
    print(f"Cache Stats: {stats.cache_stats}")
    print(f"Resource Usage: {stats.resource_usage}")


if __name__ == "__main__":
    main()
