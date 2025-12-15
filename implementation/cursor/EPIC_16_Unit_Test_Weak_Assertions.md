# Epic 16: Fix Weak Assertions and Eliminate False Positives in Unit Tests

## Epic Goal

Replace weak, permissive assertions in unit tests with specific, meaningful validations that actually verify correctness. Eliminate false positives where tests pass even when functionality is broken.

## Epic Description

### Existing System Context

- **Current relevant functionality**: Unit tests exist across the codebase but many use weak assertions (`>= 0`, `is not None`, broad exception matching) that don't validate actual behavior
- **Technology stack**: pytest, Python 3.13+, existing test fixtures
- **Integration points**: 
  - All unit test files in `tests/unit/`
  - Test fixtures in `tests/conftest.py`
  - Test utilities and helpers
- **Estimated scope**: 
  - ~50-75 weak assertions across the test suite
  - 4 high-priority files with critical weak assertions
  - ~10 medium-priority files with moderate issues

### Enhancement Details

- **What's being added/changed**: 
  - Replace weak assertions with specific expected values
  - Add validation of business logic outcomes
  - Fix tests that accept multiple outcomes without validation
  - Remove "may or may not" test patterns
  - Add assertions that verify actual correctness, not just structure

- **How it integrates**: 
  - Updates existing test files without changing test structure
  - Maintains existing fixtures and test organization
  - Improves test reliability and confidence

- **2025 standards / guardrails**:
  - **Test assertions must validate correctness**: Every assertion should verify specific expected behavior, not just that something exists or is in a range
  - **No permissive assertions**: Replace `>= 0`, `is not None`, `isinstance(result, dict)` with specific value checks
  - **Exception validation**: Match specific exception types and validate error messages, not just that exceptions are raised
  - **Business logic validation**: Tests must verify that correct outcomes occur, not just that methods don't crash

- **Success criteria**: 
  - All weak assertions replaced with specific validations
  - Tests fail when functionality is broken
  - No false positives in test suite
  - Test coverage of actual behavior increases

## Stories

1. **Story 16.1: Fix Weak Assertions in Core Tests**
   
   **Specific Files and Lines**:
   - `tests/unit/context7/test_cleanup.py`: Lines 240, 256, 271
   - `tests/unit/test_scoring.py`: Lines 58-67, 98-103
   - `tests/unit/test_agent_base.py`: Lines 103-105, 280-283
   - `tests/unit/test_workflow_executor.py`: Lines 276, 296
   
   **Tasks**:
   - Replace `>= 0` assertions with specific expected values
   - Fix `is not None` checks to validate actual values
   - Replace broad exception matching with specific exceptions and error message validation
   - Add specific value assertions for scoring, cleanup, and workflow execution results
   
   **Example Fixes**:
   
   ```python
   # BEFORE (test_cleanup.py:240)
   result = cleanup.cleanup_by_age(max_age_days=30)
   assert result.entries_removed >= 0  # Always passes!
   
   # AFTER
   result = cleanup.cleanup_by_age(max_age_days=30)
   assert result.entries_removed == 2  # Validates actual cleanup occurred
   assert result.reason == "age_cleanup"
   # Verify entries actually removed from cache
   assert "old_entry_1" not in cache
   assert "old_entry_2" not in cache
   ```
   
   ```python
   # BEFORE (test_scoring.py:58-59)
   assert result["complexity_score"] >= 0  # Always passes!
   assert result["complexity_score"] <= 10
   
   # AFTER
   # Simple code should have low complexity (good score)
   assert result["complexity_score"] >= 8.0  # High score = low complexity
   assert result["complexity_score"] <= 10.0
   ```
   
   ```python
   # BEFORE (test_agent_base.py:280-283)
   with pytest.raises((ValueError, FileNotFoundError)):  # Too broad!
       agent.load_config(invalid_path)
   
   # AFTER
   with pytest.raises(FileNotFoundError, match=r"Config file.*not found"):
       agent.load_config(invalid_path)
   # Validate specific exception type and error message
   ```

