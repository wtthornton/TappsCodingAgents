# E2E Learning Tests Review and Execution Report

**Date:** 2025-12-18  
**Test Suite:** `tests/e2e/learning/`  
**Total Tests:** 18  
**Status:** 13 Failed, 5 Passed

## Test Files Reviewed

1. `test_agent_learning_e2e.py` - 6 tests
2. `test_negative_feedback_e2e.py` - 5 tests  
3. `test_security_learning_e2e.py` - 4 tests
4. `test_workflow_learning_e2e.py` - 3 tests

## Issues Identified

### 1. API Mismatch: `failure_reasons` Parameter

**Problem:** Tests call `learn_from_task()` with `failure_reasons` parameter, but the method doesn't accept it.

**Affected Tests:**
- `test_learn_from_failure_and_recovery`
- `test_learn_from_real_failure`
- `test_failure_mode_analysis_e2e`

**Root Cause:** The `AgentLearner.learn_from_task()` method signature is:
```python
async def learn_from_task(
    self,
    capability_id: str,
    task_id: str,
    code: str | None = None,
    quality_scores: dict[str, float] | None = None,
    success: bool = True,
    duration: float = 0.0,
) -> dict[str, Any]:
```

The method internally extracts failure reasons from the `success=False` parameter, but tests are trying to pass `failure_reasons` explicitly.

**Fix:** Remove `failure_reasons` parameter from test calls. The method will extract failure reasons internally when `success=False`.

### 2. Pattern Extraction Returning 0

**Problem:** Many tests expect patterns to be extracted (`patterns_extracted > 0`), but the method returns 0.

**Affected Tests:**
- `test_learn_from_successful_task`
- `test_learn_across_multiple_tasks`
- `test_pattern_retrieval_and_reuse`
- `test_real_security_scanning_with_secure_code`
- `test_learn_from_low_quality_success` (anti-patterns)

**Root Cause:** Pattern extraction is controlled by:
1. Security threshold check (must pass security scan)
2. Decision engine threshold (quality score must meet threshold)
3. Learning intensity (must not be LOW)

The decision engine uses a default threshold of 0.7 (normalized quality score), and tests may be providing quality scores that don't meet this threshold after normalization.

**Fix:** 
- Adjust quality scores in tests to ensure they meet the threshold after normalization (0.7 * 10 = 7.0 on 0-10 scale)
- Or adjust the decision engine threshold for tests
- Ensure security scores pass the security threshold

### 3. Missing Method: `start_monitoring()`

**Problem:** `WorkflowActivityMonitor` doesn't have a `start_monitoring()` method.

**Affected Tests:**
- `test_learning_during_workflow_execution`
- `test_learning_state_in_workflow_context`

**Root Cause:** `WorkflowActivityMonitor` is a `WorkflowObserver` that automatically receives events when registered. It doesn't need a `start_monitoring()` method - it starts monitoring when registered as an observer.

**Fix:** Remove `await monitor.start_monitoring()` calls from `workflow_runner.py`. The monitor is already registered and will receive events automatically.

### 4. Key Name Mismatch: `optimization_suggestions`

**Problem:** Test expects `optimization_suggestions` key, but actual key is `improvement_suggestions`.

**Affected Tests:**
- `test_meta_learning_optimization_e2e`

**Fix:** Update test to use `improvement_suggestions` instead of `optimization_suggestions`.

### 5. Missing Attribute: `rejection_count`

**Problem:** Test tries to access `p.rejection_count` on anti-patterns, but this attribute may not exist or be 0.

**Affected Tests:**
- `test_learn_from_user_rejection`

**Root Cause:** The `CodePattern` dataclass has `rejection_count` field, but it may not be populated when learning from rejections. The `learn_from_rejection()` method may not be setting this field.

**Fix:** Check if `learn_from_rejection()` properly sets `rejection_count` on anti-patterns.

## Test Execution Results

### Passed Tests (5)
1. ✅ `test_learning_explainability_e2e`
2. ✅ `test_anti_pattern_exclusion_in_retrieval`
3. ✅ `test_security_threshold_enforcement`
4. ✅ `test_security_pattern_filtering`
5. ✅ `test_learning_persistence_across_sessions`

### Failed Tests (13)
1. ❌ `test_learn_from_successful_task` - patterns_extracted = 0
2. ❌ `test_learn_across_multiple_tasks` - patterns_extracted = 0
3. ❌ `test_learn_from_failure_and_recovery` - API mismatch (failure_reasons)
4. ❌ `test_pattern_retrieval_and_reuse` - patterns_extracted = 0
5. ❌ `test_meta_learning_optimization_e2e` - key name mismatch
6. ❌ `test_learn_from_real_failure` - API mismatch (failure_reasons)
7. ❌ `test_learn_from_user_rejection` - rejection_count = 0
8. ❌ `test_learn_from_low_quality_success` - anti_patterns_extracted = 0
9. ❌ `test_failure_mode_analysis_e2e` - API mismatch (failure_reasons)
10. ❌ `test_real_security_scanning_with_vulnerabilities` - anti_patterns_extracted = 0
11. ❌ `test_real_security_scanning_with_secure_code` - patterns_extracted = 0
12. ❌ `test_learning_during_workflow_execution` - missing start_monitoring()
13. ❌ `test_learning_state_in_workflow_context` - missing start_monitoring()

## Recommendations

1. **Fix API mismatches** - Update tests to match actual API signatures
2. **Adjust quality thresholds** - Ensure test quality scores meet extraction thresholds
3. **Fix workflow monitor** - Remove incorrect `start_monitoring()` calls
4. **Verify rejection handling** - Ensure `learn_from_rejection()` properly sets rejection_count
5. **Add test fixtures** - Consider adding fixtures to control learning thresholds for tests

## Next Steps

1. Fix all identified issues in test files
2. Re-run tests to verify fixes
3. Update test documentation if API changes are needed
4. Consider adding helper methods to simplify test setup

