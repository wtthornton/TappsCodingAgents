# Overnight Bug Fixing with Proactive Discovery

## Overview

TappsCodingAgents now supports automated overnight bug fixing with two discovery modes:

1. **Test-based discovery** (default): Runs tests and fixes failures
2. **Proactive discovery** (new): Analyzes code to find potential bugs without requiring test failures

Both modes automatically fix bugs and commit to the main branch, perfect for overnight execution.

## Usage

### Proactive Bug Discovery (Recommended for Overnight)

Find and fix bugs by analyzing code without requiring tests:

```bash
# Find and fix 20 bugs from codebase analysis
tapps-agents continuous-bug-fix --proactive --target-path src/ --max-bugs 20 --max-iterations 10

# Analyze specific directory
tapps-agents continuous-bug-fix --proactive --target-path tapps_agents/cli/ --max-bugs 15

# Overnight execution with batch commits
tapps-agents continuous-bug-fix --proactive --max-iterations 20 --commit-strategy batch
```

### Test-based Discovery (Existing)

Run tests and fix failures:

```bash
# Run tests and fix failures
tapps-agents continuous-bug-fix --test-path tests/ --max-iterations 10

# Analyze specific test file
tapps-agents continuous-bug-fix --test-path tests/test_api.py
```

## Command Options

### Proactive Mode Options

- `--proactive`: Enable proactive bug discovery (code analysis)
- `--target-path <path>`: Directory or file to analyze (default: project root)
- `--max-bugs <n>`: Maximum bugs to find per iteration (default: 20)

### Common Options

- `--test-path <path>`: Test directory/file (for test-based mode)
- `--max-iterations <n>`: Maximum loop iterations (default: 10)
- `--commit-strategy <strategy>`: `one-per-bug` (default) or `batch`
- `--no-commit`: Skip commits (dry-run mode)
- `--format <format>`: Output format (`json` or `text`)

## How It Works

### Proactive Discovery Mode

1. **Code Analysis**: Uses `ReviewerAgent` to analyze source files
2. **Bug Detection**: Identifies security vulnerabilities, code issues, and potential bugs
3. **Bug Fixing**: Uses `FixOrchestrator` (bug-fix-agent) to fix each bug
4. **Quality Gates**: Ensures fixes meet quality thresholds (≥70 overall, ≥6.5 security)
5. **Auto-commit**: Commits fixes to main branch automatically
6. **Iteration**: Repeats until no bugs found or max iterations reached

### Test-based Discovery Mode

1. **Run Tests**: Executes pytest on specified test path
2. **Parse Failures**: Extracts bug information from test failures
3. **Bug Fixing**: Uses `FixOrchestrator` to fix each bug
4. **Verify**: Re-runs tests to verify fixes
5. **Auto-commit**: Commits fixes to main branch
6. **Iteration**: Repeats until all tests pass or max iterations reached

## Overnight Execution

Perfect for running while you sleep:

```bash
# Start overnight execution
tapps-agents continuous-bug-fix --proactive --max-iterations 20 --max-bugs 20

# With batch commits (faster, fewer git operations)
tapps-agents continuous-bug-fix --proactive --max-iterations 20 --commit-strategy batch

# Analyze specific module
tapps-agents continuous-bug-fix --proactive --target-path tapps_agents/simple_mode/ --max-iterations 15
```

## Safety Features

- **Quality Gates**: Only commits fixes that pass quality thresholds
- **Max Iterations**: Prevents infinite loops (default: 10)
- **Graceful Shutdown**: Handles Ctrl+C interruption cleanly
- **Error Handling**: Continues with next bug if one fix fails
- **Dry Run**: Use `--no-commit` to test without committing

## Output

Results include:
- Total bugs found
- Bugs fixed successfully
- Bugs that failed to fix
- Iteration-by-iteration breakdown
- Fix rate statistics

Example output:
```
Continuous Bug Fix Results
================================================================================

Iterations Run: 3
Bugs Found: 12
Bugs Fixed: 10
Bugs Failed: 2
Bugs Skipped: 0

Summary:
  Fix Rate: 83.3%
  Total Bugs Found: 12
  Total Bugs Fixed: 10
  Total Bugs Failed: 2

✅ Continuous bug fix completed successfully
```

## Configuration

Configure defaults in `.tapps-agents/config.yaml`:

```yaml
continuous_bug_fix:
  max_iterations: 10
  commit_strategy: "one-per-bug"  # or "batch"
  auto_commit: true
  test_path: "tests/"  # For test-based mode
  # Proactive mode uses project root by default
```

## Integration

The proactive bug discovery integrates seamlessly with existing infrastructure:

- Uses `BugInfo` objects compatible with `BugFixCoordinator`
- Works with existing `FixOrchestrator` (bug-fix-agent)
- Supports all commit strategies
- Compatible with quality gates and thresholds

## Best Practices

1. **Start Small**: Use `--max-bugs 10` for initial runs
2. **Targeted Analysis**: Use `--target-path` to focus on specific modules
3. **Batch Commits**: Use `--commit-strategy batch` for faster execution
4. **Dry Run First**: Test with `--no-commit` before overnight execution
5. **Monitor Results**: Check output to understand what was fixed
