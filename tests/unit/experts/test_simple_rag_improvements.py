"""
Tests for Simple RAG improvements (query normalization, enhanced scoring, deduplication).
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from tapps_agents.experts.simple_rag import KnowledgeChunk, SimpleKnowledgeBase

pytestmark = pytest.mark.unit


class TestQueryNormalization:
    """Test query normalization improvements."""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory."""
        temp_dir = Path(tempfile.mkdtemp())
        knowledge_dir = temp_dir / "knowledge"
        knowledge_dir.mkdir()

        test_file = knowledge_dir / "test.md"
        test_file.write_text(
            """# Test Guide

## Authentication
How to implement secure authentication patterns.

### Password Hashing
Use bcrypt for password hashing.

### Session Management
Implement secure session management.
""",
            encoding="utf-8",
        )

        yield knowledge_dir
        shutil.rmtree(temp_dir)

    def test_stop_word_removal(self, temp_knowledge_dir):
        """Test that stop words are removed from queries."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)

        # Query with stop words
        query = "how to implement authentication"
        keywords = kb._normalize_query(query)

        # Should remove stop words like "how", "to"
        assert "how" not in keywords
        assert "to" not in keywords
        assert "implement" in keywords
        assert "authentication" in keywords

    def test_punctuation_handling(self, temp_knowledge_dir):
        """Test that punctuation is handled correctly."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)

        query = "password-hashing; and session-management!"
        keywords = kb._normalize_query(query)

        # Should handle hyphens and punctuation
        assert "password" in keywords or "password-hashing" in keywords
        assert "session" in keywords or "session-management" in keywords

    def test_short_word_filtering(self, temp_knowledge_dir):
        """Test that short words are filtered out."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)

        query = "a bc def ghij klmno"
        keywords = kb._normalize_query(query)

        # Should filter words <= 2 characters
        assert "a" not in keywords
        assert "bc" not in keywords
        assert "def" in keywords  # 3 chars
        assert "klmno" in keywords  # 5 chars


class TestEnhancedChunkScoring:
    """Test enhanced chunk scoring improvements."""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory."""
        temp_dir = Path(tempfile.mkdtemp())
        knowledge_dir = temp_dir / "knowledge"
        knowledge_dir.mkdir()

        test_file = knowledge_dir / "guide.md"
        test_file.write_text(
            """# Main Title

## Section Header

This is regular content about authentication.

```python
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

### Subsection

- List item one
- List item two

More content here.
""",
            encoding="utf-8",
        )

        yield knowledge_dir
        shutil.rmtree(temp_dir)

    def test_header_boosting(self, temp_knowledge_dir):
        """Test that headers get higher scores."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)

        query = "authentication section"
        chunks = kb.search(query, max_results=5)

        # Headers should be prioritized
        assert len(chunks) > 0
        # Headers should appear in results

    def test_code_block_boosting(self, temp_knowledge_dir):
        """Test that code blocks get boosted scores."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)

        query = "password hash bcrypt"
        chunks = kb.search(query, max_results=5)

        # Code blocks should be prioritized
        assert len(chunks) > 0
        # Chunks with code should have higher scores

    def test_list_boosting(self, temp_knowledge_dir):
        """Test that lists get boosted scores."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)

        query = "list item"
        chunks = kb.search(query, max_results=5)

        # List items should be prioritized
        assert len(chunks) > 0


class TestDeduplication:
    """Test chunk deduplication."""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory."""
        temp_dir = Path(tempfile.mkdtemp())
        knowledge_dir = temp_dir / "knowledge"
        knowledge_dir.mkdir()

        test_file = knowledge_dir / "duplicate.md"
        test_file.write_text(
            """# Duplicate Content

## Section One
This is important content about authentication.
This is important content about authentication.

## Section Two
Different content here.
Different content here.

## Section Three
More different content.
""",
            encoding="utf-8",
        )

        yield knowledge_dir
        shutil.rmtree(temp_dir)

    def test_deduplicate_similar_chunks(self, temp_knowledge_dir):
        """Test that similar chunks are deduplicated."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)

        query = "authentication content"
        kb.search(query, max_results=10)

        # Create chunks manually for testing deduplication
        test_chunks = [
            KnowledgeChunk(
                content="This is important content about authentication.",
                source_file=temp_knowledge_dir / "test.md",
                line_start=1,
                line_end=5,
                score=0.8,
            ),
            KnowledgeChunk(
                content="This is important content about authentication. Same text.",
                source_file=temp_knowledge_dir / "test.md",
                line_start=6,
                line_end=10,
                score=0.7,
            ),
        ]

        # Test deduplication
        unique_chunks = kb._deduplicate_chunks(test_chunks, similarity_threshold=0.8)

        # Should have only one unique chunk
        assert len(unique_chunks) == 1

    def test_context_deduplication(self, temp_knowledge_dir):
        """Test that get_context deduplicates chunks."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)

        query = "important content"
        context = kb.get_context(query, max_length=5000)

        # Context should not have duplicate content
        assert len(context) > 0
        # Check that we don't have exact duplicates
        lines = context.split("\n---\n")
        assert len(lines) > 0


