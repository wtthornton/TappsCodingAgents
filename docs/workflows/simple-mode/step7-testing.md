# Step 7: Testing Plan - Library Detection and Context7 Integration

**Workflow:** Simple Mode *build  
**Feature:** Priority 1 & 2 - Library Detection and Context-Aware Review Enhancement  
**Date:** January 2025

---

## Testing Strategy

### Test Coverage Goals
- **Unit Tests:** ≥ 80% coverage for all new components
- **Integration Tests:** End-to-end review workflow with library detection
- **Performance Tests:** Verify performance targets are met
- **Error Handling Tests:** Test all error scenarios

---

## Unit Tests

### 1. LibraryDetector Tests

**File:** `tests/agents/reviewer/test_library_detector.py`

**Test Cases:**
- [ ] `test_detect_from_code_imports` - Test basic import detection
- [ ] `test_detect_from_code_from_imports` - Test from imports
- [ ] `test_detect_from_code_relative_imports` - Test relative imports
- [ ] `test_detect_from_code_namespace_packages` - Test namespace packages
- [ ] `test_detect_from_code_stdlib_filtering` - Test stdlib filtering
- [ ] `test_detect_from_requirements_basic` - Test basic requirements.txt parsing
- [ ] `test_detect_from_requirements_with_versions` - Test version specifiers
- [ ] `test_detect_from_requirements_with_extras` - Test extras
- [ ] `test_detect_from_requirements_comments` - Test comment handling
- [ ] `test_detect_from_pyproject_basic` - Test basic pyproject.toml parsing
- [ ] `test_detect_from_pyproject_poetry` - Test Poetry dependencies
- [ ] `test_detect_all_merges_sources` - Test merging from all sources
- [ ] `test_detect_all_deduplication` - Test deduplication
- [ ] `test_detect_all_empty_code` - Test edge case: empty code
- [ ] `test_detect_all_invalid_syntax` - Test edge case: invalid Python syntax
- [ ] `test_detect_all_missing_files` - Test edge case: missing dependency files

**Mock Requirements:**
- Mock file system operations
- Mock AST parsing errors

### 2. PatternDetector Tests

**File:** `tests/agents/reviewer/test_pattern_detector.py`

**Test Cases:**
- [ ] `test_detect_rag_pattern_basic` - Test RAG pattern detection
- [ ] `test_detect_rag_pattern_multiple_indicators` - Test multiple indicators
- [ ] `test_detect_rag_pattern_confidence_calculation` - Test confidence scoring
- [ ] `test_detect_multi_agent_pattern_basic` - Test multi-agent pattern
- [ ] `test_detect_weighted_decision_pattern_basic` - Test weighted decision pattern
- [ ] `test_detect_patterns_all_patterns` - Test detecting all patterns
- [ ] `test_detect_patterns_confidence_threshold` - Test confidence filtering
- [ ] `test_detect_patterns_case_insensitive` - Test case-insensitive matching
- [ ] `test_detect_patterns_word_boundaries` - Test word boundary matching
- [ ] `test_detect_patterns_no_false_positives` - Test false positive prevention
- [ ] `test_detect_patterns_empty_code` - Test edge case: empty code
- [ ] `test_detect_patterns_line_numbers` - Test line number tracking

**Mock Requirements:**
- None (pure string matching)

### 3. Context7ReviewEnhancer Tests

**File:** `tests/agents/reviewer/test_context7_enhancer.py`

**Test Cases:**
- [ ] `test_get_library_recommendations_success` - Test successful lookup
- [ ] `test_get_library_recommendations_timeout` - Test timeout handling
- [ ] `test_get_library_recommendations_error` - Test error handling
- [ ] `test_get_library_recommendations_caching` - Test response caching
- [ ] `test_get_library_recommendations_batch` - Test batch lookups
- [ ] `test_get_pattern_guidance_success` - Test pattern guidance lookup
- [ ] `test_extract_best_practices` - Test best practices extraction
- [ ] `test_extract_common_mistakes` - Test common mistakes extraction
- [ ] `test_extract_examples` - Test usage examples extraction
- [ ] `test_extract_recommendations` - Test recommendations extraction
- [ ] `test_context7_disabled` - Test when Context7 is disabled

**Mock Requirements:**
- Mock Context7AgentHelper
- Mock Context7 responses
- Mock async operations

### 4. ReviewOutputEnhancer Tests

**File:** `tests/agents/reviewer/test_output_enhancer.py`

**Test Cases:**
- [ ] `test_enhance_output_with_library_recommendations` - Test library recommendations
- [ ] `test_enhance_output_with_pattern_guidance` - Test pattern guidance
- [ ] `test_enhance_output_with_both` - Test both recommendations and guidance
- [ ] `test_enhance_output_backward_compatibility` - Test backward compatibility
- [ ] `test_enhance_output_empty_recommendations` - Test empty recommendations
- [ ] `test_format_library_recommendations` - Test formatting
- [ ] `test_format_pattern_guidance` - Test formatting

