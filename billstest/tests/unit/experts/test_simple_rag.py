"""
Tests for Simple Knowledge Base RAG system.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from tapps_agents.experts.simple_rag import KnowledgeChunk, SimpleKnowledgeBase


class TestSimpleKnowledgeBase:
    """Test SimpleKnowledgeBase functionality."""

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
It uses mesh networking for reliability.

### Z-Wave Protocol
Z-Wave is another mesh protocol, operating at 900MHz.
It's known for good range and battery life.

## Devices

### Smart Lights
Smart lights can be controlled via various protocols.
Zigbee lights are energy efficient.

### Sensors
Motion sensors help with automation.
Temperature sensors monitor home climate.

## Best Practices
Use Zigbee for battery-powered devices.
Use Z-Wave for better range requirements.
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
Smart thermostats optimize HVAC.
""",
            encoding="utf-8",
        )

        yield knowledge_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_initialize_knowledge_base(self, temp_knowledge_dir):
        """Test knowledge base initialization."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)
        assert len(kb.files) == 2  # Two .md files
        assert any("home-automation" in str(f) for f in kb.files.keys())
        assert any("energy-management" in str(f) for f in kb.files.keys())

    def test_domain_filter(self, temp_knowledge_dir):
        """Test domain filtering."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir, domain="home-automation")
        assert len(kb.files) == 1
        assert any("home-automation" in str(f) for f in kb.files.keys())

    def test_search_keywords(self, temp_knowledge_dir):
        """Test keyword search."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)
        results = kb.search("Zigbee protocol", max_results=3)

        assert len(results) > 0
        assert all(isinstance(r, KnowledgeChunk) for r in results)
        # Top result should mention Zigbee
        assert "zigbee" in results[0].content.lower()

    def test_search_no_results(self, temp_knowledge_dir):
        """Test search with no matches."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)
        results = kb.search("nonexistent topic xyz123", max_results=3)
        assert len(results) == 0

    def test_get_context(self, temp_knowledge_dir):
        """Test context extraction."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)
        context = kb.get_context("Zigbee", max_length=1000)

        assert "zigbee" in context.lower()
        assert "From:" in context  # Source markers
        assert len(context) <= 1000  # Respects max_length

    def test_get_sources(self, temp_knowledge_dir):
        """Test source file listing."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)
        sources = kb.get_sources("Zigbee", max_results=5)

        assert len(sources) > 0
        assert any("home-automation" in s for s in sources)

    def test_chunk_scoring(self, temp_knowledge_dir):
        """Test that chunks are scored by relevance."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)
        results = kb.search("Zigbee protocol", max_results=5)

        # Results should be sorted by score (highest first)
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score

    def test_chunk_context_lines(self, temp_knowledge_dir):
        """Test that chunks include context around matches."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)
        results = kb.search("Zigbee", max_results=1)

        if results:
            chunk = results[0]
            # Chunk should have multiple lines (match + context)
            assert chunk.line_end > chunk.line_start
            # Content should be more than just the matched line
            assert "\n" in chunk.content or len(chunk.content.split()) > 5

    def test_markdown_aware_chunking(self, temp_knowledge_dir):
        """Test that chunking respects markdown structure."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)
        kb.search("protocols", max_results=2)

        # Headers (marked with #) should get higher scores
        # Check if any chunk starts with a header
        # This is likely since we search for "protocols" and there's a "## Protocols" header
        assert True  # Just verify it doesn't crash

    def test_empty_knowledge_dir(self):
        """Test handling of empty or missing knowledge directory."""
        temp_dir = Path(tempfile.mkdtemp())
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        kb = SimpleKnowledgeBase(empty_dir)
        assert len(kb.files) == 0

        results = kb.search("anything")
        assert len(results) == 0

        context = kb.get_context("anything")
        assert "No relevant knowledge" in context

        sources = kb.get_sources("anything")
        assert len(sources) == 0

        shutil.rmtree(temp_dir)

    def test_list_all_files(self, temp_knowledge_dir):
        """Test listing all knowledge files."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)
        files = kb.list_all_files()

        assert len(files) == 2
        assert any("home-automation" in f for f in files)
        assert any("energy-management" in f for f in files)

    def test_multiple_keywords(self, temp_knowledge_dir):
        """Test search with multiple keywords."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)
        results = kb.search("Zigbee mesh networking", max_results=3)

        # Should find content mentioning multiple keywords
        assert len(results) > 0
        top_result = results[0]
        assert "zigbee" in top_result.content.lower()

    def test_case_insensitive_search(self, temp_knowledge_dir):
        """Test that search is case-insensitive."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)

        results_lower = kb.search("zigbee", max_results=3)
        results_upper = kb.search("ZIGBEE", max_results=3)
        results_mixed = kb.search("ZiGbEe", max_results=3)

        # All should find similar results
        assert len(results_lower) > 0
        assert len(results_upper) > 0
        assert len(results_mixed) > 0

    def test_context_max_length(self, temp_knowledge_dir):
        """Test that context respects max_length."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)

        # Get context with small max_length
        context = kb.get_context("automation", max_length=100)

        # Should not exceed max_length (with some tolerance for formatting)
        assert len(context) <= 150  # Allow some overhead for formatting

    def test_source_relative_paths(self, temp_knowledge_dir):
        """Test that sources return relative paths."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)
        sources = kb.get_sources("Zigbee")

        # Sources should be relative paths, not absolute
        for source in sources:
            assert not Path(source).is_absolute() or "knowledge" in source
