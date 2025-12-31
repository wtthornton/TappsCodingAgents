"""
Tests for Vector Knowledge Base RAG system.

Tests FAISS-based semantic search with fallback to SimpleKnowledgeBase.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.experts.simple_rag import KnowledgeChunk, SimpleKnowledgeBase
from tapps_agents.experts.vector_rag import VectorKnowledgeBase

pytestmark = pytest.mark.unit

# Check if FAISS is available
try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


class TestVectorKnowledgeBase:
    """Test VectorKnowledgeBase functionality."""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory with test files."""
        temp_dir = Path(tempfile.mkdtemp())
        knowledge_dir = temp_dir / "knowledge"
        knowledge_dir.mkdir()

        # Create test knowledge file
        test_file = knowledge_dir / "home-automation.md"
        test_file.write_text(
            """# Home Automation Guide

## Protocols

### Zigbee Protocol
Zigbee is a low-power wireless protocol ideal for home automation.
It uses mesh networking for reliability and low power consumption.

### Z-Wave Protocol
Z-Wave is another mesh protocol, operating at 900MHz.
It's known for good range and battery life in home automation systems.

## Devices

### Smart Lights
Smart lights can be controlled via various protocols.
Zigbee lights are energy efficient and support dimming.

### Sensors
Motion sensors help with automation.
Temperature sensors monitor home climate.
""",
            encoding="utf-8",
        )

        # Create another domain file
        energy_file = knowledge_dir / "energy-management.md"
        energy_file.write_text(
            """# Energy Management

## Optimization
Monitor energy consumption regularly.
Use smart scheduling to reduce costs.

## Devices
Energy monitors track usage.
Smart thermostats optimize HVAC systems.
""",
            encoding="utf-8",
        )

        yield knowledge_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_initialize_with_fallback(self, temp_knowledge_dir):
        """Test initialization falls back to SimpleKnowledgeBase when FAISS unavailable."""
        # Mock FAISS as unavailable
        with patch("tapps_agents.experts.vector_rag.FAISS_AVAILABLE", False):
            kb = VectorKnowledgeBase(temp_knowledge_dir)
            kb._initialize()

            assert kb._backend_type == "simple"
            assert kb.fallback_kb is not None
            assert isinstance(kb.fallback_kb, SimpleKnowledgeBase)

    def test_get_backend_type_simple(self, temp_knowledge_dir):
        """Test get_backend_type returns 'simple' when using fallback."""
        with patch("tapps_agents.experts.vector_rag.FAISS_AVAILABLE", False):
            kb = VectorKnowledgeBase(temp_knowledge_dir)
            backend_type = kb.get_backend_type()

            assert backend_type == "simple"

    def test_search_with_fallback(self, temp_knowledge_dir):
        """Test search works with SimpleKnowledgeBase fallback."""
        with patch("tapps_agents.experts.vector_rag.FAISS_AVAILABLE", False):
            kb = VectorKnowledgeBase(temp_knowledge_dir)
            results = kb.search("Zigbee protocol", max_results=3)

            assert len(results) > 0
            assert all(isinstance(r, KnowledgeChunk) for r in results)
            # Top result should mention Zigbee
            assert "zigbee" in results[0].content.lower()

    def test_get_context_with_fallback(self, temp_knowledge_dir):
        """Test get_context works with fallback."""
        with patch("tapps_agents.experts.vector_rag.FAISS_AVAILABLE", False):
            kb = VectorKnowledgeBase(temp_knowledge_dir)
            context = kb.get_context("Zigbee", max_length=1000)

            assert "zigbee" in context.lower()
            # Allow some overhead for citation headers and formatting
            assert len(context) <= 1200

    def test_get_sources_with_fallback(self, temp_knowledge_dir):
        """Test get_sources works with fallback."""
        with patch("tapps_agents.experts.vector_rag.FAISS_AVAILABLE", False):
            kb = VectorKnowledgeBase(temp_knowledge_dir)
            sources = kb.get_sources("Zigbee", max_results=5)

            assert len(sources) > 0
            assert any("home-automation" in s for s in sources)

    def test_list_all_files_with_fallback(self, temp_knowledge_dir):
        """Test list_all_files works with fallback."""
        with patch("tapps_agents.experts.vector_rag.FAISS_AVAILABLE", False):
            kb = VectorKnowledgeBase(temp_knowledge_dir)
            files = kb.list_all_files()

            assert len(files) == 2
            assert any("home-automation" in f for f in files)
            assert any("energy-management" in f for f in files)

    def test_domain_filter_with_fallback(self, temp_knowledge_dir):
        """Test domain filtering works with fallback."""
        with patch("tapps_agents.experts.vector_rag.FAISS_AVAILABLE", False):
            kb = VectorKnowledgeBase(temp_knowledge_dir, domain="home-automation")
            files = kb.list_all_files()

            # Should filter to domain-specific files
            assert len(files) >= 1
            assert any("home-automation" in f for f in files)

    def test_empty_knowledge_dir_with_fallback(self):
        """Test handling of empty knowledge directory with fallback."""
        temp_dir = Path(tempfile.mkdtemp())
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        with patch("tapps_agents.experts.vector_rag.FAISS_AVAILABLE", False):
            kb = VectorKnowledgeBase(empty_dir)
            results = kb.search("anything")

            assert len(results) == 0

            context = kb.get_context("anything")
            assert "No relevant knowledge" in context

            sources = kb.get_sources("anything")
            assert len(sources) == 0

        shutil.rmtree(temp_dir)

    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_initialize_with_faiss_available(self, temp_knowledge_dir):
        """Test initialization with FAISS available (if installed)."""
        # This test only runs if FAISS is actually installed
        kb = VectorKnowledgeBase(temp_knowledge_dir)
        kb._initialize()

        # Should use vector backend if FAISS and sentence-transformers available
        backend_type = kb.get_backend_type()
        assert backend_type in ["vector", "simple"]  # May fallback if sentence-transformers unavailable

    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_search_with_faiss_available(self, temp_knowledge_dir):
        """Test semantic search with FAISS available (if installed)."""
        # This test only runs if FAISS is actually installed
        kb = VectorKnowledgeBase(temp_knowledge_dir)
        results = kb.search("Zigbee protocol", max_results=3)

        assert len(results) > 0
        assert all(isinstance(r, KnowledgeChunk) for r in results)
        # Results should have similarity scores
        assert all(0.0 <= r.score <= 1.0 for r in results)

    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_similarity_threshold_filtering(self, temp_knowledge_dir):
        """Test that similarity threshold filters results."""
        # This test only runs if FAISS is actually installed
        kb = VectorKnowledgeBase(temp_knowledge_dir, similarity_threshold=0.9)
        results = kb.search("Zigbee protocol", max_results=5)

        # All results should meet similarity threshold
        assert all(r.score >= 0.9 for r in results)

    def test_safety_handler_integration(self, temp_knowledge_dir):
        """Test that safety handler is initialized."""
        kb = VectorKnowledgeBase(temp_knowledge_dir)

        assert kb.safety_handler is not None
        assert hasattr(kb.safety_handler, "sanitize_retrieved_content")
        assert hasattr(kb.safety_handler, "format_retrieved_context")

    def test_index_dir_default(self, temp_knowledge_dir):
        """Test default index directory structure."""
        kb = VectorKnowledgeBase(temp_knowledge_dir, domain="test-domain")

        # Index dir should be in .tapps-agents/rag_index/<domain>
        expected_index_dir = temp_knowledge_dir.parent / ".tapps-agents" / "rag_index" / "test-domain"
        assert kb.index_dir == expected_index_dir

    def test_index_dir_custom(self, temp_knowledge_dir):
        """Test custom index directory."""
        custom_index_dir = temp_knowledge_dir / "custom_index"
        kb = VectorKnowledgeBase(temp_knowledge_dir, index_dir=custom_index_dir)

        assert kb.index_dir == custom_index_dir

    def test_chunk_size_and_overlap(self, temp_knowledge_dir):
        """Test chunk size and overlap parameters."""
        kb = VectorKnowledgeBase(
            temp_knowledge_dir,
            chunk_size=256,
            overlap=25,
        )

        assert kb.chunk_size == 256
        assert kb.overlap == 25
        assert kb.chunker.target_tokens == 256
        assert kb.chunker.overlap_tokens == 25

    def test_embedding_model_parameter(self, temp_knowledge_dir):
        """Test embedding model parameter."""
        kb = VectorKnowledgeBase(
            temp_knowledge_dir,
            embedding_model="test-model",
        )

        assert kb.embedding_model == "test-model"

    def test_similarity_threshold_parameter(self, temp_knowledge_dir):
        """Test similarity threshold parameter."""
        kb = VectorKnowledgeBase(
            temp_knowledge_dir,
            similarity_threshold=0.8,
        )

        assert kb.similarity_threshold == 0.8

    def test_get_context_max_length(self, temp_knowledge_dir):
        """Test that get_context respects max_length."""
        with patch("tapps_agents.experts.vector_rag.FAISS_AVAILABLE", False):
            kb = VectorKnowledgeBase(temp_knowledge_dir)
            context = kb.get_context("automation", max_length=100)

            # Should not exceed max_length (with some tolerance for formatting)
            assert len(context) <= 150  # Allow some overhead for formatting

    def test_get_sources_max_results(self, temp_knowledge_dir):
        """Test that get_sources respects max_results."""
        with patch("tapps_agents.experts.vector_rag.FAISS_AVAILABLE", False):
            kb = VectorKnowledgeBase(temp_knowledge_dir)
            sources = kb.get_sources("automation", max_results=1)

            assert len(sources) <= 1

    def test_error_handling_in_search(self, temp_knowledge_dir):
        """Test error handling in search method."""
        with patch("tapps_agents.experts.vector_rag.FAISS_AVAILABLE", True):
            kb = VectorKnowledgeBase(temp_knowledge_dir)

            # Mock index.search to raise an exception
            with patch.object(kb, "_initialize"), patch.object(
                kb, "index", new_callable=lambda: MagicMock()
            ) as mock_index:
                mock_index.search.side_effect = Exception("Search failed")
                kb.index = mock_index
                kb._backend_type = "vector"

                # Should fallback to SimpleKnowledgeBase on error
                results = kb.search("test query")

                # Should get results from fallback
                assert isinstance(results, list)

    def test_error_handling_in_initialization(self, temp_knowledge_dir):
        """Test error handling during initialization."""
        with patch("tapps_agents.experts.vector_rag.FAISS_AVAILABLE", True):
            # Mock create_embedder to raise an exception
            with patch(
                "tapps_agents.experts.vector_rag.create_embedder",
                side_effect=Exception("Embedder failed"),
            ):
                kb = VectorKnowledgeBase(temp_knowledge_dir)
                kb._initialize()

                # Should fallback to SimpleKnowledgeBase
                assert kb._backend_type == "simple"
                assert kb.fallback_kb is not None