2. **Story 16.2: Fix Permissive Test Outcomes**
   
   **Specific Files and Lines**:
   - `tests/unit/context7/test_commands.py`: Lines 113, 119-120
   - `tests/unit/workflow/test_detector.py`: Lines 35, 48-49
   - `tests/unit/test_agent_integration.py`: Lines 105-120
   
   **Tasks**:
   - Remove "may or may not" test patterns
   - Fix tests that accept multiple outcomes without validating which is correct
   - Replace `or` operator assertions with specific expected values
   - Add validation for fuzzy matching logic and detection accuracy
   
   **Expected Behaviors**:
   - Fuzzy match should return specific match or None (not "may or may not")
   - Detection should return specific project type (not "may be generic")
   - Error messages should be validated, not just presence checked
   
   **Example Fixes**:
   
   ```python
   # BEFORE (test_commands.py:119-120)
   result = fuzzy_match(command)
   assert result is None or result is not None  # Always passes!
   
   # AFTER
   result = fuzzy_match("refersh")  # Typo
   assert result is not None
   assert result.command == "refresh"  # Should match to correct command
   assert result.confidence >= 0.8  # High confidence match
   ```
   
   ```python
   # BEFORE (test_detector.py:48-49)
   project_type = detector.detect_project_type(path)
   assert project_type is not None  # Doesn't validate correctness
   
   # AFTER
   project_type = detector.detect_project_type(python_project_path)
   assert project_type == "python"  # Validate specific type
   assert project_type != "generic"  # Should detect specific type
   ```
   
   ```python
   # BEFORE (test_commands.py:113)
   assert success is False  # Doesn't validate error message
   
   # AFTER
   assert success is False
   assert "File not found" in result["error"]  # Validate error message
   assert result["error_code"] == "FILE_NOT_FOUND"  # Validate error code
   ```

3. **Story 16.3: Add Business Logic Validation to Scoring Tests**
   
   **Tasks**:
   - Verify that simple code scores better than complex code
   - Validate that insecure code scores lower than secure code
   - Test that maintainable code scores higher
   - Verify overall score calculation formula is correct
   - Add tests for weighted average calculations
   
   **Test Data Requirements**:
   
   ```python
   # Simple code (low complexity, good security)
   SIMPLE_CODE = '''
   def hello():
       return "world"
   '''
   
   # Complex code (high complexity, nested logic)
   COMPLEX_CODE = '''
   def process(data):
       result = []
       for i in range(len(data)):
           for j in range(len(data[i])):
               for k in range(len(data[i][j])):
                   if data[i][j][k] > 0:
                       result.append(process_item(data[i][j][k]))
       return result
   '''
   
   # Insecure code (uses eval, exec, SQL injection)
   INSECURE_CODE = '''
   def process_user_input(user_input):
       result = eval(user_input)  # Security risk!
       return result
   '''
   
   # Maintainable code (documented, typed, clear)
   MAINTAINABLE_CODE = '''
   def calculate_total(items: list[float]) -> float:
       """Calculate the total price of items.
       
       Args:
           items: List of item prices
           
       Returns:
           Total price of all items
       """
       return sum(items)
   '''
   ```
   
   **Expected Score Relationships**:
   - `simple_score > complex_score` (for complexity metric)
   - `secure_score > insecure_score` (for security metric)
   - `maintainable_score > unmaintainable_score` (for maintainability metric)
   - `overall_score = weighted_average(complexity, security, maintainability)`
   
   **Example Test**:
   
   ```python
   def test_scoring_relative_scores(self, tmp_path):
       """Test that scoring correctly ranks code quality."""
       scorer = CodeScorer()
       
       simple_file = tmp_path / "simple.py"
       simple_file.write_text(SIMPLE_CODE)
       simple_result = scorer.score_file(simple_file, SIMPLE_CODE)
       
       complex_file = tmp_path / "complex.py"
       complex_file.write_text(COMPLEX_CODE)
       complex_result = scorer.score_file(complex_file, COMPLEX_CODE)
       
       # Simple code should score better than complex code
       assert simple_result["complexity_score"] > complex_result["complexity_score"]
       assert simple_result["overall_score"] > complex_result["overall_score"]
       
       # Insecure code should have low security score
       insecure_file = tmp_path / "insecure.py"
       insecure_file.write_text(INSECURE_CODE)
       insecure_result = scorer.score_file(insecure_file, INSECURE_CODE)
       
       assert insecure_result["security_score"] < 5.0  # Low security score
       assert insecure_result["security_score"] < simple_result["security_score"]
   ```

