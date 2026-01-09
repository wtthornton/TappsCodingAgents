# Workflow UX Improvements Implementation

**Date:** January 9, 2026  
**Issue Source:** User feedback on workflow usability

## Summary

This implementation addresses 6 critical UX issues identified in user feedback that were causing workflow failures and frustration.

## Issues Addressed

### 1. CLI/Cursor Mode Confusion (P1 - High)

**Problem:** Users were confused about which execution mode was being used, leading to unexpected behavior.

**Solution:** Added explicit `--cli-mode` and `--cursor-mode` flags to workflow commands.

```bash
# Force CLI/headless mode
tapps-agents workflow rapid --cli-mode --prompt "Add feature"

# Force Cursor mode (Skills)
tapps-agents workflow rapid --cursor-mode --prompt "Add feature"
```

**Files Changed:**
- `tapps_agents/cli/parsers/top_level.py` - Added new CLI arguments

### 2. No Pre-flight Checks (P2 - Medium)

**Problem:** Users wasted time running workflows that would fail due to missing files or configuration issues.

**Solution:** Added `--dry-run` flag that validates workflow without executing.

```bash
# Validate before running
tapps-agents workflow rapid --dry-run --prompt "Add feature"
```

**Output includes:**
- Runtime mode configuration
- Input validation (target file, prompt)
- Artifact path detection (warns about existing artifacts)
- Workflow steps preview
- Environment health check

**Files Changed:**
- `tapps_agents/cli/parsers/top_level.py` - Added `--dry-run` flag
- `tapps_agents/cli/commands/top_level.py` - Added `_handle_workflow_dry_run()` function

### 3. Poor Error Messages (P1 - High)

**Problem:** Error messages were generic and didn't tell users how to proceed.

**Solution:** Enhanced `ErrorEnvelope` with actionable next steps based on error type.

**Before:**
```
Error: File not found
```

**After:**
```
[ERROR] File src/auth.py not found

[RECOVERABLE] This error may be recoverable.

[NEXT STEPS]
   1. Check if the file exists: ls -la <path>
   2. Run with different target: tapps-agents workflow <preset> --file <correct_path>
   3. Resume from this step: tapps-agents workflow resume --continue-from implement

[HINT] Review the input parameters and ensure they meet the required format.

[REFERENCE]
   workflow_id: wf-abc123
   step_id: implement
   state_dir: .tapps-agents/workflow-state/
```

**Files Changed:**
- `tapps_agents/core/error_envelope.py` - Added `_get_actionable_next_steps()` method

### 4. Hidden Workflow State (P2 - Medium)

**Problem:** Users couldn't find where workflow outputs were saved.

**Solution:** Print artifact paths after each step completes.

```
[OK] Step 'enhance' completed (3.2s)
   📄 Artifacts created:
      - docs/workflows/simple-mode/step1-enhanced-prompt.md
   📁 State: .tapps-agents/workflow-state/wf-abc123
```

**Files Changed:**
- `tapps_agents/workflow/executor.py` - Added `_print_step_artifacts()` method
- `tapps_agents/workflow/cursor_executor.py` - Added `_print_step_artifacts()` method
- `tapps_agents/cli/parsers/top_level.py` - Added `--print-paths` / `--no-print-paths` flags

### 5. Configurable Artifact Paths (P0 - Critical)

**Problem:** Rigid hardcoded artifact paths blocked workflows when paths didn't match expectations.

**Solution:** Added `WorkflowArtifactConfig` for configurable artifact paths.

```yaml
# .tapps-agents/config.yaml
workflow:
  artifacts:
    base_dir: "docs/workflows"
    simple_mode_subdir: "simple-mode"
    auto_detect_existing: true
    naming_pattern: "{workflow_id}/{step_name}.md"
    print_paths_on_completion: true
```

**Files Changed:**
- `tapps_agents/core/config.py` - Added `WorkflowArtifactConfig` class

### 6. All-or-Nothing Execution (P0 - Critical)

