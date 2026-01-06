# Step 7: Testing Plan and Validation - Codebase Context Injection

## Testing Overview

**Feature:** Codebase Context Injection for Enhancer Agent  
**Test Coverage Target:** 80%+  
**Test Types:** Unit Tests, Integration Tests, Edge Cases  
**Test Framework:** pytest

## Test Structure

```
tests/
  unit/
    agents/
      enhancer/
        test_codebase_context.py  # Unit tests for codebase context
  integration/
    agents/
      enhancer/
        test_codebase_context_integration.py  # Integration tests
```

## Unit Tests

### Test File: `tests/unit/agents/enhancer/test_codebase_context.py`

### 1. Test `_find_related_files()`

#### Test Case 1.1: Find Files by Domain
```python
async def test_find_related_files_by_domain():
    """Test finding files related to a domain."""
    # Setup: Create test files with domain-related content
    # Execute: Call _find_related_files() with domain in analysis
    # Assert: Returns files containing domain keywords
```

#### Test Case 1.2: Find Files by Technology
```python
async def test_find_related_files_by_technology():
    """Test finding files related to a technology."""
    # Setup: Create test files with technology-related content
    # Execute: Call _find_related_files() with technology in analysis
    # Assert: Returns files containing technology keywords
```

#### Test Case 1.3: Filter Excluded Files
```python
async def test_find_related_files_excludes_tests():
    """Test that test files are excluded."""
    # Setup: Create test files and regular files
    # Execute: Call _find_related_files()
    # Assert: Test files are not in results
```

#### Test Case 1.4: Limit Results
```python
async def test_find_related_files_limits_results():
    """Test that results are limited to max files."""
    # Setup: Create more than 10 matching files
    # Execute: Call _find_related_files()
    # Assert: Returns max 10 files
```

#### Test Case 1.5: Handle Empty Search Terms
```python
async def test_find_related_files_empty_search_terms():
    """Test handling of empty search terms."""
    # Setup: Analysis with no domains or technologies
    # Execute: Call _find_related_files()
    # Assert: Returns empty list
```

#### Test Case 1.6: Handle File Read Errors
```python
async def test_find_related_files_handles_errors():
    """Test error handling in file discovery."""
    # Setup: Files with permission errors
    # Execute: Call _find_related_files()
    # Assert: Returns valid list (skips error files)
```

### 2. Test `_extract_patterns()`

#### Test Case 2.1: Extract Import Patterns
```python
async def test_extract_patterns_imports():
    """Test extraction of import patterns."""
    # Setup: Files with common imports
    # Execute: Call _extract_patterns()
    # Assert: Returns import pattern
```

#### Test Case 2.2: Extract Class Patterns
```python
async def test_extract_patterns_classes():
    """Test extraction of class patterns."""
    # Setup: Files with Service/Agent/Router classes
    # Execute: Call _extract_patterns()
    # Assert: Returns class structure patterns
```

#### Test Case 2.3: Handle Syntax Errors
```python
async def test_extract_patterns_handles_syntax_errors():
    """Test handling of syntax errors."""
    # Setup: Files with invalid Python syntax
    # Execute: Call _extract_patterns()
    # Assert: Skips invalid files, continues with others
```

#### Test Case 2.4: Handle Empty Files
```python
async def test_extract_patterns_empty_files():
    """Test handling of empty files."""
    # Setup: Empty Python files
    # Execute: Call _extract_patterns()
    # Assert: Returns empty patterns list
```

### 3. Test `_find_cross_references()`

#### Test Case 3.1: Find Import References
```python
async def test_find_cross_references_imports():
    """Test finding import-based cross-references."""
    # Setup: Files with imports between them
    # Execute: Call _find_cross_references()
    # Assert: Returns cross-references
```

#### Test Case 3.2: Handle Missing Files
```python
async def test_find_cross_references_missing_files():
    """Test handling of missing files."""
    # Setup: File paths that don't exist
    # Execute: Call _find_cross_references()
    # Assert: Skips missing files, continues
```

#### Test Case 3.3: Handle Syntax Errors
```python
async def test_find_cross_references_syntax_errors():
    """Test handling of syntax errors."""
    # Setup: Files with invalid Python syntax
    # Execute: Call _find_cross_references()
    # Assert: Skips invalid files
```

