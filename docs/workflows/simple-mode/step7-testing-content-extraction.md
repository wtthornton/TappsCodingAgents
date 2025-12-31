# Step 7: Testing - Improved Content Extraction

**Workflow:** Simple Mode *build  
**Feature:** Priority 2 - Improved Content Extraction from Context7  
**Date:** January 2025

---

## Test Plan Summary

### Test Coverage Goals

- **Unit Tests:** ≥ 90% coverage (critical for parsing logic)
- **Integration Tests:** End-to-end extraction tests
- **Edge Cases:** Malformed markdown, empty content, various formats

---

## Unit Tests

### Test File: `tests/agents/reviewer/test_context7_enhancer_extraction.py`

#### Test Suite 1: Section Detection

**Test Cases:**
1. `test_find_section_by_header_basic`
   - Test finding section with exact header match
   - Verify section boundaries returned correctly

2. `test_find_section_by_header_variations`
   - Test finding section with header variations (Best Practices, best practices, BEST PRACTICES)
   - Verify case-insensitive matching

3. `test_find_section_by_header_multiple_keywords`
   - Test finding section with multiple keywords
   - Verify first match is returned

4. `test_find_section_by_header_nested_sections`
   - Test finding section with nested subsections
   - Verify correct section boundaries

5. `test_find_section_by_header_not_found`
   - Test when section not found
   - Should return None

6. `test_find_section_by_header_section_at_end`
   - Test section that extends to end of content
   - Verify end boundary is correct

#### Test Suite 2: Content Extraction from Section

**Test Cases:**
1. `test_extract_from_section_bulleted_lists`
   - Test extraction of bulleted list items
   - Verify all items extracted

2. `test_extract_from_section_numbered_lists`
   - Test extraction of numbered list items (1., 2., 3.)
   - Verify numbers stripped correctly

3. `test_extract_from_section_nested_lists`
   - Test extraction from nested lists
   - Verify nesting preserved or flattened appropriately

4. `test_extract_from_section_paragraphs`
   - Test extraction of paragraph text
   - Verify context-aware filtering

5. `test_extract_from_section_mixed_content`
   - Test extraction from section with mixed content (lists + paragraphs)
   - Verify all content types extracted

6. `test_extract_from_section_empty_section`
   - Test extraction from empty section
   - Should return empty list

#### Test Suite 3: Code Block Extraction

**Test Cases:**
1. `test_extract_all_code_blocks_basic`
   - Test extraction of simple code blocks
   - Verify code content preserved

