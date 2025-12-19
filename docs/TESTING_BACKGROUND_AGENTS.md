# Testing Background Agents Guide

**How to test TappsCodingAgents Background Agents**

This guide covers all methods for testing Background Agents in the TappsCodingAgents framework.

---

## Quick Reference

### Available Background Agents

1. **Quality Analyzer** - Project quality analysis and reports
2. **Test Runner** - Execute test suite
3. **Security Auditor** - Security scanning and dependency auditing
4. **PR Mode** - Verify changes and create PRs

---

## Method 1: Testing in Cursor IDE (Natural Language)

The easiest way to test Background Agents is using natural language triggers in Cursor AI chat.

### Quality Analyzer

**Trigger phrases:**
- "Analyze project quality"
- "Generate quality report"
- "Run lint and type check"
- "Check code quality"

**Expected results:**
- Quality analysis reports in `.tapps-agents/reports/`
- JSON files with scores and recommendations
- Progress files for monitoring

### Test Runner

**Trigger phrases:**
- "Run tests"
- "Run the test suite"
- "Check tests"

**Expected results:**
- Test execution results in `.tapps-agents/reports/`
- Coverage reports (if enabled)
- Test artifacts

### Security Auditor

**Trigger phrases:**
- "Run security scan"
- "Audit dependencies"
- "Security analysis"

**Expected results:**
- Security scan reports
- Dependency audit results
- Vulnerability reports

### PR Mode

**Trigger phrases:**
- "Open a PR with these changes"
- "Create a PR for this refactor"
- "Prepare a PR and run checks"
- "Make changes and open a PR"

**Expected results:**
- Isolated worktree with changes
- Pull request created
- Verification reports

### Monitoring Progress

1. **Progress Files**: Check `.tapps-agents/reports/progress-{task-id}.json`
2. **Cursor UI**: Background Agents panel shows real-time progress
3. **Logs**: Review Cursor's Background Agents logs

---

## Method 2: Automated Tests (pytest)

Run the integration test suite to verify Background Agents functionality.

### Run All Background Agent Tests

```bash
# Run all background agent integration tests
python -m pytest tests/integration/workflow/test_background_agents.py -v -m integration

# Run auto-execution integration tests
python -m pytest tests/integration/test_auto_execution_integration.py -v
```

### Run Specific Tests

```bash
# Test quality agent artifact creation
python -m pytest tests/integration/workflow/test_background_agents.py::test_background_quality_agent_creates_artifact -v

# Test testing agent artifact creation
python -m pytest tests/integration/workflow/test_background_agents.py::test_background_testing_agent_creates_artifact -v

# Test auto-executor with mock agent
python -m pytest tests/integration/test_auto_execution_integration.py::test_auto_executor_with_mock_agent -v
```

### Test Coverage

```bash
# Run with coverage report
python -m pytest tests/integration/workflow/test_background_agents.py -v -m integration --cov=tapps_agents.workflow --cov-report=html
```

---

## Method 3: Configuration Validation

Validate your Background Agent configuration file before testing.

### Validate Configuration

```bash
# Validate default configuration (.cursor/background-agents.yaml)
python -m tapps_agents.cli background-agent-config validate

# Validate with JSON output
python -m tapps_agents.cli background-agent-config validate --format json

# Validate custom configuration file
python -m tapps_agents.cli background-agent-config validate --config-path /path/to/config.yaml
```

### Generate Configuration

```bash
# Generate configuration from template
python -m tapps_agents.cli background-agent-config generate

# Generate minimal configuration
python -m tapps_agents.cli background-agent-config generate --minimal

# Overwrite existing configuration
python -m tapps_agents.cli background-agent-config generate --overwrite
```

---

## Method 4: Manual Command-Line Testing

Test Background Agents directly via command line.

### Test Quality Analyzer Commands

```bash
# Analyze project quality
python -m tapps_agents.cli reviewer analyze-project --format json

# Generate quality report
python -m tapps_agents.cli reviewer report . json markdown html --output-dir .tapps-agents/reports

# Run lint check
python -m tapps_agents.cli reviewer lint . --format json

# Run type check
python -m tapps_agents.cli reviewer type-check . --format json
```

### Test Test Runner Commands

```bash
# Run tests
python -m tapps_agents.cli tester run-tests
```

### Test Security Auditor Commands

```bash
# Run security scan
python -m tapps_agents.cli ops security-scan --target . --type all

# Audit dependencies
python -m tapps_agents.cli ops audit-dependencies --severity-threshold high --format json
```

### Test Background Wrapper

```bash
# Test background task wrapper
python -m tapps_agents.core.background_wrapper \
  --agent-id test-agent \
  --task-id test-task \
  --agent reviewer \
  --command analyze-project \
  --args '{"format": "json"}'
```

