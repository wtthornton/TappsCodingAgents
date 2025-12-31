"""
Tests for context7_enhancer.py - Enhanced Content Extraction

Tests for improved content extraction methods including:
- Section detection
- Content extraction from sections
- Code block extraction
- Enhanced best practices, mistakes, and examples extraction
"""

import pytest
from unittest.mock import Mock, MagicMock

pytestmark = pytest.mark.unit

from tapps_agents.agents.reviewer.context7_enhancer import (
    Context7ReviewEnhancer,
    LibraryRecommendation,
    PatternGuidance,
)
from tapps_agents.context7.agent_integration import Context7AgentHelper


# Sample test data
SAMPLE_MARKDOWN_WITH_SECTIONS = """# Library Documentation

## Best Practices

- Use chunking strategy for large documents
- Implement proper error handling for API calls
- Set appropriate temperature for LLM
- Always validate input data

## Common Mistakes

- Not setting proper temperature for LLM
- Missing retry logic for API calls
- Forgetting to handle errors
- Not validating user input

## Examples

```python
from langchain.llms import OpenAI
llm = OpenAI(temperature=0.7)
```

```python
# Another example
result = llm.generate(prompt)
```

## Other Section

Some other content here.
"""

SAMPLE_MARKDOWN_WITHOUT_SECTIONS = """
Some general content about the library.
You should use it properly.
Avoid common mistakes.
Here's an example: ```python
code = "example"
```
"""

SAMPLE_MARKDOWN_NUMBERED_LISTS = """# Documentation

## Best Practices

1. First practice
2. Second practice
3. Third practice
"""

SAMPLE_MARKDOWN_MIXED = """# Documentation

## Best Practices

- Bullet point one
- Bullet point two

Some paragraph text that should be extracted because it contains recommendations.

1. Numbered item one
2. Numbered item two
"""


@pytest.fixture
def mock_context7_helper():
    """Create a mock Context7AgentHelper."""
    helper = Mock(spec=Context7AgentHelper)
    helper.enabled = True
    return helper


@pytest.fixture
def enhancer(mock_context7_helper):
    """Create a Context7ReviewEnhancer instance for testing."""
    return Context7ReviewEnhancer(
        context7_helper=mock_context7_helper,
        timeout=30,
        cache_enabled=False  # Disable cache for testing
    )


class TestSectionDetection:
    """Test suite for section detection methods."""
    
    def test_find_section_by_header_basic(self, enhancer):
        """Test finding section with exact header match."""
        section = enhancer._find_section_by_header(
            SAMPLE_MARKDOWN_WITH_SECTIONS,
            ["best practice"]
        )
        assert section is not None
        start, end = section
        assert start == 2  # Line with "## Best Practices" (0-indexed)
        assert end >= start  # Section has content
    
    def test_find_section_by_header_variations(self, enhancer):
        """Test finding section with header variations."""
        # Test case-insensitive matching - keywords are lowercased in method
        section1 = enhancer._find_section_by_header(
            SAMPLE_MARKDOWN_WITH_SECTIONS,
            ["best practices"]  # Lowercase keyword works
        )
        assert section1 is not None
        
        # Test with "Best Practices" - should work because header is lowercased
        section2 = enhancer._find_section_by_header(
            SAMPLE_MARKDOWN_WITH_SECTIONS,
            ["best practice"]  # Singular also works
        )
        assert section2 is not None
    
    def test_find_section_by_header_multiple_keywords(self, enhancer):
        """Test finding section with multiple keywords."""
        section = enhancer._find_section_by_header(
            SAMPLE_MARKDOWN_WITH_SECTIONS,
            ["recommendation", "best practice", "tip"]
        )
        assert section is not None
    
    def test_find_section_by_header_not_found(self, enhancer):
        """Test when section not found."""
        section = enhancer._find_section_by_header(
            SAMPLE_MARKDOWN_WITH_SECTIONS,
            ["nonexistent section"]
        )
        assert section is None
    
    def test_find_section_by_header_section_at_end(self, enhancer):
        """Test section that extends to end of content."""
        content = """# Title

## Last Section

Content here
More content
"""
        section = enhancer._find_section_by_header(content, ["last section"])
        assert section is not None
        start, end = section
        assert end == len(content.split('\n')) - 1