**Mock Requirements:**
- Mock LibraryRecommendation objects
- Mock PatternGuidance objects

---

## Integration Tests

### 5. End-to-End Review Tests

**File:** `tests/agents/reviewer/test_reviewer_integration.py`

**Test Cases:**
- [ ] `test_review_file_with_library_detection` - Test full review with library detection
- [ ] `test_review_file_with_pattern_detection` - Test full review with pattern detection
- [ ] `test_review_file_with_context7` - Test full review with Context7 integration
- [ ] `test_review_file_output_format` - Test enhanced output format
- [ ] `test_review_file_backward_compatibility` - Test backward compatibility
- [ ] `test_review_file_performance` - Test performance targets

**Mock Requirements:**
- Mock file system
- Mock Context7AgentHelper
- Mock Context7 responses

---

## Performance Tests

### 6. Performance Validation

**File:** `tests/agents/reviewer/test_performance.py`

**Test Cases:**
- [ ] `test_library_detection_performance` - Verify < 100ms per file
- [ ] `test_pattern_detection_performance` - Verify < 50ms per file
- [ ] `test_context7_lookup_performance` - Verify timeout handling
- [ ] `test_review_time_increase` - Verify < 30% increase

**Requirements:**
- Use time.time() for measurements
- Run multiple iterations for accuracy

---

## Error Handling Tests

### 7. Error Scenario Tests

**Test Cases:**
- [ ] `test_library_detection_syntax_error` - Test invalid Python syntax
- [ ] `test_library_detection_file_not_found` - Test missing files
- [ ] `test_context7_lookup_timeout` - Test timeout scenarios
- [ ] `test_context7_lookup_network_error` - Test network failures
- [ ] `test_pattern_detection_empty_code` - Test edge cases

---

## Test Implementation Plan

### Phase 1: Unit Tests (Priority 1)
1. LibraryDetector unit tests
2. PatternDetector unit tests
3. ReviewOutputEnhancer unit tests
4. Context7ReviewEnhancer unit tests (with mocks)

### Phase 2: Integration Tests (Priority 2)
1. End-to-end review workflow tests
2. Output format validation tests

### Phase 3: Performance Tests (Priority 3)
1. Performance benchmark tests
2. Performance regression tests

---

## Test Data

### Sample Code Files

**test_code_with_langchain.py:**
```python
from langchain.llms import OpenAI
from langchain.vectorstores import FAISS
import pandas as pd

def rag_function():
    vectorstore = FAISS()
    return vectorstore
```

**test_code_with_agents.py:**
```python
from agents import Agent, Orchestrator

class MultiAgentSystem:
    def __init__(self):
        self.agent = Agent()
        self.orchestrator = Orchestrator()
```

**test_code_with_weighted.py:**
```python
def weighted_decision(scores, weights):
    weighted_score = sum(s * w for s, w in zip(scores, weights))
    return weighted_score
```

### Sample Dependency Files

**test_requirements.txt:**
```
langchain>=0.1.0
pandas==1.5.0
numpy[extra1,extra2]>=1.20.0
# This is a comment
```

**test_pyproject.toml:**
```toml
[project]
dependencies = [
    "langchain>=0.1.0",
    "pandas==1.5.0"
]

[tool.poetry.dependencies]
python = "^3.8"
langchain = "^0.1.0"
```

---

## Test Execution

### Running Tests

```bash
# Run all tests
pytest tests/agents/reviewer/test_library_detector.py -v

# Run with coverage
pytest tests/agents/reviewer/ --cov=tapps_agents/agents/reviewer --cov-report=html

# Run performance tests
pytest tests/agents/reviewer/test_performance.py -v -m performance
```

### Coverage Goals

- **LibraryDetector:** ≥ 90% coverage
- **PatternDetector:** ≥ 90% coverage
- **Context7ReviewEnhancer:** ≥ 80% coverage (mocked Context7)
- **ReviewOutputEnhancer:** ≥ 90% coverage
- **Overall:** ≥ 80% coverage

---

## Test Status

### Current Status
⏳ **Tests Not Yet Implemented**

**Next Steps:**
1. Create test files
2. Implement unit tests
3. Implement integration tests
4. Run tests and verify coverage
5. Fix any failing tests

---

## Validation Criteria

### Test Success Criteria
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Test coverage ≥ 80%
- ✅ Performance targets met
- ✅ Error handling verified
- ✅ Backward compatibility verified

---

**Next Step:** Implement tests according to this plan.

**Status:** ⏳ Pending Implementation
