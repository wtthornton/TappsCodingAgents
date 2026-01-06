# Step 7: Testing Plan - Doctor Cache Status Feature

## Test Strategy

### Unit Tests

#### Test File: `tests/unit/core/test_doctor_cache_status.py`

**Test Cases:**

1. **Test Context7 Disabled**
   - Config has Context7 disabled
   - Should return "ok" finding with "Disabled" message
   - No cache directory checks performed

2. **Test Context7 Enabled, Cache Directory Missing**
   - Context7 enabled in config
   - Cache directory doesn't exist
   - Should return "warn" finding with remediation

3. **Test Context7 Enabled, Cache Directory Not Writable**
   - Context7 enabled
   - Cache directory exists but not writable
   - Should return "warn" finding

4. **Test Context7 Enabled, Cache Empty**
   - Context7 enabled
   - Cache directory accessible
   - Cache has 0 entries
   - Should return "warn" finding with "Empty" message

5. **Test Context7 Enabled, Cache Populated**
   - Context7 enabled
   - Cache directory accessible
   - Cache has entries
   - Should return "ok" finding with entry count

6. **Test Context7 Import Error**
   - Context7 components not available
   - Should return None (graceful degradation)

7. **Test Cache Metrics Error**
   - Context7 enabled and accessible
   - Metrics calculation fails
   - Should return "warn" finding with fallback message

### Integration Tests

#### Test File: `tests/integration/cli/test_doctor_full_flag.py`

**Test Cases:**

1. **Test Doctor Without --full Flag**
   - Run `tapps-agents doctor`
   - Should show only doctor findings
   - Should not run health checks

2. **Test Doctor With --full Flag**
   - Run `tapps-agents doctor --full`
   - Should show doctor findings
   - Should also show health check results
   - Output should clearly distinguish sections

3. **Test Doctor --full JSON Output**
   - Run `tapps-agents doctor --full --format json`
   - Should include health_checks in JSON output
   - Should be valid JSON

4. **Test Doctor --full With Health Check Failure**
   - Health check system unavailable
   - Should still show doctor results
   - Should warn about health check failure

### Test Data Setup

**Fixtures Needed:**
- Config with Context7 enabled/disabled
- Mock cache directory structures
- Mock cache metrics (empty, populated)
- Mock health check results

### Test Coverage Goals

- **Unit Tests**: 100% coverage of `_check_context7_cache_status()`
- **Integration Tests**: All command-line scenarios
- **Edge Cases**: Import errors, permission errors, missing directories

### Validation Criteria

✅ All tests pass  
✅ No linter errors  
✅ Code coverage ≥ 80%  
✅ Windows compatibility verified  
✅ Backward compatibility maintained