### 4. Test `_generate_context_summary()`

#### Test Case 4.1: Generate Summary with Data
```python
def test_generate_context_summary_with_data():
    """Test summary generation with all data."""
    # Setup: Related files, patterns, cross-references
    # Execute: Call _generate_context_summary()
    # Assert: Returns formatted markdown
```

#### Test Case 4.2: Generate Summary with Empty Data
```python
def test_generate_context_summary_empty():
    """Test summary generation with empty data."""
    # Setup: Empty lists
    # Execute: Call _generate_context_summary()
    # Assert: Returns summary with "No ... found" messages
```

#### Test Case 4.3: Format Relative Paths
```python
def test_generate_context_summary_relative_paths():
    """Test that paths are formatted as relative."""
    # Setup: Absolute file paths
    # Execute: Call _generate_context_summary()
    # Assert: Paths in output are relative to project root
```

### 5. Test `_stage_codebase_context()`

#### Test Case 5.1: Successful Execution
```python
async def test_stage_codebase_context_success():
    """Test successful codebase context injection."""
    # Setup: Valid prompt and analysis
    # Execute: Call _stage_codebase_context()
    # Assert: Returns context dict with all keys
```

#### Test Case 5.2: Error Handling
```python
async def test_stage_codebase_context_error_handling():
    """Test error handling in codebase context stage."""
    # Setup: Analysis that causes errors
    # Execute: Call _stage_codebase_context()
    # Assert: Returns empty context (doesn't raise exception)
```

## Integration Tests

### Test File: `tests/integration/agents/enhancer/test_codebase_context_integration.py`

### 1. Full Pipeline Integration

#### Test Case I.1: End-to-End Enhancement with Context
```python
async def test_enhancement_pipeline_with_context():
    """Test full enhancement pipeline including codebase context."""
    # Setup: Real codebase with related files
    # Execute: Run full enhancement pipeline
    # Assert: Enhanced prompt includes codebase context
```

#### Test Case I.2: Context Included in Synthesis
```python
async def test_context_included_in_synthesis():
    """Test that codebase context is included in synthesis stage."""
    # Setup: Run enhancement through synthesis
    # Execute: Check synthesis output
    # Assert: Codebase context section present in enhanced prompt
```

### 2. Real Codebase Scenarios

#### Test Case I.3: Test with TappsCodingAgents Codebase
```python
async def test_with_real_codebase():
    """Test with actual TappsCodingAgents codebase."""
    # Setup: Use actual project files
    # Execute: Run codebase context injection
    # Assert: Finds relevant files, extracts patterns
```

#### Test Case I.4: Test with Empty Codebase
```python
async def test_with_empty_codebase():
    """Test with minimal codebase."""
    # Setup: Codebase with few files
    # Execute: Run codebase context injection
    # Assert: Handles gracefully, returns empty context
```

## Edge Cases

### 1. Error Scenarios

#### Edge Case 1.1: All Files Fail to Read
```python
async def test_all_files_fail_to_read():
    """Test when all files have read errors."""
    # Setup: Files with permission errors
    # Execute: Run codebase context injection
    # Assert: Returns empty context, doesn't crash
```

#### Edge Case 1.2: All Files Have Syntax Errors
```python
async def test_all_files_syntax_errors():
    """Test when all files have syntax errors."""
    # Setup: Files with invalid Python syntax
    # Execute: Run codebase context injection
    # Assert: Returns empty patterns/references, doesn't crash
```

#### Edge Case 1.3: Project Root Not Found
```python
async def test_project_root_not_found():
    """Test when project root doesn't exist."""
    # Setup: Invalid project root path
    # Execute: Run codebase context injection
    # Assert: Handles gracefully, returns empty context
```

### 2. Performance Scenarios

#### Edge Case 2.1: Very Large Codebase
```python
async def test_very_large_codebase():
    """Test with codebase containing many files."""
    # Setup: Codebase with 1000+ files
    # Execute: Run codebase context injection
    # Assert: Completes within 10 seconds, limits results
```

#### Edge Case 2.2: Very Large Files
```python
async def test_very_large_files():
    """Test with files exceeding size limit."""
    # Setup: Files > 100KB
    # Execute: Run codebase context injection
    # Assert: Large files are skipped
```

