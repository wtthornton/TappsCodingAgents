# Troubleshooting Guide

**Version**: 2.4.2  
**Last Updated**: January 2026

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

### Dependency Conflict Warning: pipdeptree and packaging

**Problem:** During installation, you see:
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
pipdeptree 2.30.0 requires packaging>=25, but you have packaging 24.2 which is incompatible.
```

**Cause:** TappsCodingAgents constrains `packaging>=23.2,<25` for `langchain-core` compatibility, but `pipdeptree>=2.30.0` requires `packaging>=25`. These are incompatible.

**Solution:** This is **non-fatal** and can be safely ignored. TappsCodingAgents works perfectly without `pipdeptree`.

- **Standard installation** (recommended): `pip install -e .` - No conflict ✅
- **If you need pipdeptree**: Install with `pip install -e ".[dependency-analysis]"` - Warning is expected ⚠️
- **If pipdeptree was installed separately**: `pip uninstall pipdeptree` to remove the warning

**See:** [DEPENDENCY_CONFLICT_PIPDEPTREE.md](DEPENDENCY_CONFLICT_PIPDEPTREE.md) for detailed explanation.

## CLI

### Cannot import '_version_' from 'tapps_agents' (Upgrade Required)

**Problem:** When running `python -m tapps_agents.cli --version` or any CLI command, you get:
```
ImportError: cannot import name '_version_' from 'tapps_agents' (unknown location)
```

**Cause:** You have an older version (2.0.1 or earlier) installed that has a bug preventing the CLI from running. The CLI can't run, so you can't use it to upgrade.

**Solution:** Upgrade directly using `pip`, bypassing the broken CLI:

```bash
# Upgrade to latest version
pip install --upgrade tapps-agents

# Or upgrade to specific version (3.0.1+ fixes this issue)
pip install --upgrade tapps-agents==3.0.1
```

**If installed as git submodule:**
```bash
cd TappsCodingAgents
git pull origin main
git checkout v3.0.1  # or latest tag
pip install -e .
```

**Verify after upgrade:**
```bash
python -m tapps_agents.cli --version
# Should show: tapps-agents 3.0.1
```

See [TROUBLESHOOTING_UPGRADE.md](TROUBLESHOOTING_UPGRADE.md) for detailed upgrade instructions.

### ModuleNotFoundError: No module named 'tapps_agents.agents.analyst' (After Upgrade)

**Problem:** After upgrading to 3.0.1 (or any new version), you get:
```
ModuleNotFoundError: No module named 'tapps_agents.agents.analyst'
```

**Cause:** When upgrading code to a new version but not reinstalling the package, editable installs can have stale metadata that prevents Python from finding modules correctly.

**Solution:** Reinstall the package to refresh the editable install:

```bash
# If installed via pip (editable mode):
cd /path/to/TappsCodingAgents
pip install -e .

# If installed as regular package, upgrade:
pip install --upgrade tapps-agents==3.0.1

# Verify the fix:
python -m tapps_agents.cli reviewer review --help
```

**Prevention:** Always reinstall after upgrading code when using editable installs:
```bash
git pull origin main  # or checkout new version
git checkout v3.0.1   # if upgrading to specific version
pip install -e .      # Refresh editable install
```

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

## Background Agents

### Unicode Encoding Errors on Windows

**Problem:** When running background agents or quality reports on Windows, you may encounter:
```
UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 3626: character maps to <undefined>
```

**Solution:** This has been fixed in version 2.0.6+. All subprocess calls now use UTF-8 encoding. If you still see this error:

1. **Update to latest version:**
   ```bash
   pip install --upgrade tapps-agents
   ```

2. **Verify encoding fix is applied:**
   - Check that `tapps_agents/agents/reviewer/scoring.py` has `encoding="utf-8"` in subprocess calls
   - Check that `tapps_agents/agents/reviewer/typescript_scorer.py` has `encoding="utf-8"` in subprocess calls

3. **Set environment variable (temporary workaround if needed):**
   ```powershell
   $env:PYTHONIOENCODING='utf-8'
   ```

### Background Agent Not Showing Progress

**Problem:** Background agents run but you don't see when they start or complete.

**Solution:** Execution indicators were added in version 2.0.6+. You should see:
- Clear start indicators when tasks begin
- Setup status messages
- Running indicators during execution
- Completion indicators when tasks finish

If indicators are not showing:
1. Ensure you're using version 2.0.6 or later
2. Check that output is not being redirected (indicators print to stderr)
3. Verify `.cursor/background-agents.yaml` is properly configured

## Workflow State Files

### "Failed to parse state file" Errors

**Problem:** You see repeated errors like:
```
Failed to parse state file .../full-sdlc-20251213-150718.json: Expecting value: line 26 column 9 (char 724)
```

**Status:** ✅ **Fixed in version 2.0.8+**

This issue was caused by reading state files while they were still being written. The fix includes:

1. **Atomic File Writing**: All state files are now written using a temp-then-rename pattern, ensuring files are only visible when fully written
2. **File Validation**: Files are validated before parsing (size checks, JSON validation)
3. **File Age Checks**: Files must be at least 2 seconds old before being read
4. **Retry Logic**: Automatic retries with exponential backoff for files that may be in transition
5. **Graceful Handling**: Incomplete or corrupted files return None instead of raising errors

**If you still see these errors:**
- Update to the latest version: `pip install --upgrade tapps-agents`
- Old corrupted files are automatically skipped (they won't cause errors)
- New state files are written atomically and won't have this issue

**For Developers:**
- See `docs/STATE_PERSISTENCE_DEVELOPER_GUIDE.md` for technical details
- The fix is in `tapps_agents/workflow/file_utils.py` and all state file writers

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

## LLM Operations

### All LLM operations handled by Cursor

The framework no longer uses local LLMs (Ollama) or requires API keys. All LLM operations are handled by Cursor Skills, which use the developer's configured model in Cursor.

If you see issues with agent operations:

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

**Symptoms**: Tools not working as expected or incorrect mode detection.

**Solution**:
- Ensure Cursor Skills are properly installed and configured.
- Verify agents are creating instruction objects correctly.
- Check Cursor integration settings.

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

### Instruction objects not being executed

**Symptoms**: Agents create instruction objects but Cursor Skills don't execute them.

**Solution**:
1. Verify Cursor Skills are installed: check `.claude/skills/` directory exists.
2. Ensure Cursor is properly configured and running.
3. Check that instruction objects have valid `to_skill_command()` output.
4. Review Cursor Skills logs for execution errors.

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
