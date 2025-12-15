# Smoke E2E Tests

Fast, deterministic smoke tests that validate critical vertical slices without requiring real LLM or Context7 services.

## Characteristics

- **No network calls**: No real LLM, no real Context7
- **Deterministic**: Use fixed fixtures and seeded randomness where needed
- **Fast**: Run in under 30 seconds total
- **Stable**: Tests produce identical results on repeated runs
- **Contract-based**: Validate stable contracts (exit codes, JSON shape, file existence) rather than brittle text

## Test Coverage

### Workflow Parsing (`test_workflow_parsing.py`)

- Parse all shipped workflows from `workflows/` directory
- Validate workflow schema and cross-references
- Handle invalid workflow YAML gracefully

### Workflow Executor (`test_workflow_executor.py`)

- Initialize workflow executor with minimal workflow
- Advance workflow steps with mocked agents
- Validate state transitions (start → step → complete)
- Validate step execution order

### Workflow Persistence (`test_workflow_persistence.py`)

- Save workflow state to `.tapps-agents/workflow-state/`
- Load workflow state from persisted file
- Resume workflow from saved state
- Validate state consistency (checksums, version)

### Agent Lifecycle (`test_agent_lifecycle.py`)

- Agent activation (activate method)
- Agent execution (run method with mocked MAL)
- Agent cleanup (close method)
- Multiple agents can run in sequence

### Worktree Cleanup (`test_worktree_cleanup.py`)

- Worktree creation under `.tapps-agents/worktrees/`
- Worktree cleanup (idempotent removal)
- Multiple worktrees can coexist
- Cleanup doesn't affect main working tree

## Running Smoke Tests

### Run All Smoke Tests

```bash
pytest tests/e2e/smoke/ -m e2e_smoke
```

### Run Specific Test File

```bash
pytest tests/e2e/smoke/test_workflow_parsing.py -m e2e_smoke
```

### Run with Verbose Output

```bash
pytest tests/e2e/smoke/ -m e2e_smoke -v
```

## Performance

All smoke tests should run in under 30 seconds total. If tests are taking longer:

1. Check for unnecessary I/O operations
2. Verify mocks are being used instead of real services
3. Review test complexity and simplify if needed

## Best Practices

1. **Use mocks**: Always use `mock_mal` fixture for LLM operations
2. **Validate contracts**: Test stable contracts (exit codes, JSON shape) not brittle text
3. **Keep it fast**: Each test should complete in seconds
4. **Be deterministic**: Tests should produce identical results on repeated runs
5. **Use appropriate templates**: Choose the simplest template that meets test needs

## Troubleshooting

### Tests Failing with Network Errors

Ensure tests are using mocked services. Check that `mock_mal` fixture is being used.

### Tests Taking Too Long

Review test complexity and ensure mocks are being used. Consider breaking large tests into smaller ones.

### Tests Not Deterministic

Check for:
- Random number generation (use seeded random)
- Time-dependent operations (use stable clocks/mocks)
- External file system state (use isolated test projects)
