# E2E Test Suite

This directory contains end-to-end tests for TappsCodingAgents, organized by test type.

## Directory Structure

```
tests/e2e/
├── smoke/          # Fast, deterministic smoke tests (no external services)
├── workflows/      # Workflow execution E2E tests
├── scenarios/      # User journey scenario tests
├── cli/            # CLI command E2E tests
└── fixtures/       # Shared E2E fixtures and utilities
```

## Test Types

### Smoke Tests (`smoke/`)

Fast, deterministic tests that validate critical vertical slices without requiring real LLM or Context7 services.

**Characteristics:**
- No network calls (no real LLM, no real Context7)
- Use fixed fixtures and seeded randomness where needed
- Use stable clocks/mocks for time-dependent operations
- Tests produce identical results on repeated runs
- Run in under 30 seconds total

**Marker:** `@pytest.mark.e2e_smoke`

**Example:**
```python
@pytest.mark.e2e_smoke
def test_workflow_parsing(e2e_project):
    # Test workflow parsing without external services
    pass
```

### Workflow Tests (`workflows/`)

Tests that validate workflow execution end-to-end.

**Marker:** `@pytest.mark.e2e_workflow`

### Scenario Tests (`scenarios/`)

Tests that validate complete user journeys from start to finish.

**Marker:** `@pytest.mark.e2e_scenario`

### CLI Tests (`cli/`)

Tests that validate CLI commands work correctly end-to-end.

**Marker:** `@pytest.mark.e2e_cli`

## Project Templates

E2E tests use project templates to create isolated test environments. Three template tiers are available:

### Minimal Template

Single file, basic structure. Use for simple tests that don't need complex project structure.

```python
@pytest.mark.template_type("minimal")
def test_simple(e2e_project):
    # e2e_project contains a single main.py file
    pass
```

### Small Template

Multiple files, basic test structure, minimal dependencies. Use for tests that need a basic project structure.

```python
@pytest.mark.template_type("small")
def test_with_tests(e2e_project):
    # e2e_project contains src/ and tests/ directories
    pass
```

### Medium Template

Multi-file project, tests, dependencies, config files. Use for tests that need a realistic project structure.

```python
@pytest.mark.template_type("medium")
def test_complex(e2e_project):
    # e2e_project contains full project structure with dependencies
    pass
```

## E2E Harness Utilities

The E2E harness provides utilities for creating test projects, capturing artifacts, and managing test environments.

### Creating Test Projects

```python
from tests.e2e.fixtures.e2e_harness import create_test_project

project_path = create_test_project("minimal", tmp_path)
```

### Capturing Artifacts

```python
from tests.e2e.fixtures.e2e_harness import capture_artifacts

artifacts = capture_artifacts(project_path, "test_name", correlation_id)
```

### Asserting Artifacts

```python
from tests.e2e.fixtures.e2e_harness import (
    assert_artifact_exists,
    assert_artifact_content,
    assert_json_artifact_shape,
)

assert_artifact_exists(project_path, "artifact.txt")
assert_artifact_content(project_path, "artifact.txt", "expected content")
assert_json_artifact_shape(project_path, "data.json", ["required", "keys"])
```

## Fixtures

### `e2e_project`

Creates an isolated test project using a template.

```python
def test_something(e2e_project):
    # e2e_project is a Path to the test project
    pass
```

Use the `template_type` marker to specify which template to use:

```python
@pytest.mark.template_type("small")
def test_with_small_template(e2e_project):
    pass
```

### `e2e_correlation_id`

Generates a unique correlation ID for the test run.

```python
def test_something(e2e_project, e2e_correlation_id):
    # Use correlation_id for logging and artifact tracking
    pass
```

### `e2e_artifact_capture`

Automatically captures artifacts on test failure.

```python
def test_something(e2e_project, e2e_artifact_capture):
    # Artifacts are automatically captured if test fails
    pass
```

## Artifact Capture Conventions

### Correlation IDs

Each E2E test run gets a unique correlation ID in the format:
```
e2e-YYYYMMDD-HHMMSS-<random>
```

### State Snapshots

State snapshots are captured at key points:
- Workflow start
- Step transitions
- Failures

### Failure Bundles

Failure bundles include:
- Logs from `.tapps-agents/logs/`
- State snapshots from `.tapps-agents/workflow-state/`
- Produced artifacts from project root
- Step timeline
- Error information

### Secret Redaction

Secrets are automatically redacted from captured artifacts:
- API keys (common patterns)
- Custom secrets (if provided)

## Running E2E Tests

### Run All E2E Tests

```bash
pytest tests/e2e/ -m ""
```

### Run Smoke Tests Only

```bash
pytest tests/e2e/smoke/ -m e2e_smoke
```

### Run Workflow Tests

```bash
pytest tests/e2e/workflows/ -m e2e_workflow
```

### Run with Real Services

```bash
# Requires LLM service
pytest tests/e2e/ -m "e2e_workflow and requires_llm"

# Requires Context7
pytest tests/e2e/ -m "e2e_workflow and requires_context7"
```

## Marker Taxonomy

See [Marker & Execution Matrix Documentation](../docs/stories/8.2.marker-and-execution-matrix.md) for complete marker taxonomy and execution matrix.

## Windows Compatibility

All E2E utilities use `pathlib.Path` for cross-platform path handling. No bash-isms or shell commands are used.

## Best Practices

1. **Use appropriate templates**: Choose the simplest template that meets your test needs
2. **Mark tests correctly**: Use appropriate markers (`e2e_smoke`, `e2e_workflow`, etc.)
3. **Validate contracts**: Test stable contracts (exit codes, JSON shape, file existence) rather than brittle text
4. **Capture artifacts**: Use `e2e_artifact_capture` fixture for automatic artifact capture on failure
5. **Keep tests deterministic**: Smoke tests should produce identical results on repeated runs
6. **Use timeouts**: Add explicit timeouts to prevent tests from hanging

## Troubleshooting

### Tests Failing with Artifact Capture Errors

Artifact capture failures don't fail the test - they're logged as warnings. Check test logs for artifact capture issues.

### Tests Not Finding Project Files

Ensure you're using the `e2e_project` fixture and accessing files relative to the project path:

```python
def test_something(e2e_project):
    file_path = e2e_project / "main.py"  # Correct
    # Not: Path("main.py")  # Wrong - relative to current directory
```

### Tests Hanging

Add explicit timeouts:

```python
@pytest.mark.timeout(30)
def test_something(e2e_project):
    pass
```
