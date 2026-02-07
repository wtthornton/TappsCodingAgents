# Troubleshooting Guide

**Version**: 3.6.4  
**Last Updated**: January 2026

## Installation

### `pip install` fails

- Ensure Python 3.12+ (recommended: latest stable Python):

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

**Understanding Playwright Options:**
- **Playwright MCP Server**: Browser automation via Cursor's MCP tools (recommended in Cursor)
- **Python Playwright Package**: Browser automation from CLI (required for CLI usage)

**If you're using Cursor:**
- If **Playwright MCP is configured**, you can ignore this message: browser automation should be done via Cursor Skills using Playwright MCP tools.
- To check if Playwright MCP is configured, run: `tapps-agents doctor` and look for "Playwright MCP" status. Doctor also reports Beads (bd) status (optional task tracking); see [Beads Integration](BEADS_INTEGRATION.md).
- To configure Playwright MCP, add it to `.cursor/mcp.json`:
  ```json
  {
    "mcpServers": {
      "Playwright": {
        "command": "npx",
        "args": ["-y", "@playwright/mcp-server"]
      }
    }
  }
  ```

**If you need browser automation from the CLI** (outside Cursor), install the Python Playwright package:

```bash
python -m pip install playwright
python -m playwright install
```

**Note**: Playwright MCP is optional. If not configured, tapps-agents will use the Python Playwright package when available.

### "pytest is not recognized"

Some environments don’t expose `pytest` as a command. Use:

```bash
python -m pytest -q
```

(And ensure you installed dependencies in your venv.)

## Init and Reset (Windows)

### Access Denied / WinError 5 when running `init --reset`

**Problem:** `tapps-agents init --reset` fails with `PermissionError: [WinError 5] Access is denied` on files in `.cursor/rules/` or `.claude/skills/`.

**Cause:** Cursor IDE, antivirus, or another process has files in those directories open or locked. On Windows, open files cannot be deleted or overwritten.

**Solution:**

1. **Close Cursor IDE** (or at least close all tabs under `.cursor` and `.claude`), then run from an **external terminal** (PowerShell or cmd outside Cursor):
   ```bash
   python -m tapps_agents.cli init --reset --yes
   ```

2. **Ensure no other process** (antivirus, backup, indexing) is locking `.cursor` or `.claude` before retrying.

3. **Retry:** The framework now uses safe remove with retries and, for skills, a rename-with-retry plus copy fallback. If a skill (e.g. architect) still fails with "Access is denied" on rename, it will be skipped; copy the skill manually from the backup (e.g. `.tapps-agents/backups/init-reset-<timestamp>/.claude/skills/architect` → `.claude/skills/architect`) or close Cursor and re-run `init --reset --yes`.

**Prevention:** Run `init --reset` from an external terminal rather than Cursor's integrated terminal when upgrading framework files.

## Unicode Encoding Errors on Windows

**Problem:** When running quality reports on Windows, you may encounter:
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

## Execution Progress Indicators

**Problem:** Workflows run but you don't see when they start or complete.

**Solution:** Execution indicators were added in version 2.0.6+. You should see:
- Clear start indicators when tasks begin
- Setup status messages
- Running indicators during execution
- Completion indicators when tasks finish

If indicators are not showing:
1. Ensure you're using version 2.0.6 or later
2. Check that output is not being redirected (indicators print to stderr)

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

**Problem:** During `init --reset` or any CLI command you get:
```
ValidationError: 1 validation error for ProjectConfig
scoring.weights
  Value error, Scoring weights must sum to 1.0, got 1.1
```

**Cause:** The framework requires **7** scoring weights that must sum to **1.0**. After an upgrade, an existing `scoring.weights` section may have 5 categories, wrong totals, or custom values that no longer sum to 1.0.

**Fix (choose one):**

1. **Replace with framework defaults** (recommended if you have no custom weights)

   In `.tapps-agents/config.yaml`, set `scoring.weights` to:

   ```yaml
   scoring:
     weights:
       complexity: 0.18
       security: 0.27
       maintainability: 0.24
       test_coverage: 0.13
       performance: 0.08
       structure: 0.05
       devex: 0.05
   ```
   These sum to 1.0.

2. **Keep custom weights but rebalance**

   If you use custom weights, ensure all **7** keys exist and the sum is 1.0. If your current sum is 1.1, divide each value by 1.1 (or scale down one or more values by 0.1 total). The 7 keys are: `complexity`, `security`, `maintainability`, `test_coverage`, `performance`, `structure`, `devex`.

3. **Workaround to run init when config is broken**

   Temporarily rename the config so init can run with defaults, then fix and restore:

   ```powershell
   # In the project that fails (e.g. HomeIQ)
   Rename-Item .tapps-agents\config.yaml .tapps-agents\config.yaml.bak
   python -m tapps_agents.cli init --reset --yes
   # Edit .tapps-agents\config.yaml.bak: fix scoring.weights, then replace config.yaml
   ```

### `tapps-agents` command not found (Windows / other project)

**Problem:** In a project that uses TappsCodingAgents (e.g. HomeIQ), `tapps-agents` is not recognized as a cmdlet or program.

**Cause:** The `tapps-agents` entry point is in the Python environment’s `Scripts` (or `bin`) directory. That path may not be on `PATH` when using a different project’s venv or terminal.

**Fix:** Run the CLI via the module. Ensure you are in the project root and using the environment where `tapps-agents` is installed:

```powershell
python -m tapps_agents.cli init --reset --yes
```

To have `tapps-agents` on `PATH`, add the `Scripts` directory of that environment to `PATH`, or use the venv’s `python` explicitly.

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

### Unknown command for auto-execution

**Symptoms**: Workflow execution fails with error:
```
Unknown command for auto-execution: <agent>/<action>
Available: [list of available commands]
```

**Cause**: The workflow preset uses an agent/action combination that isn't mapped in `COMMAND_MAPPING`. This typically happens when:
- A workflow preset uses a command that hasn't been added to the command mapping
- There's a mismatch between the action name in the workflow and the mapped command

**Solution**:
1. **Check if this is a known issue**: This error was fixed in version 3.2.2+ for:
   - `improver/refactor` (used in maintenance, quality, simple-improve-quality workflows)
   - `documenter/update_docstrings` (used in maintenance workflow)
2. **Upgrade to latest version**: Run `pip install --upgrade tapps-agents` to get the latest fixes
3. **If error persists with a different command**:
   - Check the workflow preset YAML file for the agent/action combination
   - Verify the command exists in the agent's implementation
   - File an issue with the workflow preset name and the exact error message
4. **Workaround**: Disable auto-execution for that step:
   ```yaml
   steps:
     - id: problematic-step
       agent: improver
       action: refactor
       # Add metadata to disable auto-execution
       metadata:
         auto_execute: false
   ```

**Affected Workflows** (fixed in 3.2.2+):
- `maintenance` (fix workflow) - uses `improver/refactor` and `documenter/update_docstrings`
- `quality` - uses `improver/refactor`
- `simple-improve-quality` - uses `improver/refactor`

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
