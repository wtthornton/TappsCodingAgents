# E2E CI/CD Execution Guide

This document describes how E2E tests are executed in CI/CD pipelines.

## Overview

The E2E test suite is integrated into CI/CD with a clear execution matrix:
- **PR checks**: Fast tests only (unit + smoke E2E)
- **Main branch**: Unit + integration + workflow E2E (mocked)
- **Nightly**: Scenario E2E + real services (when credentials available)

## CI/CD Workflow

### GitHub Actions Workflow

The main E2E workflow is defined in `.github/workflows/e2e.yml`:

#### PR Checks Job

**Trigger:** Pull requests
**Command:** `pytest -m "unit or e2e_smoke"`
**Timeout:** 10 minutes
**Characteristics:**
- Fast execution (< 1 minute typically)
- No external service dependencies
- Deterministic results
- Suitable for PR gating

**Artifacts:**
- JUnit XML report (`junit-pr-checks.xml`)
- Test results (coverage, cache)

#### Main Branch Job

**Trigger:** Pushes to main branch
**Command:** `pytest -m "unit or integration or e2e_workflow"`
**Timeout:** 30 minutes
**Characteristics:**
- Moderate execution time (< 5 minutes typically)
- Uses mocked services (no external dependencies)
- Validates workflow execution

**Artifacts:**
- JUnit XML report (`junit-main-branch.xml`)
- Coverage report (`coverage.xml`)
- Test results (coverage, cache)

#### Nightly Job

**Trigger:** Schedule (2 AM UTC daily) or manual dispatch
**Command:** `pytest -m "e2e_scenario or (e2e_workflow and requires_llm) or (e2e_cli and requires_llm)"`
**Timeout:** 60 minutes
**Characteristics:**
- Longer execution time (10+ minutes)
- Uses real services (requires credentials)
- Validates complete user journeys
- Tests skip gracefully if credentials unavailable

**Artifacts:**
- JUnit XML report (`junit-nightly.xml`)
- Failure artifacts (if tests fail)
- Test summaries

## Marker Expressions

### PR Checks
```bash
pytest -m "unit or e2e_smoke"
```

### Main Branch
```bash
pytest -m "unit or integration or e2e_workflow"
```

### Nightly
```bash
pytest -m "e2e_scenario or (e2e_workflow and requires_llm) or (e2e_cli and requires_llm)"
```

## Credential Handling

### Required Credentials

For real-service tests, the following credentials may be required:
- `ANTHROPIC_API_KEY` - Anthropic API key
- `OPENAI_API_KEY` - OpenAI API key
- `CONTEXT7_API_KEY` - Context7 API key

### Credential Gates

Tests that require credentials will:
1. Check for required environment variables
2. Skip gracefully if credentials are unavailable (don't fail)
3. Only run when credentials are available

### Setting Up Credentials in GitHub Actions

1. Go to repository Settings → Secrets and variables → Actions
2. Add secrets:
   - `ANTHROPIC_API_KEY`
   - `OPENAI_API_KEY`
   - `CONTEXT7_API_KEY`
3. Credentials are automatically injected in nightly jobs

## Artifact Collection

### JUnit Reports

JUnit XML reports are generated for all test runs:
- Location: `junit-*.xml`
- Uploaded as CI artifacts
- Retention: 7-90 days (depending on job type)

### Failure Artifacts

On test failure, the following artifacts are collected:
- Logs from `.tapps-agents/logs/`
- State snapshots from `.tapps-agents/workflow-state/`
- Produced artifacts from project root
- Test output and error messages

**Important:** All artifacts are automatically redacted (secrets removed) before upload.

### Artifact Redaction

The following are automatically redacted from artifacts:
- API keys (patterns: `sk-*`, `sk-ant-*`)
- Tokens and secrets
- Passwords
- Environment variables containing sensitive data

## Safety Controls

### Timeout Controls

Different test types have different timeout limits:
- Smoke tests: 60 seconds
- Workflow tests: 300 seconds (5 minutes)
- Scenario tests: 1800 seconds (30 minutes)
- CLI tests: 300 seconds (5 minutes)

### Cost Controls

Cost controls are available for real-service tests:
- Token usage tracking
- API call counting
- Cost regression alerts

### Scheduled-Only Enforcement

Real-service tests only run:
- On schedule (nightly at 2 AM UTC)
- On manual workflow dispatch
- **Not** on PR checks or main branch pushes

## Local Execution

### Run PR Checks Locally

```bash
pytest -m "unit or e2e_smoke"
```

### Run Main Branch Tests Locally

```bash
pytest -m "unit or integration or e2e_workflow"
```

### Run Nightly Tests Locally

```bash
# Set credentials first
export ANTHROPIC_API_KEY=your_key
export OPENAI_API_KEY=your_key
export CONTEXT7_API_KEY=your_key

# Run tests
pytest -m "e2e_scenario or (e2e_workflow and requires_llm) or (e2e_cli and requires_llm)"
```

## Troubleshooting

### Tests Skipped Unexpectedly

Check if tests are marked with `requires_llm` or `requires_context7` and services are unavailable. Tests will skip gracefully (not fail).

### Tests Running Too Slowly

- Check timeout configurations
- Review test execution logs
- Consider optimizing slow tests

### Artifacts Not Uploaded

- Check CI workflow logs
- Verify artifact paths are correct
- Ensure artifacts are created before upload step

### Secrets in Artifacts

All artifacts are automatically redacted. If you see secrets in artifacts:
1. Report immediately
2. Check redaction patterns in `tests/e2e/fixtures/ci_artifacts.py`
3. Update redaction patterns if needed

## Best Practices

1. **Keep PR checks fast**: PR checks should complete in < 1 minute
2. **Use appropriate markers**: Mark tests with correct E2E type markers
3. **Default to mocked**: Don't mark tests with `requires_llm` unless necessary
4. **Test locally first**: Run tests locally before pushing
5. **Check artifacts on failure**: Always review failure artifacts for debugging

## CI/CD Integration Examples

### GitHub Actions

See `.github/workflows/e2e.yml` for the complete workflow definition.

### GitLab CI

```yaml
stages:
  - test

pr-checks:
  stage: test
  only:
    - merge_requests
  script:
    - pip install -e ".[dev]"
    - pytest -m "unit or e2e_smoke" --junitxml=junit-pr-checks.xml

main-branch:
  stage: test
  only:
    - main
  script:
    - pip install -e ".[dev]"
    - pytest -m "unit or integration or e2e_workflow" --junitxml=junit-main-branch.xml

nightly:
  stage: test
  only:
    - schedules
  script:
    - pip install -e ".[dev]"
    - pytest -m "e2e_scenario or (e2e_workflow and requires_llm)" --junitxml=junit-nightly.xml || true
  variables:
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
    CONTEXT7_API_KEY: $CONTEXT7_API_KEY
  allow_failure: true
```

### Jenkins

```groovy
pipeline {
    agent any
    stages {
        stage('PR Checks') {
            when { branch 'PR-*' }
            steps {
                sh 'pytest -m "unit or e2e_smoke" --junitxml=junit-pr-checks.xml'
            }
        }
        stage('Main Branch') {
            when { branch 'main' }
            steps {
                sh 'pytest -m "unit or integration or e2e_workflow" --junitxml=junit-main-branch.xml'
            }
        }
        stage('Nightly') {
            when { triggeredBy 'TimerTrigger' }
            steps {
                sh 'pytest -m "e2e_scenario or (e2e_workflow and requires_llm)" --junitxml=junit-nightly.xml || true'
            }
        }
    }
}
```