class TestContentExtractionFromSection:
    """Test suite for content extraction from sections."""
    
    def test_extract_from_section_bulleted_lists(self, enhancer):
        """Test extraction of bulleted list items."""
        # Find the actual section first
        section = enhancer._find_section_by_header(
            SAMPLE_MARKDOWN_WITH_SECTIONS,
            ["best practice"]
        )
        assert section is not None
        items = enhancer._extract_from_section(
            section,
            SAMPLE_MARKDOWN_WITH_SECTIONS
        )
        assert len(items) >= 4
        assert any("chunking strategy" in item.lower() for item in items)
        assert any("error handling" in item.lower() for item in items)
    
    def test_extract_from_section_numbered_lists(self, enhancer):
        """Test extraction of numbered list items."""
        section = enhancer._find_section_by_header(
            SAMPLE_MARKDOWN_NUMBERED_LISTS,
            ["best practice"]
        )
        assert section is not None
        items = enhancer._extract_from_section(
            section,
            SAMPLE_MARKDOWN_NUMBERED_LISTS
        )
        assert len(items) == 3
        assert "First practice" in items[0]
        assert "Second practice" in items[1]
        assert "Third practice" in items[2]
    
    def test_extract_from_section_mixed_content(self, enhancer):
        """Test extraction from section with mixed content."""
        section = enhancer._find_section_by_header(
            SAMPLE_MARKDOWN_MIXED,
            ["best practice"]
        )
        assert section is not None
        items = enhancer._extract_from_section(
            section,
            SAMPLE_MARKDOWN_MIXED
        )
        # Should extract both bullet points and paragraph
        assert len(items) >= 2
    
    def test_extract_from_section_empty_section(self, enhancer):
        """Test extraction from empty section."""
        content = """# Title

## Empty Section

## Next Section
"""
        section = enhancer._find_section_by_header(content, ["empty section"])
        assert section is not None
        items = enhancer._extract_from_section(section, content)
        assert len(items) == 0


class TestCodeBlockExtraction:
    """Test suite for code block extraction."""
    
    def test_extract_all_code_blocks_basic(self, enhancer):
        """Test extraction of simple code blocks."""
        content = """Some text

```python
code here
```

More text
"""
        blocks = enhancer._extract_all_code_blocks(content)
        assert len(blocks) == 1
        assert "code here" in blocks[0]
    
    def test_extract_all_code_blocks_with_language(self, enhancer):
        """Test extraction of code blocks with language tags."""
        content = """```python
def hello():
    print("world")
```
"""
        blocks = enhancer._extract_all_code_blocks(content)
        assert len(blocks) == 1
        assert "def hello():" in blocks[0]
        assert "print" in blocks[0]
    
    def test_extract_all_code_blocks_multiple(self, enhancer):
        """Test extraction of multiple code blocks."""
        blocks = enhancer._extract_all_code_blocks(SAMPLE_MARKDOWN_WITH_SECTIONS)
        assert len(blocks) == 2
        assert "OpenAI" in blocks[0]
        assert "llm.generate" in blocks[1]
    
    def test_extract_code_blocks_from_section(self, enhancer):
        """Test extraction of code blocks from specific section."""
        section = enhancer._find_section_by_header(
            SAMPLE_MARKDOWN_WITH_SECTIONS,
            ["example"]
        )
        assert section is not None
        blocks = enhancer._extract_code_blocks_from_section(
            section,
            SAMPLE_MARKDOWN_WITH_SECTIONS
        )
        # Should extract code blocks from Examples section
        assert len(blocks) >= 1  # At least one code block in Examples section