## Dependencies

- **Prerequisites**: None - can start immediately
- **Blocks**: None - doesn't block other work
- **Can be done in parallel with**: Epic 17, Epic 18 (different test files)
- **Related Epics**: Part of Epic 16-20 unit test improvement initiative

## Compatibility Requirements

- [ ] Test changes don't break existing test infrastructure
- [ ] Fixtures remain compatible
- [ ] Test execution time doesn't significantly increase
- [ ] No changes to production code required

## Risk Mitigation

- **Primary Risk**: Fixing assertions may reveal existing bugs, requiring code fixes
- **Mitigation**: 
  - Fix tests incrementally by module
  - Document any bugs discovered during test fixes
  - Prioritize high-risk test files first
- **Rollback Plan**: 
  - Test changes can be reverted independently
  - No impact on production code
  - Can fix tests in phases

## Definition of Done

- [ ] All weak assertions replaced with specific validations
- [ ] Zero `>= 0` assertions remain (except where mathematically necessary)
- [ ] Zero `is not None` checks without value validation
- [ ] No false positive tests remain
- [ ] Tests validate actual business logic outcomes
- [ ] Exception handling tests validate error messages
- [ ] Test suite reliability improved (tests fail when functionality breaks)
- [ ] All high-risk test files updated:
  - [ ] `tests/unit/context7/test_cleanup.py`
  - [ ] `tests/unit/test_scoring.py`
  - [ ] `tests/unit/context7/test_commands.py`
  - [ ] `tests/unit/workflow/test_detector.py`
  - [ ] `tests/unit/test_agent_base.py`
  - [ ] `tests/unit/test_workflow_executor.py`
- [ ] All exception tests validate error message content
- [ ] All scoring tests validate relative score relationships
- [ ] No regression in test execution time
- [ ] Test suite failure rate increases when functionality is intentionally broken (verified)

## Integration Verification

- **IV1**: Tests fail when functionality is intentionally broken
  - Intentionally break a function (e.g., return wrong value)
  - Verify test fails with clear error message
  - Measure test failure rate before/after epic completion
  
- **IV2**: All assertions validate specific expected values
  - Run grep for `>= 0` (without context) - should return 0 results in test files
  - Run grep for `is not None` (without value validation) - should return 0 results
  - Verify all assertions check specific values or relationships
  
- **IV3**: Exception tests validate error message content
  - Check exception tests validate `error_message` or `str(exception)` content
  - Verify specific exception types are tested (not broad matching)
  - Ensure error messages are meaningful and actionable
  
- **IV4**: Business logic tests verify correct outcomes
  - Run scoring tests with known inputs, verify outputs match expected formulas
  - Verify relative score relationships (simple > complex, secure > insecure)
  - Test cleanup actually removes entries (not just returns count)
  - Validate workflow execution order and dependencies

## Timeline

**Estimated Duration**: 1-2 weeks
- **Week 1**: Stories 16.1 and 16.2 (core fixes)
- **Week 2**: Story 16.3 (business logic validation) + verification

**Risk Buffer**: Add 20% buffer for bug discovery and fixes

**Status**: NOT STARTED

