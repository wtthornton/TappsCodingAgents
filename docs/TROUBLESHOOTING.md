# Troubleshooting Guide

**Version**: 2.0.4  
**Last Updated**: December 2025

## Installation

### `pip install` fails

- Ensure Python 3.13+ (recommended: latest stable Python):

```bash
python --version
```

- Upgrade tooling:

```bash
python -m pip install --upgrade pip
```

## CLI

### CLI runs but prints "Playwright not available"

Some browser-related functionality can run in a mocked mode if the **Python Playwright package** is not installed.

- If you're using **Cursor** with **Playwright MCP**, you can ignore this: browser automation should be done via Cursor Skills/Background Agents.
- If you need browser automation from the **CLI** (outside Cursor), install Playwright:

```bash
python -m pip install playwright
python -m playwright install
```

### "pytest is not recognized"

Some environments don’t expose `pytest` as a command. Use:

```bash
python -m pytest -q
```

(And ensure you installed dependencies in your venv.)

## Configuration

### "Configuration file not found"

This is not an error: configuration is optional.

If you want configuration, create:

- `.tapps-agents/config.yaml`

Recommended:

```bash
python -m tapps_agents.cli init
```

Or start from the template:

```bash
mkdir -p .tapps-agents
cp templates/default_config.yaml .tapps-agents/config.yaml
```

See `docs/CONFIGURATION.md`.

### Scoring weights validation error

If you see an error about weights not summing to 1.0, ensure `scoring.weights.*` totals ~1.0.

## Ollama / Local LLM

### Cannot connect to Ollama

- Verify Ollama is installed and running:

```bash
ollama list
```

- Ensure the URL in `.tapps-agents/config.yaml` matches your setup:

```yaml
mal:
  ollama_url: "http://localhost:11434"
```

### MAL disabled while running inside Cursor

If you see errors like **`MALDisabledInCursorModeError`**, that is expected when running the framework under Cursor
(including Cursor Background Agents). In this setup, **Cursor is the only LLM runtime** and the framework runs tools-only.

If you explicitly want to enable MAL for a headless CLI run, set:

```bash
export TAPPS_AGENTS_MODE=headless
```

## Quality Tools

### Ruff / mypy not found

These are Python dependencies. If you installed via `pip install -e .`, they should be available in the venv. Verify:

```bash
python -c "import ruff, mypy"  # may fail if not installed
```

Or run the CLI commands and inspect the error output:

```bash
python -m tapps_agents.cli reviewer lint path/to/file.py
python -m tapps_agents.cli reviewer type-check path/to/file.py
```

## Runtime Mode Issues

### Confusion between Cursor mode and headless mode

**Symptoms**: Errors like `MALDisabledInCursorModeError` or tools not working as expected.

**Solution**:
- **In Cursor**: Framework runs tools-only. Use Cursor Skills/Background Agents for LLM operations.
- **Headless CLI**: Set `TAPPS_AGENTS_MODE=headless` to enable MAL (if configured).

**Verify mode**:
```bash
# Check current mode
python -c "from tapps_agents.core.runtime_mode import detect_runtime_mode; print(detect_runtime_mode())"
```

## Credential Issues

### Context7 credentials invalid

**Symptoms**: Warnings about Context7 credential validation failures.

**Solution**:
1. Verify Context7 is enabled in `.tapps-agents/config.yaml`:
   ```yaml
   context7:
     enabled: true
   ```
2. Check MCP Gateway configuration if using Context7 via MCP.
3. Context7 is optional; agents will continue without it.

### MAL credentials missing (headless mode)

**Symptoms**: Connection errors when trying to use MAL in headless mode.

**Solution**:
1. Verify MAL configuration in `.tapps-agents/config.yaml`.
2. For Ollama: Ensure Ollama is running and accessible.
3. For cloud providers: Verify API keys are set correctly.
4. MAL is optional; only needed for headless CLI runs.

## Workflow Execution Issues

### Workflow stuck or failed

**Symptoms**: Workflow execution hangs or fails with unclear error messages.

**Solution**:
1. Check workflow state: `.tapps-agents/workflow-state/current_state.json`
2. Review error envelope in state file for structured error information.
3. Check logs for correlation IDs (workflow_id, step_id, agent).
4. Resume workflow if recoverable (see runbooks in `docs/RUNBOOKS.md`).

### Step timeout errors

**Symptoms**: Steps timing out during execution.

**Solution**:
1. Increase timeout in workflow step metadata:
   ```yaml
   steps:
     - id: long-running-step
       timeout: 1800  # 30 minutes
   ```
2. Check for resource constraints (CPU, memory, network).
3. Review step logs for performance bottlenecks.

## Artifact and Data Issues

### `.tapps-agents/` directory growing too large

**Symptoms**: Disk space issues from accumulated artifacts.

**Solution**:
1. Use cleanup tools (see `docs/RUNBOOKS.md` for cleanup procedures).
2. Configure retention policies in workflow configuration.
3. Manually clean old worktrees: `.tapps-agents/worktrees/`
4. Clean old analytics: `.tapps-agents/analytics/history/`

### Worktree merge conflicts

**Symptoms**: Git worktree operations failing with merge conflicts.

**Solution**:
1. Worktrees are automatically cleaned up after workflow completion.
2. For stuck worktrees, manually remove: `.tapps-agents/worktrees/<worktree-name>`
3. Ensure git repository is in a clean state before running workflows.

## Logging and Monitoring Issues

### Logs missing correlation fields

**Symptoms**: Logs don't include workflow_id, step_id, or trace_id.

**Solution**:
1. Ensure using `WorkflowLogger` for workflow-related logging.
2. Check that workflow executor is properly initialized.
3. Verify trace ID environment variables if using distributed tracing.

### Structured logging not working

**Symptoms**: Logs not in JSON format when `TAPPS_AGENTS_STRUCTURED_LOGGING=true` is set.

**Solution**:
1. Verify environment variable is set before importing modules.
2. Check that JSONFormatter is properly configured.
3. Review logging configuration in your application.

## Getting Help

- Run `python -m tapps_agents.cli --help`
- Check configuration docs: `docs/CONFIGURATION.md`
- Review runbooks: `docs/RUNBOOKS.md` (if available)
- File an issue with:
  - OS + Python version
  - CLI command you ran
  - Full stack trace / output
  - Correlation IDs (workflow_id, step_id, trace_id) if available
