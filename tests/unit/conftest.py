"""
Pytest configuration and shared fixtures for unit tests.

This module provides fixtures that are shared across all unit tests,
particularly the unified_cache fixture needed by concurrency tests.
"""

from unittest.mock import Mock

import pytest

from tapps_agents.context7.kb_cache import KBCache
from tapps_agents.core.context_manager import ContextManager, ContextTier
from tapps_agents.core.hardware_profiler import HardwareProfile
from tapps_agents.core.unified_cache import UnifiedCache
from tapps_agents.experts.simple_rag import SimpleKnowledgeBase


@pytest.fixture
def tmp_cache_root(tmp_path):
    """Create temporary cache root directory."""
    cache_root = tmp_path / ".tapps-agents" / "kb"
    cache_root.mkdir(parents=True, exist_ok=True)
    return cache_root


@pytest.fixture
def mock_context_manager():
    """Create mock ContextManager for testing."""
    mock_cm = Mock(spec=ContextManager)
    mock_cm.get_context.return_value = {
        "content": "test context",
        "cached": True,
        "token_estimate": 100,
    }
    mock_cm.caches = {
        ContextTier.TIER1: Mock(max_size=100),
        ContextTier.TIER2: Mock(max_size=100),
        ContextTier.TIER3: Mock(max_size=100),
    }
    mock_cm.get_cache_stats.return_value = {"hits": 10, "misses": 5}
    mock_cm.clear_cache.return_value = None
    return mock_cm


@pytest.fixture
def mock_kb_cache():
    """Create mock KBCache for testing."""
    mock_kb = Mock(spec=KBCache)
    mock_kb.get.return_value = Mock(
        content="test KB content",
        context7_id="test-id",
        trust_score=0.9,
        token_count=200,
        cache_hits=5,
    )
    mock_kb.store.return_value = Mock(content="stored content", token_count=150)
    mock_kb.delete.return_value = True
    mock_kb.metadata_manager = Mock()
    mock_kb.metadata_manager.load_cache_index.return_value = Mock(
        libraries={"test-lib": {"topics": {"test-topic": {}}}}
    )
    return mock_kb


@pytest.fixture
def mock_knowledge_base():
    """Create mock SimpleKnowledgeBase for testing."""
    mock_kb = Mock(spec=SimpleKnowledgeBase)
    mock_kb.search.return_value = [{"chunk": "test chunk", "score": 0.8}]
    mock_kb.get_context.return_value = "test context from knowledge base"
    mock_kb.get_sources.return_value = ["source1.md", "source2.md"]
    mock_kb.list_all_files.return_value = ["file1.md", "file2.md"]
    mock_kb.domain = "test-domain"
    return mock_kb


@pytest.fixture
def unified_cache_mock(tmp_cache_root, mock_context_manager, mock_kb_cache, mock_knowledge_base):
    """Create UnifiedCache instance with mocks for testing."""
    return UnifiedCache(
        cache_root=tmp_cache_root,
        context_manager=mock_context_manager,
        kb_cache=mock_kb_cache,
        knowledge_base=mock_knowledge_base,
        hardware_profile=HardwareProfile.DEVELOPMENT,
    )


@pytest.fixture
def unified_cache(unified_cache_mock):
    """Alias for unified_cache_mock for backward compatibility."""
    return unified_cache_mock

