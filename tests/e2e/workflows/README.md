# E2E Workflow Tests

This directory contains end-to-end tests for workflow execution, covering preset workflows, state management, and failure/resume scenarios.

## Test Structure

### Test Files

- `test_full_sdlc_workflow.py` - Tests for the full SDLC preset workflow
- `test_quality_workflow.py` - Tests for the quality improvement preset workflow
- `test_quick_fix_workflow.py` - Tests for the quick-fix preset workflow
- `test_workflow_failure_resume.py` - Tests for workflow failure and resume functionality

## Test Coverage

### Tier-1 Preset Workflows

The tests cover the most important preset workflows:

1. **Full SDLC** (`full-sdlc.yaml`)
   - Complete software development lifecycle
   - All quality gates enabled
   - Multiple steps with dependencies

2. **Quality** (`quality.yaml`)
   - Code quality improvement cycle
   - Review and improvement steps
   - Quality gate routing

3. **Quick Fix** (`quick-fix.yaml`)
   - Fast bug fix workflow
   - Minimal overhead
   - Gate routing for review loop

### Test Types

Each workflow test validates:

- **Workflow Parsing**: YAML parsing and schema validation
- **Workflow Initialization**: Workflow start and state creation
- **Workflow Execution**: Step-by-step execution with state capture
- **State Transitions**: Workflow and step state transitions
- **Artifact Creation**: Expected artifacts are created
- **Gate Routing**: Gate pass/fail paths (where applicable)

### Failure and Resume Tests

The failure/resume tests validate:

- **State Persistence**: Workflow state is saved on failure
- **State Loading**: Persisted state can be loaded
- **State Consistency**: State remains consistent after save/load
- **Artifact Preservation**: Artifacts are preserved after failure
- **Resume Functionality**: Workflow can resume from persisted state

## Running Tests

### Run All Workflow E2E Tests

```bash
pytest tests/e2e/workflows/ -m e2e_workflow
```

### Run Specific Workflow Tests

```bash
# Full SDLC workflow
pytest tests/e2e/workflows/test_full_sdlc_workflow.py -m e2e_workflow

# Quality workflow
pytest tests/e2e/workflows/test_quality_workflow.py -m e2e_workflow

# Quick fix workflow
pytest tests/e2e/workflows/test_quick_fix_workflow.py -m e2e_workflow

# Failure and resume
pytest tests/e2e/workflows/test_workflow_failure_resume.py -m e2e_workflow
```

### Run with Real Services

By default, tests run in **mocked mode** (no real LLM calls). To run with real services:

```bash
pytest tests/e2e/workflows/ -m "e2e_workflow and requires_llm"
```

Note: Real mode requires LLM credentials to be configured.

## Test Execution Modes

### Mocked Mode (Default)

- No real LLM calls
- Deterministic execution
- Fast execution
- Suitable for CI/CD

### Real Mode

- Real LLM calls (requires credentials)
- Non-deterministic (may vary between runs)
- Slower execution
- Suitable for integration validation

## Using the Workflow Runner

The workflow runner harness provides utilities for E2E workflow testing:

```python
from tests.e2e.fixtures.workflow_runner import WorkflowRunner

# Create runner
runner = WorkflowRunner(project_path, use_mocks=True)

# Load workflow
workflow = runner.load_workflow(workflow_path)

# Run workflow
state, results = await runner.run_workflow(workflow_path, max_steps=10)

# Run step-by-step with state capture
state, snapshots, results = await runner.run_workflow_step_by_step(
    workflow_path, max_steps=10, capture_after_each_step=True
)

# Capture state snapshot
snapshot = runner.capture_workflow_state(executor, step_id="step1")

# Assert artifacts
runner.assert_workflow_artifacts(["artifact1.md", "artifact2.json"])

# Control gate outcomes
runner.control_gate_outcome("quality_gate", False)  # Force gate to fail
```

## Pytest Fixtures

The E2E conftest provides several fixtures:

- `workflow_runner` - WorkflowRunner instance (mocked by default)
- `gate_controller` - GateController for deterministic gate outcomes
- `workflow_project` - Alias for e2e_project
- `e2e_project` - Isolated test project (from Epic 8)
- `mock_mal` - Mocked Model Abstraction Layer (from tests/conftest.py)

## Test Markers

- `@pytest.mark.e2e_workflow` - Marks test as workflow E2E test
- `@pytest.mark.template_type("small")` - Specifies project template type
- `@pytest.mark.requires_llm` - Enables real LLM execution
- `@pytest.mark.timeout(60)` - Sets test timeout

## Best Practices

1. **Use Mocked Mode by Default**: Tests should run fast and deterministically
2. **Limit Step Execution**: Use `max_steps` to keep tests fast
3. **Validate Contracts**: Assert stable contracts (state, artifacts) not brittle text
4. **Capture State**: Use state snapshots for debugging failures
5. **Isolate Tests**: Each test uses an isolated project environment
6. **Clean Up**: Projects are automatically cleaned up after tests

## Troubleshooting

### Tests Time Out

- Reduce `max_steps` parameter
- Check for infinite loops in workflow execution
- Verify mocked agents are working correctly

### State Persistence Fails

- Check `.tapps-agents/workflow-state/` directory exists
- Verify file permissions
- Check state file format (should be valid JSON)

### Artifacts Not Found

- Verify artifact paths are correct
- Check if artifacts are created in mocked mode
- Use real mode for full artifact validation

## Related Documentation

- [E2E Test Suite Overview](../../e2e/README.md)
- [Marker Taxonomy](../../e2e/MARKER_TAXONOMY.md)
- [Workflow Runner Harness](../fixtures/workflow_runner.py)