2. `test_extract_all_code_blocks_with_language`
   - Test extraction of code blocks with language tags (```python)
   - Verify language tags handled correctly

3. `test_extract_all_code_blocks_multiple`
   - Test extraction of multiple code blocks
   - Verify all blocks extracted

4. `test_extract_all_code_blocks_unclosed`
   - Test extraction of unclosed code block
   - Should handle gracefully

5. `test_extract_code_blocks_from_section`
   - Test extraction of code blocks from specific section
   - Verify only blocks from section extracted

#### Test Suite 4: Enhanced Best Practices Extraction

**Test Cases:**
1. `test_extract_best_practices_with_section`
   - Test extraction when "Best Practices" section exists
   - Verify enhanced extraction used

2. `test_extract_best_practices_without_section`
   - Test extraction when section not found
   - Verify fallback to simple extraction

3. `test_extract_best_practices_section_variations`
   - Test with different section header variations
   - Verify all variations detected

4. `test_extract_best_practices_fallback_on_error`
   - Test fallback when enhanced extraction fails
   - Verify simple extraction used

#### Test Suite 5: Enhanced Common Mistakes Extraction

**Test Cases:**
1. `test_extract_common_mistakes_with_section`
   - Test extraction when "Common Mistakes" section exists
   - Verify enhanced extraction used

2. `test_extract_common_mistakes_without_section`
   - Test extraction when section not found
   - Verify fallback to simple extraction

3. `test_extract_common_mistakes_section_variations`
   - Test with different section header variations
   - Verify all variations detected

#### Test Suite 6: Enhanced Examples Extraction

**Test Cases:**
1. `test_extract_examples_with_section`
   - Test extraction when "Examples" section exists
   - Verify code blocks from section extracted

2. `test_extract_examples_without_section`
   - Test extraction when section not found
   - Verify all code blocks extracted

3. `test_extract_examples_limit`
   - Test that examples are limited to 3
   - Verify limit applied correctly

#### Test Suite 7: Filtering and Limiting

**Test Cases:**
1. `test_filter_and_limit_basic`
   - Test basic filtering and limiting
   - Verify max_items limit applied

2. `test_filter_and_limit_min_length`
   - Test filtering by minimum length
   - Verify short items filtered out

3. `test_filter_and_limit_duplicates`
   - Test duplicate removal (case-insensitive)
   - Verify duplicates removed

4. `test_filter_and_limit_empty_list`
   - Test with empty list
   - Should return empty list

---

## Integration Tests

### Test File: `tests/agents/reviewer/test_context7_enhancer_integration.py`

#### Test Suite 1: End-to-End Extraction

**Test Cases:**
1. `test_complete_extraction_flow`
   - Test complete extraction flow with real markdown
   - Verify all methods work together

2. `test_extraction_with_real_context7_response`
   - Test with mock Context7 response
   - Verify extraction quality

3. `test_extraction_performance`
   - Test extraction performance
   - Verify < 50ms target met

---

## Test Data

### Sample Markdown Content

```markdown
# Library Documentation

## Best Practices

- Use chunking strategy for large documents
- Implement proper error handling for API calls
- Set appropriate temperature for LLM

## Common Mistakes

- Not setting proper temperature for LLM
- Missing retry logic for API calls
- Forgetting to handle errors

## Examples

```python
from langchain.llms import OpenAI
llm = OpenAI(temperature=0.7)
```

```python
# Another example
result = llm.generate(prompt)
```
```

### Sample Section Detection Test Data

```python
SAMPLE_MARKDOWN = """
# Title

## Best Practices

- Practice 1
- Practice 2

## Other Section

Some content
"""
```

---

## Test Execution Plan

### Phase 1: Unit Tests
1. Create test file `tests/agents/reviewer/test_context7_enhancer_extraction.py`
2. Implement all unit test cases
3. Run tests: `pytest tests/agents/reviewer/test_context7_enhancer_extraction.py -v`
4. Target: 100% pass rate, ≥ 90% coverage

### Phase 2: Integration Tests
1. Create test file `tests/agents/reviewer/test_context7_enhancer_integration.py`
2. Implement integration test cases
3. Run tests: `pytest tests/agents/reviewer/test_context7_enhancer_integration.py -v`
4. Target: 100% pass rate

### Phase 3: Coverage Analysis
1. Run coverage: `pytest --cov=tapps_agents/agents/reviewer/context7_enhancer tests/agents/reviewer/test_context7_enhancer_extraction.py tests/agents/reviewer/test_context7_enhancer_integration.py`
2. Target: ≥ 90% coverage
3. Identify uncovered lines
4. Add tests for uncovered lines if critical

### Phase 4: Performance Testing
1. Test with various content sizes
2. Measure extraction time
3. Verify < 50ms target
4. Profile hot paths if needed

---

## Test Validation Criteria

### Unit Tests
- ✅ All test cases pass
- ✅ Edge cases handled
- ✅ Error cases handled
- ✅ No false positives

### Integration Tests
- ✅ End-to-end flow works
- ✅ All methods work together
- ✅ Real-world scenarios covered

### Coverage
- ✅ ≥ 90% code coverage
- ✅ All critical paths covered
- ✅ Edge cases covered

### Performance
- ✅ < 50ms per extraction
- ✅ No performance regression
- ✅ Handles large documents efficiently

---

## Test Implementation Notes

### Test Structure

```python
import pytest
from tapps_agents.agents.reviewer.context7_enhancer import (
    Context7ReviewEnhancer,
    Context7AgentHelper
)

class TestSectionDetection:
    def test_basic(self):
        enhancer = Context7ReviewEnhancer(mock_helper)
        section = enhancer._find_section_by_header(
            SAMPLE_MARKDOWN,
            ["best practice"]
        )
        assert section is not None
        assert section[0] == 3  # Start line
        assert section[1] == 6  # End line

# More test classes...
```

### Test Fixtures

```python
@pytest.fixture
def sample_markdown():
    return SAMPLE_MARKDOWN

@pytest.fixture
def enhancer():
    mock_helper = Mock(spec=Context7AgentHelper)
    return Context7ReviewEnhancer(mock_helper)
```

---

## Next Steps

1. **Implement Unit Tests:** Create test file and implement all test cases
2. **Implement Integration Tests:** Create integration test file
3. **Run Tests:** Execute test suite
4. **Fix Issues:** Address any failing tests
5. **Coverage Analysis:** Ensure ≥ 90% coverage
6. **Performance Testing:** Verify performance targets

---

**Status:** Test Plan Complete  
**Next:** Implement tests and validate implementation
