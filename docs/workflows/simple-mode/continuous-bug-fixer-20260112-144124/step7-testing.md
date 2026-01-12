# Step 7: Testing Plan - Continuous Bug Finder and Fixer

## Testing Strategy

### Unit Tests

#### BugFinder Tests
- Test `_parse_pytest_output()` with various pytest output formats
- Test `_extract_source_file()` with different traceback formats
- Test `find_bugs()` with mock pytest execution
- Test edge cases: no failures, all failures, malformed output

#### BugFixCoordinator Tests
- Test `fix_bug()` with mock FixOrchestrator
- Test `verify_fix()` with mock test execution
- Test error handling when FixOrchestrator fails

#### CommitManager Tests
- Test `commit_fix()` with mock git operations
- Test `commit_batch()` with multiple bugs
- Test `_generate_commit_message()` with various bug types
- Test error handling for non-git repositories

#### ContinuousBugFixer Tests
- Test `execute()` with mock components
- Test iteration loop and stop conditions
- Test `_generate_summary()` with various result sets
- Test signal handling (interruption)

### Integration Tests

1. **Full Flow Test**
   - Run with real pytest (small test suite with known failures)
   - Mock FixOrchestrator to avoid LLM calls
   - Verify bug detection and fixing flow

2. **Git Integration Test**
   - Test commit operations in temporary git repository
   - Test batch commit strategy
   - Test one-per-bug commit strategy

3. **FixOrchestrator Integration Test**
   - Test actual FixOrchestrator integration (with mocked LLM)
   - Verify parameter passing
   - Verify result handling

### E2E Tests

1. **Basic E2E Test**
   - Create test project with failing tests
   - Run continuous-bug-fix command
   - Verify bugs are detected and fixed
   - Verify commits are created

2. **Error Handling E2E Test**
   - Test with tests that can't be fixed
   - Test with no git repository
   - Test with invalid test paths
   - Test interruption handling

## Test Files to Create

```
tests/unit/continuous_bug_fix/
  test_bug_finder.py
  test_bug_fix_coordinator.py
  test_commit_manager.py
  test_continuous_bug_fixer.py

tests/integration/continuous_bug_fix/
  test_full_flow.py
  test_git_integration.py
  test_fix_orchestrator_integration.py

tests/e2e/continuous_bug_fix/
  test_basic_e2e.py
  test_error_handling_e2e.py
```

## Test Data Requirements

1. **Pytest Output Samples**
   - Various pytest output formats
   - Different error types (TypeError, AttributeError, etc.)
   - Different traceback formats

2. **Test Projects**
   - Project with failing tests
   - Project with fixable bugs
   - Project with unfixable bugs
   - Project without git repository

## Testing Checklist

- [ ] Unit tests for BugFinder
- [ ] Unit tests for BugFixCoordinator
- [ ] Unit tests for CommitManager
- [ ] Unit tests for ContinuousBugFixer
- [ ] Integration test: Full flow
- [ ] Integration test: Git operations
- [ ] Integration test: FixOrchestrator integration
- [ ] E2E test: Basic functionality
- [ ] E2E test: Error handling
- [ ] Test coverage > 80%

## Manual Testing Steps

1. **Basic Usage Test**
   ```bash
   # Create test project with failing tests
   tapps-agents continuous-bug-fix --test-path tests/unit/ --max-iterations 3
   ```

2. **Dry Run Test**
   ```bash
   tapps-agents continuous-bug-fix --no-commit --max-iterations 2
   ```

3. **Batch Commit Test**
   ```bash
   tapps-agents continuous-bug-fix --commit-strategy batch --max-iterations 2
   ```

4. **Error Handling Test**
   ```bash
   # Test with invalid path
   tapps-agents continuous-bug-fix --test-path invalid/path/
   
   # Test without git repository (in temp directory)
   cd /tmp/test_project/
   tapps-agents continuous-bug-fix
   ```

## Performance Testing

- Test with large test suites (100+ tests)
- Test with many failures (50+ failures)
- Test iteration limits and timeout handling
- Measure execution time per iteration

## Security Testing

- Test git operations (no force push)
- Test file path validation
- Test command injection prevention
- Test permission handling

## Known Limitations

1. **No Tests Yet**
   - Implementation is complete but untested
   - Tests should be added before production use

2. **Configuration Not Integrated**
   - Config schema not added to config.py
   - Default values hardcoded in some places

3. **Limited Error Recovery**
   - Some errors cause full stop
   - Could add retry logic for transient failures

## Recommended Testing Order

1. **Phase 1: Unit Tests**
   - Start with BugFinder (parsing logic)
   - Then CommitManager (git operations)
   - Then BugFixCoordinator (integration logic)
   - Finally ContinuousBugFixer (orchestration)

2. **Phase 2: Integration Tests**
   - Full flow with mocked components
   - Git operations in test repositories
   - FixOrchestrator integration

3. **Phase 3: E2E Tests**
   - Basic functionality
   - Error handling
   - Edge cases

4. **Phase 4: Manual Testing**
   - Real-world scenarios
   - Performance testing
   - User acceptance testing
