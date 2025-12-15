# E2E Scenario Tests

This directory contains end-to-end scenario tests that validate complete user journeys from start to finish.

## Overview

Scenario tests validate realistic user journeys (feature implementation, bug fix, refactoring) to provide high confidence that multi-agent orchestration, artifact handling, quality gates, and reporting work together end-to-end.

## Test Structure

### Test Files

- `test_feature_scenario.py` - Feature implementation scenario tests
- `test_bug_fix_scenario.py` - Bug fix scenario tests
- `test_refactor_scenario.py` - Refactoring scenario tests

## Scenario Types

### Feature Implementation Scenario

**Template**: Small project template  
**Workflow**: `workflows/presets/feature-implementation.yaml`  
**Journey**:
1. Feature request analysis
2. Feature design
3. Feature implementation
4. Code review with quality gates
5. Test generation and execution

**Expected Outcomes**:
- Feature code created
- Tests pass
- Quality gates pass
- Artifacts created (feature-spec.md, design.md, review-report.md, etc.)

### Bug Fix Scenario

**Template**: Small project template  
**Workflow**: `workflows/presets/quick-fix.yaml`  
**Journey**:
1. Bug report analysis
2. Bug reproduction
3. Bug fix implementation
4. Code review with quality gates
5. Test verification

**Expected Outcomes**:
- Bug fixed
- Tests pass
- Review gate passes
- Artifacts created (debug-report.md, review-report.md, etc.)

### Refactoring Scenario

**Template**: Medium project template  
**Workflow**: `workflows/multi-agent-refactor.yaml` or `workflows/presets/maintenance.yaml`  
**Journey**:
1. Refactor requirements analysis
2. Refactoring implementation
3. Code review with quality gates
4. Documentation updates
5. Regression test verification

**Expected Outcomes**:
- Refactored code
- Tests pass
- Quality maintained/improved
- Documentation updated
- Artifacts created (refactor-plan.md, review-report.md, refactor-docs.md, etc.)

## Running Scenario Tests

### Run All Scenario Tests (Mocked Mode)

```bash
pytest tests/e2e/scenarios/ -m e2e_scenario
```

### Run Specific Scenario Test

```bash
# Feature scenario
pytest tests/e2e/scenarios/test_feature_scenario.py -m e2e_scenario

# Bug fix scenario
pytest tests/e2e/scenarios/test_bug_fix_scenario.py -m e2e_scenario

# Refactor scenario
pytest tests/e2e/scenarios/test_refactor_scenario.py -m e2e_scenario
```

### Run with Real LLM (Scheduled Runs Only)

```bash
# Requires LLM credentials
pytest tests/e2e/scenarios/ -m "e2e_scenario and requires_llm"
```

## Test Characteristics

### Default Behavior (Mocked Mode)

- **Fast**: Tests run in under 5 minutes
- **Deterministic**: Uses mocked agents for consistent results
- **No external dependencies**: No real LLM or Context7 calls
- **Suitable for PR gating**: Can run in CI without credentials

### Real LLM Mode

- **Slow**: Tests run in 15-30 minutes
- **Non-deterministic**: Uses real LLM services
- **Requires credentials**: Needs LLM API keys
- **Scheduled runs only**: Marked with `requires_llm` marker

## Reliability Controls

Scenario tests include reliability controls:

- **Timeouts**: Per-scenario (30 min default), per-step (5 min default), per-workflow (30 min default)
- **Retries**: Bounded retries for transient failures (max 3 attempts, exponential backoff)
- **Cost Guardrails**: Token budgets, call limits, parallelism limits
- **Partial Progress Capture**: State snapshots and artifacts captured on failure

## Validation

Each scenario test validates:

1. **File Changes**: Expected files created/modified
2. **Artifacts**: Expected artifacts created (specs, reports, code, tests, docs)
3. **Test Outcomes**: Tests pass, new tests created
4. **Quality Signals**: Quality gates pass, scores meet thresholds

## Failure Handling

On failure, scenario tests:

1. Capture state snapshots
2. Capture artifacts (logs, state, outputs)
3. Create failure bundles with correlation IDs
4. Redact secrets from captured artifacts
5. Provide actionable error messages

## Configuration

### Timeout Configuration

```python
from tests.e2e.fixtures.reliability_controls import TimeoutConfig

timeout_config = TimeoutConfig(
    scenario_timeout_seconds=1800,  # 30 minutes
    step_timeout_seconds=300,       # 5 minutes
    workflow_timeout_seconds=1800,  # 30 minutes
)
```

### Retry Configuration

```python
from tests.e2e.fixtures.reliability_controls import RetryConfig

retry_config = RetryConfig(
    max_attempts=3,
    initial_backoff_seconds=2.0,
    max_backoff_seconds=60.0,
)
```

### Cost Configuration

```python
from tests.e2e.fixtures.reliability_controls import CostConfig

cost_config = CostConfig(
    max_tokens_per_scenario=100000,
    max_calls_per_scenario=100,
    max_parallel_scenarios=2,
)
```

Or via environment variables:

```bash
export E2E_MAX_TOKENS_PER_SCENARIO=100000
export E2E_MAX_CALLS_PER_SCENARIO=100
export E2E_MAX_PARALLEL_SCENARIOS=2
```

## Best Practices

1. **Use mocked mode by default**: Keep tests fast and deterministic
2. **Mark real LLM tests**: Use `@pytest.mark.requires_llm` for scheduled runs
3. **Validate contracts**: Test stable outcomes (artifacts, gates, reports) not free-form text
4. **Capture artifacts**: Use `e2e_artifact_capture` fixture for automatic capture on failure
5. **Set appropriate timeouts**: Use scenario-appropriate timeout values
6. **Monitor costs**: Track token usage and API calls in real LLM mode

## Troubleshooting

### Tests Timing Out

- Increase timeout values in test configuration
- Check for hanging operations
- Review workflow step timeouts

### Tests Failing Validation

- Check expected outputs match actual outputs
- Verify artifacts are created in correct locations
- Review scenario template setup

### Cost Budget Exceeded

- Reduce token budgets in cost configuration
- Optimize workflow to use fewer LLM calls
- Use mocked mode for development

## Related Documentation

- [E2E Test Suite README](../README.md)
- [Workflow E2E Tests](../workflows/README.md)
- [Smoke E2E Tests](../smoke/README.md)
- [Marker Taxonomy](../MARKER_TAXONOMY.md)

