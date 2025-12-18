# E2E Learning System Tests

End-to-end tests for the agent learning system, validating learning functionality with real agent execution, workflow integration, and persistence.

## Test Files

- `test_agent_learning_e2e.py` - Agent learning with real execution
- `test_workflow_learning_e2e.py` - Learning in workflow context
- `test_security_learning_e2e.py` - Security-aware learning E2E
- `test_negative_feedback_e2e.py` - Negative feedback learning E2E

## Test Coverage

### Agent Learning E2E

- ✅ Learning from successful tasks
- ✅ Learning across multiple tasks
- ✅ Learning from failures and recovery
- ✅ Pattern retrieval and reuse
- ✅ Learning explainability
- ✅ Meta-learning optimization

### Workflow Learning E2E

- ✅ Learning during workflow execution
- ✅ Learning persistence across sessions
- ✅ Learning state in workflow context

### Security Learning E2E

- ✅ Real security scanning with vulnerabilities
- ✅ Real security scanning with secure code
- ✅ Security threshold enforcement
- ✅ Security pattern filtering

### Negative Feedback E2E

- ✅ Learning from real failures
- ✅ Learning from user rejections
- ✅ Learning from low-quality code
- ✅ Anti-pattern exclusion
- ✅ Failure mode analysis

## Running Tests

### Run All Learning E2E Tests

```bash
pytest tests/e2e/learning/ -m e2e_workflow
```

### Run Specific Test File

```bash
# Agent learning
pytest tests/e2e/learning/test_agent_learning_e2e.py -m e2e_workflow

# Workflow learning
pytest tests/e2e/learning/test_workflow_learning_e2e.py -m e2e_workflow

# Security learning
pytest tests/e2e/learning/test_security_learning_e2e.py -m e2e_workflow

# Negative feedback
pytest tests/e2e/learning/test_negative_feedback_e2e.py -m e2e_workflow
```

### Run with Verbose Output

```bash
pytest tests/e2e/learning/ -m e2e_workflow -v
```

## Test Characteristics

- **Real Execution**: Tests use real agent execution, not just mocks
- **Integration**: Tests validate learning system integration with agents and workflows
- **Persistence**: Tests validate learning state persistence (where applicable)
- **Security**: Tests use real security scanning with actual vulnerable code
- **Realistic Scenarios**: Tests use realistic code examples and failure scenarios

## Test Timeouts

All tests have appropriate timeouts:
- Agent learning tests: 60 seconds
- Workflow learning tests: 60-120 seconds
- Security learning tests: 60 seconds
- Negative feedback tests: 60 seconds

## Dependencies

These tests require:
- Real agent execution (can use mocked MAL for speed)
- Security scanner (Bandit or heuristic fallback)
- Learning system components
- Workflow executor (for workflow tests)

## Notes

- Some tests validate learning functionality that requires pattern persistence
- Full persistence testing may require additional storage implementation
- Workflow learning tests may need workflow executor integration updates

