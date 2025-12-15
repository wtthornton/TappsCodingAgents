# Epic 15: E2E Agent Behavior Testing & Command Validation

## Epic Goal

Add comprehensive E2E tests that validate **actual agent behavior** (command parsing, response generation, error handling) rather than just checking that agents can be activated and mocks can be called. Tests should verify that agents correctly process commands, generate appropriate responses, and handle errors correctly.

## Epic Description

### Existing System Context

- **Current relevant functionality**: E2E tests validate agent lifecycle (activate/run/close) but don't validate agent behavior:
  - `test_agent_execution` only checks that mock was called, not that agent logic works
  - No validation of command parsing
  - No validation of response generation
  - No validation of error handling
  - Generic `mock_mal` returns "Mock LLM response" without simulating real behavior
- **Technology stack**: `pytest`, existing agent implementations in `tapps_agents/agents/`, MAL abstraction layer.
- **Integration points**:
  - `tests/e2e/smoke/test_agent_lifecycle.py` - current agent tests
  - `tests/conftest.py` - `mock_mal` fixture
  - `tapps_agents/agents/*/agent.py` - agent implementations

### Enhancement Details

- **What's being added/changed**:
  - **Agent behavior tests**: Add E2E tests that validate agent command processing, response generation, and error handling.
  - **Command validation**: Test that agents correctly parse and validate commands.
  - **Response validation**: Test that agents generate appropriate responses based on input.
  - **Error handling tests**: Test that agents handle errors correctly (invalid commands, missing files, etc.).
  - **Agent-specific behavior**: Test agent-specific functionality (planner plans, implementer implements, reviewer reviews).

- **How it integrates**:
  - Extends existing agent lifecycle tests with behavior validation.
  - Adds new test files in `tests/e2e/agents/` for agent behavior testing.
  - Enhances `mock_mal` or creates agent-specific mocks that simulate behavior.
  - Integrates with workflow tests to validate agent behavior during workflow execution.

- **2025 standards / guardrails**:
  - **Behavioral validation**: Tests must validate agent behavior, not just that agents can be called.
  - **Command processing**: Validate that agents correctly parse, validate, and process commands.
  - **Response generation**: Validate that agents generate appropriate responses based on input and context.
  - **Error handling**: Validate that agents handle errors correctly (invalid input, missing files, network errors).
  - **Agent-specific behavior**: Test agent-specific functionality (e.g., planner creates plans, implementer writes code, reviewer provides feedback).
  - **Integration with workflows**: Validate agent behavior during actual workflow execution, not just in isolation.

- **Success criteria**:
  - Tests validate agent command parsing and validation
  - Tests validate agent response generation
  - Tests validate agent error handling
  - Tests validate agent-specific behavior
  - Tests validate agent behavior during workflow execution

## Stories

1. **Story 15.1: Agent Command Processing Tests**
   - Add E2E tests for agent command parsing and validation:
     - Test valid commands are accepted
     - Test invalid commands are rejected with clear errors
     - Test command parameter validation
     - Test command help/usage output
   - Create test utilities in `tests/e2e/fixtures/agent_test_helpers.py`
   - Add tests for each agent type (planner, implementer, reviewer, etc.)

2. **Story 15.2: Agent Response Generation Tests**
   - Add E2E tests for agent response generation:
     - Test that agents generate appropriate responses based on input
     - Test that responses are properly formatted
     - Test that responses contain expected information
     - Test that responses are contextually appropriate
   - Create response validation utilities
   - Add tests for each agent type

3. **Story 15.3: Agent Error Handling Tests**
   - Add E2E tests for agent error handling:
     - Test handling of invalid input
     - Test handling of missing files
     - Test handling of network errors (with mocked MAL)
     - Test handling of permission errors
     - Test error message clarity and actionability
   - Create error scenario test fixtures
   - Add tests for each agent type

4. **Story 15.4: Agent-Specific Behavior Tests**
   - Add E2E tests for agent-specific functionality:
     - Planner: validates plan creation, plan structure, plan completeness
     - Implementer: validates code generation, code correctness, code style
     - Reviewer: validates review feedback, review quality, gate evaluation
     - Tester: validates test generation, test execution, test results
   - Create agent-specific test utilities
   - Add comprehensive tests for each agent

5. **Story 15.5: Agent Behavior in Workflow Context**
   - Add E2E tests that validate agent behavior during workflow execution:
     - Test that agents receive correct context from workflow
     - Test that agents produce artifacts that workflow expects
     - Test that agents handle workflow-specific errors
     - Test that agents integrate correctly with workflow state
   - Extend workflow tests to validate agent behavior
   - Add integration tests for agent-workflow interaction

## Compatibility Requirements

- [ ] New tests are additive (don't break existing tests)
- [ ] Agent behavior tests can run with mocked MAL (no real LLM required)
- [ ] Tests validate behavior without requiring real external services

## Risk Mitigation

- **Primary Risk**: Agent behavior tests are complex and may be brittle.
- **Mitigation**:
  - Use behavioral mocks for fast, deterministic testing
  - Test agent behavior in isolation first, then in workflow context
  - Add clear error messages for debugging
  - Use contract-based validation (validate response structure, not exact text)
- **Rollback Plan**: Agent behavior tests can be disabled via markers if needed.

## Definition of Done

- [x] Agent command processing tests implemented
- [x] Agent response generation tests implemented
- [x] Agent error handling tests implemented
- [x] Agent-specific behavior tests implemented
- [x] Agent behavior in workflow context tests implemented
- [x] All tests pass consistently
- [x] Documentation updated with agent testing patterns

## Status

**COMPLETE** - All stories implemented and tested. Agent behavior tests validate command processing, response generation, error handling, agent-specific behavior, and workflow context integration.

## Story Manager Handoff

"Please develop detailed user stories for Epic 15 (E2E Agent Behavior Testing). Key considerations:
- Test agent command parsing and validation
- Test agent response generation and formatting
- Test agent error handling and error messages
- Test agent-specific functionality (planner plans, implementer implements, reviewer reviews)
- Test agent behavior during workflow execution
- Use behavioral mocks for fast, deterministic testing
- Validate behavior, not just that agents can be called"