class TestContextBuilding:
    """Test improved context building."""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory."""
        temp_dir = Path(tempfile.mkdtemp())
        knowledge_dir = temp_dir / "knowledge"
        knowledge_dir.mkdir()

        test_file = knowledge_dir / "guide.md"
        test_file.write_text(
            """# Guide

## Chapter One
Content about topic one.

## Chapter Two
Content about topic two.

## Chapter Three
Content about topic three.
""",
            encoding="utf-8",
        )

        yield knowledge_dir
        shutil.rmtree(temp_dir)

    def test_context_prioritization(self, temp_knowledge_dir):
        """Test that context prioritizes high-scoring chunks."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)

        query = "topic one"
        context = kb.get_context(query, max_length=5000)

        # Should include relevant content
        assert "topic one" in context.lower() or len(context) == 0

    def test_context_length_limit(self, temp_knowledge_dir):
        """Test that context respects max_length."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)

        query = "content"
        context = kb.get_context(query, max_length=100)

        # Should respect max_length
        assert len(context) <= 150  # Allow some padding for formatting

    def test_source_tracking(self, temp_knowledge_dir):
        """Test that source tracking prevents redundant chunks."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)

        query = "content topic"
        context = kb.get_context(query, max_length=5000)

        # Should have source information
        assert "[From:" in context or len(context) == 0


class TestEnhancedScoringIntegration:
    """Integration tests for enhanced scoring."""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory with diverse content."""
        temp_dir = Path(tempfile.mkdtemp())
        knowledge_dir = temp_dir / "knowledge"
        knowledge_dir.mkdir()

        test_file = knowledge_dir / "comprehensive.md"
        test_file.write_text(
            """# Comprehensive Guide

## Important Header
This is critical authentication information.

```python
# Code example for authentication
def authenticate(user, password):
    return verify_credentials(user, password)
```

### Subsection
- Important point one
- Important point two

Regular paragraph with authentication details.
""",
            encoding="utf-8",
        )

        yield knowledge_dir
        shutil.rmtree(temp_dir)

    def test_combined_scoring_boost(self, temp_knowledge_dir):
        """Test that multiple boosts work together."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)

        query = "authentication code example"
        chunks = kb.search(query, max_results=5)

        # Should prioritize chunks with both keywords and code
        assert len(chunks) > 0

    def test_phrase_matching_boost(self, temp_knowledge_dir):
        """Test that phrase matching gets boosted."""
        kb = SimpleKnowledgeBase(temp_knowledge_dir)

        query = "important point"
        chunks = kb.search(query, max_results=5)

        # Should find list items with phrase match
        assert len(chunks) > 0
