# Step 7: Testing - Priority 2 & 3 Missing Parts

**Workflow:** Simple Mode *build  
**Feature:** Complete Priority 2 & 3 - Missing Formatter Support and Pattern Enhancements  
**Date:** January 2025

---

## Test Plan Summary

### Test Coverage Goals

- **Unit Tests:** ≥ 80% coverage
- **Integration Tests:** End-to-end formatter tests
- **Edge Cases:** Empty data, malformed data, different formats

---

## Unit Tests

### Test File: `tests/cli/test_formatters_enhanced.py`

#### Test Suite 1: Library Recommendations Markdown Formatting

**Test Cases:**
1. `test_format_library_recommendations_markdown_basic`
   - Test basic formatting with best practices, common mistakes, examples
   - Verify markdown structure
   - Verify all sections present

2. `test_format_library_recommendations_markdown_empty`
   - Test with empty recommendations dict
   - Should return empty list

3. `test_format_library_recommendations_markdown_partial`
   - Test with only best practices (no mistakes, no examples)
   - Should only show best practices section

4. `test_format_library_recommendations_markdown_multiple_libs`
   - Test with multiple libraries
   - Verify each library formatted separately

5. `test_format_library_recommendations_markdown_malformed`
   - Test with malformed data (non-dict values)
   - Should handle gracefully

#### Test Suite 2: Pattern Guidance Markdown Formatting

**Test Cases:**
1. `test_format_pattern_guidance_markdown_basic`
   - Test basic formatting with recommendations, best practices
   - Verify markdown structure
   - Verify confidence score displayed

2. `test_format_pattern_guidance_markdown_empty`
   - Test with empty guidance dict
   - Should return empty list

3. `test_format_pattern_guidance_markdown_confidence`
   - Test with confidence score (float)
   - Test with detected flag (bool)
   - Verify correct display

4. `test_format_pattern_guidance_markdown_multiple_patterns`
   - Test with multiple patterns
   - Verify each pattern formatted separately

#### Test Suite 3: Library Recommendations HTML Formatting

**Test Cases:**
1. `test_format_library_recommendations_html_basic`
   - Test basic HTML formatting
   - Verify HTML structure
   - Verify styling classes

2. `test_format_library_recommendations_html_code_examples`
   - Test code examples in HTML
   - Verify `<pre><code>` blocks
   - Verify proper escaping

3. `test_format_library_recommendations_html_empty`
   - Test with empty recommendations
   - Should return empty list

#### Test Suite 4: Pattern Guidance HTML Formatting

**Test Cases:**
1. `test_format_pattern_guidance_html_basic`
   - Test basic HTML formatting
   - Verify HTML structure
   - Verify confidence display

2. `test_format_pattern_guidance_html_multiple_patterns`
   - Test with multiple patterns
   - Verify each pattern in separate section

#### Test Suite 5: Integration with Existing Formatters

**Test Cases:**
1. `test_format_markdown_with_library_recommendations`
   - Test format_markdown() with library_recommendations
   - Verify section appears in output
   - Verify integration with existing sections

2. `test_format_markdown_with_pattern_guidance`
   - Test format_markdown() with pattern_guidance
   - Verify section appears in output

3. `test_format_markdown_with_both_sections`
   - Test format_markdown() with both new sections
   - Verify both sections appear
   - Verify correct order

4. `test_format_html_with_library_recommendations`
   - Test format_html() with library_recommendations
   - Verify section appears in HTML
   - Verify styling

5. `test_format_html_with_pattern_guidance`
   - Test format_html() with pattern_guidance
   - Verify section appears in HTML

6. `test_format_markdown_batch_results`
   - Test batch results (list of results)
   - Verify each result formatted with new sections
   - Verify correct structure

7. `test_format_html_batch_results`
   - Test batch results in HTML
   - Verify each result formatted with new sections

#### Test Suite 6: Edge Cases

**Test Cases:**
1. `test_format_with_missing_sections`
   - Test formatters with data that doesn't have new sections
   - Should work normally (backward compatibility)

2. `test_format_with_empty_sections`
   - Test with empty library_recommendations dict
   - Test with empty pattern_guidance dict
   - Should not add sections

3. `test_format_with_none_values`
   - Test with None values in recommendations
   - Should handle gracefully

4. `test_format_with_unexpected_types`
   - Test with string values instead of dict
   - Test with list values
   - Should handle gracefully

---

## Integration Tests

### Test File: `tests/cli/test_formatters_integration.py`

#### Test Suite 1: End-to-End Formatter Tests

**Test Cases:**
1. `test_review_result_with_library_recommendations`
   - Create mock review result with library_recommendations
   - Format as markdown
   - Format as HTML
   - Verify output contains recommendations

2. `test_review_result_with_pattern_guidance`
   - Create mock review result with pattern_guidance
   - Format as markdown
   - Format as HTML
   - Verify output contains guidance