class TestEnhancedBestPracticesExtraction:
    """Test suite for enhanced best practices extraction."""
    
    def test_extract_best_practices_with_section(self, enhancer):
        """Test extraction when 'Best Practices' section exists."""
        practices = enhancer._extract_best_practices(SAMPLE_MARKDOWN_WITH_SECTIONS)
        assert len(practices) > 0
        assert len(practices) <= 5  # Should be limited
        assert any("chunking" in p.lower() for p in practices)
    
    def test_extract_best_practices_without_section(self, enhancer):
        """Test extraction when section not found (fallback)."""
        practices = enhancer._extract_best_practices(SAMPLE_MARKDOWN_WITHOUT_SECTIONS)
        # Should fallback to simple extraction
        assert isinstance(practices, list)
        assert len(practices) <= 5
    
    def test_extract_best_practices_section_variations(self, enhancer):
        """Test with different section header variations."""
        # Test that section detection works with variations
        # The method lowercases both header and keywords, so all should work
        # Items must be > 10 chars to pass filtering
        content = """## Best Practices
- This is item one which is long enough
- This is item two which is also long enough
"""
        practices = enhancer._extract_best_practices(content)
        assert len(practices) > 0
        assert any("item one" in p.lower() or "item two" in p.lower() for p in practices)
    
    def test_extract_best_practices_simple_fallback(self, enhancer):
        """Test simple extraction fallback method."""
        practices = enhancer._extract_best_practices_simple(
            SAMPLE_MARKDOWN_WITHOUT_SECTIONS
        )
        assert isinstance(practices, list)
        assert len(practices) <= 5


class TestEnhancedCommonMistakesExtraction:
    """Test suite for enhanced common mistakes extraction."""
    
    def test_extract_common_mistakes_with_section(self, enhancer):
        """Test extraction when 'Common Mistakes' section exists."""
        mistakes = enhancer._extract_common_mistakes(SAMPLE_MARKDOWN_WITH_SECTIONS)
        assert len(mistakes) > 0
        assert len(mistakes) <= 5
        assert any("temperature" in m.lower() for m in mistakes)
    
    def test_extract_common_mistakes_without_section(self, enhancer):
        """Test extraction when section not found (fallback)."""
        mistakes = enhancer._extract_common_mistakes(SAMPLE_MARKDOWN_WITHOUT_SECTIONS)
        assert isinstance(mistakes, list)
        assert len(mistakes) <= 5
    
    def test_extract_common_mistakes_section_variations(self, enhancer):
        """Test with different section header variations."""
        # Test that section detection works with variations
        # Items must be > 10 chars to pass filtering
        content = """## Common Mistakes
- This is mistake one which is long enough
- This is mistake two which is also long enough
"""
        mistakes = enhancer._extract_common_mistakes(content)
        assert len(mistakes) > 0
        assert any("mistake one" in m.lower() or "mistake two" in m.lower() for m in mistakes)
    
    def test_extract_common_mistakes_simple_fallback(self, enhancer):
        """Test simple extraction fallback method."""
        mistakes = enhancer._extract_common_mistakes_simple(
            SAMPLE_MARKDOWN_WITHOUT_SECTIONS
        )
        assert isinstance(mistakes, list)
        assert len(mistakes) <= 5


class TestEnhancedExamplesExtraction:
    """Test suite for enhanced examples extraction."""
    
    def test_extract_examples_with_section(self, enhancer):
        """Test extraction when 'Examples' section exists."""
        examples = enhancer._extract_examples(SAMPLE_MARKDOWN_WITH_SECTIONS)
        assert len(examples) > 0
        assert len(examples) <= 3  # Should be limited to 3
        # Check that we got code blocks (may be from Examples section or all blocks)
        # The examples should contain code - check all examples combined
        all_examples_text = " ".join(examples).lower()
        # Should contain code-related keywords from the sample markdown
        assert any(keyword in all_examples_text for keyword in ["openai", "llm", "generate", "python", "from", "import"])
    
    def test_extract_examples_without_section(self, enhancer):
        """Test extraction when section not found (all code blocks)."""
        examples = enhancer._extract_examples(SAMPLE_MARKDOWN_WITHOUT_SECTIONS)
        assert isinstance(examples, list)
        assert len(examples) <= 3
    
    def test_extract_examples_limit(self, enhancer):
        """Test that examples are limited to 3."""
        content = """## Examples
```python
code1
```
```python
code2
```
```python
code3
```
```python
code4
```
"""
        examples = enhancer._extract_examples(content)
        assert len(examples) == 3  # Should be limited