### 3. Data Scenarios

#### Edge Case 3.1: No Related Files Found
```python
async def test_no_related_files_found():
    """Test when no related files are found."""
    # Setup: Codebase with no matching files
    # Execute: Run codebase context injection
    # Assert: Returns empty context with appropriate message
```

#### Edge Case 3.2: No Patterns Extracted
```python
async def test_no_patterns_extracted():
    """Test when no patterns can be extracted."""
    # Setup: Files with no common patterns
    # Execute: Run codebase context injection
    # Assert: Returns empty patterns list
```

#### Edge Case 3.3: No Cross-References Found
```python
async def test_no_cross_references_found():
    """Test when no cross-references are found."""
    # Setup: Files with no imports between them
    # Execute: Run codebase context injection
    # Assert: Returns empty cross-references list
```

## Test Fixtures

### Fixture: Sample Codebase
```python
@pytest.fixture
def sample_codebase(tmp_path):
    """Create a sample codebase for testing."""
    # Create directory structure
    # Create sample Python files
    # Return codebase path
```

### Fixture: Enhancer Agent
```python
@pytest.fixture
async def enhancer_agent():
    """Create enhancer agent instance for testing."""
    # Create config
    # Create agent
    # Return agent
```

### Fixture: Analysis Dict
```python
@pytest.fixture
def sample_analysis():
    """Create sample analysis dict."""
    return {
        "domains": ["authentication", "user-management"],
        "technologies": ["FastAPI", "SQLAlchemy"],
        "intent": "feature",
        "scope": "module",
    }
```

## Test Execution Plan

### Phase 1: Unit Tests (Priority: High)
1. ✅ Write unit tests for all helper methods
2. ✅ Test error handling scenarios
3. ✅ Test edge cases
4. ✅ Achieve 80%+ coverage

### Phase 2: Integration Tests (Priority: Medium)
1. ✅ Write integration tests
2. ✅ Test with real codebase
3. ✅ Test full pipeline integration

### Phase 3: Performance Tests (Priority: Low)
1. ✅ Test with large codebase
2. ✅ Verify performance targets
3. ✅ Test optimization scenarios

## Validation Criteria

### Functional Validation
- ✅ Codebase context injection works correctly
- ✅ Related files are found accurately
- ✅ Patterns are extracted correctly
- ✅ Cross-references are detected
- ✅ Context summary is well-formatted

### Quality Validation
- ✅ Error handling works correctly
- ✅ Performance meets targets (< 10 seconds)
- ✅ Code follows project standards
- ✅ Documentation is complete

### Integration Validation
- ✅ Integrates with enhancement pipeline
- ✅ Doesn't break existing functionality
- ✅ Backward compatible (works without context)
- ✅ Logging is appropriate

## Test Coverage Report

**Target:** 80%+ coverage

**Current Status:** 0% (tests not yet written)

**Required Tests:**
- Unit tests: ~20 test cases
- Integration tests: ~5 test cases
- Edge cases: ~10 test cases
- **Total:** ~35 test cases

## Test Execution Commands

```bash
# Run all codebase context tests
pytest tests/unit/agents/enhancer/test_codebase_context.py -v

# Run integration tests
pytest tests/integration/agents/enhancer/test_codebase_context_integration.py -v

# Run with coverage
pytest tests/unit/agents/enhancer/test_codebase_context.py --cov=tapps_agents.agents.enhancer --cov-report=html

# Run specific test
pytest tests/unit/agents/enhancer/test_codebase_context.py::test_find_related_files_by_domain -v
```

## Next Steps

1. **Create Test File** - Create `test_codebase_context.py`
2. **Write Unit Tests** - Implement all unit test cases
3. **Write Integration Tests** - Implement integration test cases
4. **Run Tests** - Execute tests and verify coverage
5. **Fix Issues** - Address any test failures
6. **Update Coverage** - Ensure 80%+ coverage achieved

## Test Implementation Priority

### High Priority (Must Have)
1. Unit tests for all helper methods
2. Error handling tests
3. Basic integration tests

### Medium Priority (Should Have)
1. Edge case tests
2. Performance tests
3. Real codebase tests

### Low Priority (Nice to Have)
1. Stress tests
2. Optimization tests
3. Benchmark tests
