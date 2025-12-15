# Epic 17: Reduce Mock Overuse and Add Integration Testing

## Epic Goal

Reduce excessive mocking in unit tests and add real integration tests that validate actual component behavior and interactions. Replace mock-heavy tests with tests that use real implementations or appropriate fakes.

## Epic Description

### Existing System Context

- **Current relevant functionality**: Unit tests heavily mock dependencies (MAL, agents, caches, expert registry), preventing validation of real behavior
- **Technology stack**: pytest, unittest.mock, existing test fixtures
- **Integration points**: 
  - Model Abstraction Layer (MAL) tests
  - Agent tests (ReviewerAgent, etc.)
  - Cache tests (UnifiedCache, KBCache)
  - Workflow executor tests
  - CLI tests

### Enhancement Details

- **What's being added/changed**: 
  - Replace mocks with real implementations where feasible
  - Use fakes instead of mocks for complex dependencies
  - Add integration tests for component interactions
  - Test actual network behavior, timeout handling, error responses
  - Validate real cache behavior, not just method calls
  - Test actual agent behavior, not just CLI wrappers

- **How it integrates**: 
  - Updates existing test files to use real implementations
  - Adds new integration test files where appropriate
  - Maintains test isolation through fixtures and test data
  - Uses test doubles (fakes) instead of mocks for complex dependencies

- **2025 standards / guardrails**:
  - **Prefer real implementations**: Use actual code paths unless there's a compelling reason to mock
  - **Use fakes over mocks**: For complex dependencies, create test doubles that implement real behavior
  - **Test integration**: Validate that components work together correctly
  - **Network testing**: Use test servers or fixtures for network-dependent tests
  - **Isolation through data**: Use test data and fixtures for isolation, not mocks

- **Success criteria**: 
  - Reduced mock usage in core test files
  - Integration tests validate component interactions
  - Real behavior is tested, not just method calls
  - Network and timeout behavior is validated
  - Cache behavior is actually tested

## Stories

1. ✅ **Story 17.1: Reduce Mocking in MAL Tests** (Completed 2025-01-15)
   - ✅ Replaced HTTP client mocks with httpx.MockTransport for real HTTP behavior
   - ✅ Test actual network behavior, timeout handling, and error responses
   - ✅ Validated real response parsing and error handling
   - ✅ Tested fallback logic with real provider behavior using routing transports

2. ✅ **Story 17.2: Add Real Agent Behavior Tests** (Completed 2025-01-15)
   - ✅ Reduced mocking in ReviewerAgent tests
   - ✅ Using real CodeScorer instances instead of mocks
   - ✅ Validated real agent execution paths and scoring results
   - ✅ Tested error propagation through real agent code

3. ✅ **Story 17.3: Test Real Cache Behavior** (Completed 2025-01-15)
   - ✅ Replaced mocked cache dependencies with real cache instances
   - ✅ Tested actual cache hit/miss behavior with real ContextManager
   - ✅ Validated cache storage and retrieval with real implementations
   - ✅ Used test fixtures for cache isolation (separate directories per test)

4. ✅ **Story 17.4: Add Component Integration Tests** (Completed 2025-01-15)
   - ✅ Updated CLI tests to use real ReviewerAgent instances (with MAL mocked)
   - ✅ Validated component interactions with real agent behavior
   - ✅ Tested error propagation with real component code paths

## Compatibility Requirements

- [ ] Test changes don't break existing test infrastructure
- [ ] Test execution time remains reasonable
- [ ] Tests remain isolated and don't affect each other
- [ ] No changes to production code required

## Risk Mitigation

- **Primary Risk**: Real implementations may require external dependencies or slow down tests
- **Mitigation**: 
  - Use test fixtures and test servers for external dependencies
  - Create fast fakes for slow operations
  - Use test data isolation instead of mocks
  - Mark slow integration tests appropriately
- **Rollback Plan**: 
  - Can revert to mocks if needed
  - Integration tests can be separated from unit tests
  - No impact on production code

## Definition of Done

- [x] Mock usage reduced in core test files (MAL, agents, caches)
- [x] Real implementations tested where feasible
- [x] Integration tests added for component interactions
- [x] Network behavior tested with test servers/fixtures (httpx.MockTransport)
- [x] Cache behavior validated with real cache instances
- [x] Test execution time remains acceptable
- [x] Tests remain isolated and reliable

## Integration Verification

- **IV1**: Tests validate real component behavior
- **IV2**: Integration tests verify component interactions
- **IV3**: Network and timeout behavior is tested
- **IV4**: Cache operations are validated with real instances