**Problem:** Workflow failures lost all progress; no way to resume from a specific step.

**Solution:** Added `--continue-from` and `--skip-steps` flags.

```bash
# Resume from a specific step
tapps-agents workflow rapid --continue-from implement --prompt "Add feature"

# Skip steps that were already completed
tapps-agents workflow rapid --skip-steps "enhance,plan" --prompt "Add feature"
```

**Files Changed:**
- `tapps_agents/cli/parsers/top_level.py` - Added `--continue-from` and `--skip-steps` flags
- `tapps_agents/workflow/executor.py` - Added `continue_from` and `skip_steps` attributes
- `tapps_agents/workflow/cursor_executor.py` - Added `continue_from` and `skip_steps` attributes

## New CLI Flags Summary

| Flag | Description |
|------|-------------|
| `--cli-mode` | Force CLI/headless mode |
| `--cursor-mode` | Force Cursor mode (Skills) |
| `--dry-run` | Validate without executing |
| `--continue-from STEP` | Resume from specific step |
| `--skip-steps STEPS` | Skip comma-separated steps |
| `--print-paths` | Print artifact paths (default: True) |
| `--no-print-paths` | Disable artifact path printing |

## Configuration Changes

New `workflow.artifacts` section in `.tapps-agents/config.yaml`:

```yaml
workflow:
  artifacts:
    base_dir: "docs/workflows"
    simple_mode_subdir: "simple-mode"
    auto_detect_existing: true
    naming_pattern: "{workflow_id}/{step_name}.md"
    print_paths_on_completion: true
  graceful_partial_completion: true
  pre_flight_validation: true
```

## Files Modified Summary

**Core Implementation:**
- `tapps_agents/cli/parsers/top_level.py` - Added new CLI arguments
- `tapps_agents/cli/commands/top_level.py` - Added dry-run handler and mode processing
- `tapps_agents/core/config.py` - Added `WorkflowArtifactConfig` class
- `tapps_agents/core/error_envelope.py` - Enhanced with actionable next steps
- `tapps_agents/workflow/executor.py` - Added artifact printing and new attributes
- `tapps_agents/workflow/cursor_executor.py` - Added artifact printing and new attributes

**Documentation (installed by `init`):**
- `tapps_agents/resources/cursor/rules/command-reference.mdc` - Updated workflow flags
- `tapps_agents/resources/cursor/rules/quick-reference.mdc` - Added workflow execution flags

**Installed Files (current project):**
- `.cursor/rules/command-reference.mdc` - Updated workflow flags
- `.cursor/rules/quick-reference.mdc` - Added workflow execution flags

## Testing

All changes verified:
1. ✅ Imports successful
2. ✅ CLI help shows new flags
3. ✅ Dry-run functionality works
4. ✅ Error messages show actionable steps
5. ✅ Windows compatibility (ASCII-safe output)
6. ✅ Documentation files updated (init resources)

## Usage Examples

### Pre-flight Validation
```bash
tapps-agents workflow rapid --dry-run --prompt "Add user authentication"
```

### Resume Failed Workflow
```bash
# List available steps
tapps-agents workflow state list

# Resume from implement step
tapps-agents workflow rapid --continue-from implement --prompt "Add user authentication"
```

### Skip Already-Done Steps
```bash
tapps-agents workflow rapid --skip-steps "enhance,plan" --prompt "Add user authentication"
```

### Force CLI Mode for CI/CD
```bash
tapps-agents workflow rapid --cli-mode --auto --prompt "Add user authentication"
```

## What Users Should Do Now

1. **First:** Run `tapps-agents doctor --full` to verify environment
2. **Second:** Use `--dry-run` before running workflows to catch issues early
3. **Third:** Use `--continue-from` when workflows fail to resume from last good step
4. **Fourth:** Use individual agent commands when workflow blocks:
   ```bash
   tapps-agents enhancer enhance "..."
   tapps-agents planner plan "..."
   tapps-agents implementer implement "..." file.tsx
   tapps-agents reviewer review file.tsx
   ```