---

## Method 5: Programmatic Testing

Test Background Agents programmatically using Python.

### Test Quality Agent

```python
from pathlib import Path
from tapps_agents.workflow.background_quality_agent import BackgroundQualityAgent

# Create agent
agent = BackgroundQualityAgent(
    worktree_path=Path("."),
    correlation_id="test-quality-001",
    timeout_seconds=60.0,
)

# Run quality analysis
artifact = await agent.run_quality_analysis(target_path=Path("test.py"))

# Verify results
assert artifact.status in ["completed", "failed", "timeout"]
assert artifact.worktree_path == str(Path("."))
```

### Test Testing Agent

```python
from pathlib import Path
from tapps_agents.workflow.background_testing_agent import BackgroundTestingAgent

# Create agent
agent = BackgroundTestingAgent(
    worktree_path=Path("."),
    correlation_id="test-testing-001",
    timeout_seconds=60.0,
)

# Run tests
artifact = await agent.run_tests(test_path=Path("tests"), coverage=False)

# Verify results
assert artifact.status in ["completed", "failed", "timeout", "not_run"]
```

### Test Auto-Executor

```python
from tapps_agents.workflow.background_auto_executor import BackgroundAgentAutoExecutor

# Create executor
executor = BackgroundAgentAutoExecutor(
    polling_interval=0.1,
    timeout_seconds=5.0,
    project_root=Path("."),
    enable_metrics=True,
    enable_audit=True,
)

# Execute command
result = await executor.execute_command(
    command="@analyst gather-requirements --target-file test.md",
    worktree_path=Path("worktree"),
    workflow_id="test-workflow",
    step_id="test-step",
)

# Verify result
assert result["status"] == "completed"
assert result["success"] is True
```

---

## Method 6: Using Test Fixtures

Use provided test fixtures for consistent testing.

### Mock Background Agent

```python
from tests.fixtures.background_agent_fixtures import MockBackgroundAgent

# Create mock agent
mock_agent = MockBackgroundAgent(
    worktree_path=Path("worktree"),
    delay_seconds=0.1,
)

# Simulate execution
await mock_agent.simulate_execution(
    workflow_id="test-workflow",
    step_id="test-step",
    success=True,
    artifacts=["test.md"],
)
```

---

## Verification Checklist

After testing, verify:

- [ ] Configuration file exists: `.cursor/background-agents.yaml`
- [ ] Configuration is valid (no validation errors)
- [ ] Agents respond to trigger phrases in Cursor
- [ ] Results are generated in `.tapps-agents/reports/`
- [ ] Progress files are created during execution
- [ ] Worktrees are created and cleaned up properly
- [ ] Integration tests pass
- [ ] No errors in Cursor Background Agents logs

---

## Troubleshooting

### Agent Not Triggering

1. **Check Configuration**: Verify `.cursor/background-agents.yaml` exists
2. **Check Triggers**: Ensure trigger phrase matches configuration
3. **Check Cursor Version**: Ensure Background Agents support is enabled
4. **Validate Config**: Run `python -m tapps_agents.cli background-agent-config validate`

### Tests Failing

1. **Check Dependencies**: Ensure all test dependencies are installed
2. **Check Markers**: Use `-m integration` for integration tests
3. **Check Timeouts**: Some tests may need longer timeouts
4. **Check Worktrees**: Clean up unused worktrees with `git worktree list`

### No Results Generated

1. **Check Permissions**: Ensure write permissions to `.tapps-agents/reports/`
2. **Check Logs**: Review Cursor's Background Agents logs
3. **Check Worktree**: Verify worktree was created successfully
4. **Check Commands**: Test commands manually to verify they work

---

## See Also

- [BACKGROUND_AGENTS_GUIDE.md](BACKGROUND_AGENTS_GUIDE.md) - Full Background Agents guide
- [BACKGROUND_AGENTS_AUTO_EXECUTION_GUIDE.md](BACKGROUND_AGENTS_AUTO_EXECUTION_GUIDE.md) - Auto-execution guide
- [CURSOR_SKILLS_INSTALLATION_GUIDE.md](CURSOR_SKILLS_INSTALLATION_GUIDE.md) - Skills setup

---

## Quick Test Commands

```bash
# 1. Validate configuration
python -m tapps_agents.cli background-agent-config validate

# 2. Run integration tests
python -m pytest tests/integration/workflow/test_background_agents.py -v -m integration

# 3. Test quality analyzer command
python -m tapps_agents.cli reviewer analyze-project --format json

# 4. Test test runner command
python -m tapps_agents.cli tester run-tests

# 5. Test security auditor command
python -m tapps_agents.cli ops security-scan --target . --type all
```