3. `test_review_result_with_both_sections`
   - Create mock review result with both sections
   - Format as markdown
   - Format as HTML
   - Verify both sections present

4. `test_batch_review_results`
   - Create multiple mock review results
   - Format as markdown (batch)
   - Format as HTML (batch)
   - Verify all results formatted correctly

---

## Test Data

### Sample Library Recommendations

```python
SAMPLE_LIBRARY_RECOMMENDATIONS = {
    "langchain": {
        "best_practices": [
            "Use chunking strategy for large documents",
            "Implement proper error handling for API calls"
        ],
        "common_mistakes": [
            "Not setting proper temperature for LLM",
            "Missing retry logic for API calls"
        ],
        "usage_examples": [
            "from langchain.llms import OpenAI\nllm = OpenAI(temperature=0.7)"
        ],
        "source": "context7"
    }
}
```

### Sample Pattern Guidance

```python
SAMPLE_PATTERN_GUIDANCE = {
    "rag_system": {
        "detected": True,
        "confidence": 0.8,
        "recommendations": [
            "Use semantic search for retrieval",
            "Implement proper chunking strategy"
        ],
        "best_practices": [
            "Use appropriate embedding models",
            "Implement proper vector store indexing"
        ],
        "source": "context7"
    }
}
```

### Sample Review Result

```python
SAMPLE_REVIEW_RESULT = {
    "file": "src/app.py",
    "scoring": {
        "overall_score": 85.0,
        "complexity_score": 7.5,
        "security_score": 8.0,
        "maintainability_score": 7.2
    },
    "library_recommendations": SAMPLE_LIBRARY_RECOMMENDATIONS,
    "pattern_guidance": SAMPLE_PATTERN_GUIDANCE
}
```

---

## Test Execution Plan

### Phase 1: Unit Tests
1. Create test file `tests/cli/test_formatters_enhanced.py`
2. Implement all unit test cases
3. Run tests: `pytest tests/cli/test_formatters_enhanced.py -v`
4. Target: 100% pass rate

### Phase 2: Integration Tests
1. Create test file `tests/cli/test_formatters_integration.py`
2. Implement integration test cases
3. Run tests: `pytest tests/cli/test_formatters_integration.py -v`
4. Target: 100% pass rate

### Phase 3: Coverage Analysis
1. Run coverage: `pytest --cov=tapps_agents/cli/formatters tests/cli/test_formatters_enhanced.py tests/cli/test_formatters_integration.py`
2. Target: ≥ 80% coverage
3. Identify uncovered lines
4. Add tests for uncovered lines if critical

### Phase 4: Manual Testing
1. Test with real review results
2. Test markdown output in markdown viewer
3. Test HTML output in browser
4. Verify visual appearance
5. Verify all sections display correctly

---

## Test Validation Criteria

### Unit Tests
- ✅ All test cases pass
- ✅ Edge cases handled
- ✅ Error cases handled
- ✅ No false positives

### Integration Tests
- ✅ End-to-end flow works
- ✅ All formatters work together
- ✅ Batch results work correctly
- ✅ Real-world scenarios covered

### Coverage
- ✅ ≥ 80% code coverage
- ✅ All critical paths covered
- ✅ Edge cases covered

### Manual Testing
- ✅ Markdown renders correctly
- ✅ HTML displays correctly
- ✅ All sections visible
- ✅ Styling consistent

---

## Test Implementation Notes

### Test Structure

```python
import pytest
from tapps_agents.cli.formatters import (
    _format_library_recommendations_markdown,
    _format_pattern_guidance_markdown,
    _format_library_recommendations_html,
    _format_pattern_guidance_html,
    format_markdown,
    format_html
)

class TestLibraryRecommendationsMarkdown:
    def test_basic(self):
        # Test implementation
        pass
    
    # More test methods...

class TestPatternGuidanceMarkdown:
    def test_basic(self):
        # Test implementation
        pass
    
    # More test methods...

# More test classes...
```

### Test Fixtures

```python
@pytest.fixture
def sample_library_recommendations():
    return SAMPLE_LIBRARY_RECOMMENDATIONS

@pytest.fixture
def sample_pattern_guidance():
    return SAMPLE_PATTERN_GUIDANCE

@pytest.fixture
def sample_review_result():
    return SAMPLE_REVIEW_RESULT
```

---

## Next Steps

1. **Implement Unit Tests:** Create `tests/cli/test_formatters_enhanced.py`
2. **Implement Integration Tests:** Create `tests/cli/test_formatters_integration.py`
3. **Run Tests:** Execute test suite
4. **Fix Issues:** Address any failing tests
5. **Coverage Analysis:** Ensure ≥ 80% coverage
6. **Manual Testing:** Verify visual output

---

**Status:** Test Plan Complete  
**Next:** Implement tests and validate implementation