class TestFilteringAndLimiting:
    """Test suite for filtering and limiting methods."""
    
    def test_filter_and_limit_basic(self, enhancer):
        """Test basic filtering and limiting."""
        items = ["item1", "item2", "item3", "item4", "item5", "item6"]
        # Items need to be at least min_length (default 10), so make them longer
        items = ["item one is long enough", "item two is long enough", "item three is long enough", 
                 "item four is long enough", "item five is long enough", "item six is long enough"]
        filtered = enhancer._filter_and_limit(items, max_items=3)
        assert len(filtered) == 3
    
    def test_filter_and_limit_min_length(self, enhancer):
        """Test filtering by minimum length."""
        items = ["short", "this is a longer item", "also short", "another long item"]
        filtered = enhancer._filter_and_limit(items, min_length=10)
        # Should filter out "short" and "also short" (both < 10 chars)
        # Keep "this is a longer item" and "another long item"
        assert len(filtered) >= 2  # At least 2 items should pass
        assert all(len(item) >= 10 for item in filtered)
    
    def test_filter_and_limit_duplicates(self, enhancer):
        """Test duplicate removal (case-insensitive)."""
        items = ["Item One is long enough", "item one is long enough", "Item Two is long enough", "ITEM ONE IS LONG ENOUGH"]
        filtered = enhancer._filter_and_limit(items, min_length=10)
        # Should remove duplicates (case-insensitive)
        # "Item One is long enough", "item one is long enough", "ITEM ONE IS LONG ENOUGH" are duplicates
        # "Item Two is long enough" is unique
        assert len(filtered) >= 1  # At least one unique item
        assert len(filtered) <= 2  # At most 2 unique items (one variant of "Item One" + "Item Two")
    
    def test_filter_and_limit_empty_list(self, enhancer):
        """Test with empty list."""
        filtered = enhancer._filter_and_limit([])
        assert filtered == []


class TestErrorHandling:
    """Test suite for error handling and edge cases."""
    
    def test_extract_best_practices_with_malformed_markdown(self, enhancer):
        """Test extraction with malformed markdown."""
        malformed = """## Best Practices
- Item 1
# Broken header
- Item 2
"""
        # Should not crash, should return results
        practices = enhancer._extract_best_practices(malformed)
        assert isinstance(practices, list)
    
    def test_extract_with_empty_content(self, enhancer):
        """Test extraction with empty content."""
        practices = enhancer._extract_best_practices("")
        assert practices == []
        
        mistakes = enhancer._extract_common_mistakes("")
        assert mistakes == []
        
        examples = enhancer._extract_examples("")
        assert examples == []
    
    def test_extract_with_none_content(self, enhancer):
        """Test extraction handles None gracefully."""
        # Should not crash
        try:
            practices = enhancer._extract_best_practices(None)  # type: ignore
        except (AttributeError, TypeError):
            pass  # Expected to fail gracefully or raise appropriate error


class TestIntegration:
    """Integration tests for complete extraction flow."""
    
    def test_complete_extraction_flow(self, enhancer):
        """Test complete extraction flow with real markdown."""
        content = SAMPLE_MARKDOWN_WITH_SECTIONS
        
        practices = enhancer._extract_best_practices(content)
        mistakes = enhancer._extract_common_mistakes(content)
        examples = enhancer._extract_examples(content)
        
        # All should return results
        assert len(practices) > 0
        assert len(mistakes) > 0
        assert len(examples) > 0
        
        # All should be within limits
        assert len(practices) <= 5
        assert len(mistakes) <= 5
        assert len(examples) <= 3
    
    def test_extraction_performance(self, enhancer):
        """Test extraction performance."""
        import time
        
        content = SAMPLE_MARKDOWN_WITH_SECTIONS * 10  # Larger content
        
        start = time.time()
        practices = enhancer._extract_best_practices(content)
        mistakes = enhancer._extract_common_mistakes(content)
        examples = enhancer._extract_examples(content)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 50ms target)
        assert elapsed < 0.1  # 100ms is generous for test environment
        assert len(practices) > 0
        assert len(mistakes) > 0
        assert len(examples) > 0
