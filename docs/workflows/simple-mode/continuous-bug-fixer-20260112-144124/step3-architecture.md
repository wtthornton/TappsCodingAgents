# Step 3: Architecture Design - Continuous Bug Finder and Fixer

## System Overview

The Continuous Bug Finder and Fixer is a CLI command that orchestrates test execution, bug detection, automated fixing, and git commits in a continuous loop.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Command Entry Point                  │
│              (tapps-agents continuous-bug-fix)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ContinuousBugFixer (Orchestrator)              │
│  - Main loop coordination                                   │
│  - Progress reporting                                       │
│  - Summary generation                                       │
└───────┬───────────────────────────────────┬─────────────────┘
        │                                   │
        ▼                                   ▼
┌───────────────────┐           ┌──────────────────────────┐
│   BugFinder       │           │   BugFixCoordinator      │
│  - Run pytest     │           │  - Call FixOrchestrator  │
│  - Parse failures │           │  - Handle results        │
│  - Extract bugs   │           │  - Verify fixes          │
└─────────┬─────────┘           └──────────┬───────────────┘
          │                                │
          │                                ▼
          │                    ┌──────────────────────────┐
          │                    │   FixOrchestrator        │
          │                    │   (Existing Component)   │
          │                    │  - Debug → Fix → Test    │
          │                    │  - Review → Commit       │
          │                    └──────────────────────────┘
          │
          ▼
┌───────────────────┐
│  CommitManager    │
│  - Commit fixes   │
│  - Create messages│
│  - Handle git ops │
└───────────────────┘
```

## Component Design

### 1. ContinuousBugFixer (Main Orchestrator)

**Location:** `tapps_agents/cli/commands/continuous_bug_fix.py`

**Responsibilities:**
- Coordinate the main execution loop
- Manage iteration limits and stop conditions
- Aggregate results and generate summary reports
- Handle user interruption (Ctrl+C)
- Progress reporting

**Key Methods:**
```python
async def execute(
    test_path: str | None = None,
    max_iterations: int = 10,
    commit_strategy: str = "one-per-bug",
    auto_commit: bool = True,
) -> dict[str, Any]:
    """Main execution method"""
    
async def _run_iteration(iteration: int) -> dict[str, Any]:
    """Execute one iteration of bug finding and fixing"""
    
def _generate_summary(results: list[dict]) -> dict[str, Any]:
    """Generate final summary report"""
```

**Dependencies:**
- BugFinder (bug detection)
- BugFixCoordinator (bug fixing coordination)
- CommitManager (git operations)

---

### 2. BugFinder (Test Execution & Parsing)

**Location:** `tapps_agents/continuous_bug_fix/bug_finder.py`

**Responsibilities:**
- Execute pytest programmatically
- Parse pytest output to extract test failures
- Identify source files (not test files) that need fixing
- Extract error messages and descriptions
- Filter out test setup/configuration errors

**Key Methods:**
```python
async def find_bugs(
    test_path: str | None = None,
    project_root: Path | None = None,
) -> list[BugInfo]:
    """Run tests and return list of bugs found"""
    
async def _run_pytest(test_path: str | None) -> dict[str, Any]:
    """Execute pytest and capture output"""
    
def _parse_pytest_output(
    output: str,
    project_root: Path,
) -> list[BugInfo]:
    """Parse pytest output to extract bug information"""
```

**Data Structure:**
```python
@dataclass
class BugInfo:
    file_path: str          # Source file with bug
    error_message: str      # Error description
    test_name: str          # Test that failed
    test_file: str          # Test file path
    line_number: int | None # Line number if available
```

**Integration:**
- Reuses `TesterAgent._run_pytest()` pattern for test execution
- Uses subprocess to run pytest with JSON output (pytest-json-report plugin) or parse text output
- Filters bugs: only source files (exclude test files, config files)

---

### 3. BugFixCoordinator (Bug Fixing Coordination)

**Location:** `tapps_agents/continuous_bug_fix/bug_fix_coordinator.py`

**Responsibilities:**
- Call FixOrchestrator for each bug
- Handle async execution
- Verify fixes by re-running tests
- Track fix results

**Key Methods:**
```python
async def fix_bug(
    bug: BugInfo,
    config: ProjectConfig | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Fix a single bug using FixOrchestrator"""
    
async def verify_fix(
    bug: BugInfo,
    test_path: str | None = None,
) -> bool:
    """Re-run tests to verify bug is fixed"""
```

**Integration:**
- Uses `FixOrchestrator.execute()` from `tapps_agents.simple_mode.orchestrators.fix_orchestrator`
- Passes file path and error message to FixOrchestrator
- Handles FixOrchestrator results (success/failure, commit info)

---

### 4. CommitManager (Git Operations)

**Location:** `tapps_agents/continuous_bug_fix/commit_manager.py`

**Responsibilities:**
- Commit fixes after bug-fix-agent succeeds
- Create meaningful commit messages
- Handle batch commits (if commit_strategy is "batch")
- Validate git repository

**Key Methods:**
```python
async def commit_fix(
    bug: BugInfo,
    commit_message: str | None = None,
) -> dict[str, Any]:
    """Commit a single fix"""
    
async def commit_batch(
    bugs: list[BugInfo],
    commit_message: str | None = None,
) -> dict[str, Any]:
    """Commit multiple fixes in one commit"""
```

**Integration:**
- Uses `commit_changes()` from `tapps_agents.core.git_operations`
- Validates git repository before committing
- Creates commit messages: "Fix: [error description] (from [test_name])"

---

## Data Flow

### Main Execution Flow

```
1. CLI Command Invoked
   ↓
2. ContinuousBugFixer.execute()
   ↓
3. Loop (max_iterations):
   a. BugFinder.find_bugs()
      - Run pytest
      - Parse failures
      - Return list of BugInfo
   ↓
   b. For each bug:
      - BugFixCoordinator.fix_bug()
        - Call FixOrchestrator.execute()
        - Wait for fix completion
        - Return result
      ↓
      - If fix successful:
        - CommitManager.commit_fix()
        - Verify fix (re-run test)
      ↓
      - If fix failed:
        - Log failure
        - Continue to next bug
   ↓
   c. Check stop conditions:
      - No bugs found → Stop
      - Max iterations reached → Stop
      - Manual interruption → Stop
   ↓
4. Generate Summary Report
   - Total bugs found
   - Bugs fixed
   - Bugs failed
   - Iterations run
```

## Integration Points

### 1. Test Execution
- **Pattern:** Reuse `TesterAgent._run_pytest()` approach
- **Method:** Use subprocess to run pytest
- **Output Format:** Parse pytest text output or use pytest-json-report plugin
- **Location:** `tapps_agents/agents/tester/agent.py` (reference implementation)

### 2. Bug Fixing
- **Component:** `FixOrchestrator` (existing)
- **Location:** `tapps_agents/simple_mode/orchestrators/fix_orchestrator.py`
- **Method:** `execute(intent, parameters)`
- **Parameters:**
  ```python
  {
      "files": [bug.file_path],
      "error_message": bug.error_message,
      "auto_commit": False,  # We handle commits separately
  }
  ```

### 3. Git Operations
- **Module:** `tapps_agents.core.git_operations`
- **Functions:** `commit_changes()`, `get_current_branch()`, etc.
- **Location:** `tapps_agents/core/git_operations.py`

### 4. Configuration
- **Pattern:** Follow existing config structure
- **Location:** `.tapps-agents/config.yaml`
- **Section:** `continuous_bug_fix:`
  ```yaml
  continuous_bug_fix:
    max_iterations: 10
    commit_strategy: "one-per-bug"  # or "batch"
    auto_commit: true
    test_path: "tests/"
  ```

## Error Handling Strategy

### Test Execution Errors
- Handle pytest not found / execution failures
- Log error and continue (return empty bug list)
- Don't crash on test execution errors

### Bug Fix Errors
- If FixOrchestrator fails → log and continue to next bug
- Track failures in results
- Include in summary report

### Git Operation Errors
- Validate git repository before committing
- Handle uncommitted changes (warn or skip)
- Log git errors but continue execution

### Edge Cases
- No tests in project → return empty bug list, stop
- All tests passing → return empty bug list, stop
- Test failures in test files → filter out (only fix source files)
- Max iterations reached → stop and report

## Performance Considerations

1. **Test Execution**
   - Use pytest parallel execution if available (`-n auto`)
   - Cache test results when possible
   - Minimize redundant test runs

2. **Bug Fixing**
   - Fix bugs sequentially (one at a time)
   - FixOrchestrator already handles async execution internally
   - Don't parallelize fixes (avoid conflicts)

3. **Progress Reporting**
   - Show progress after each iteration
   - Don't block on progress updates
   - Use async-friendly logging

## Security Considerations

1. **Git Operations**
   - Never force push
   - Validate branch before committing
   - Respect git hooks

2. **Test Execution**
   - Run tests in isolated environment (if possible)
   - Don't execute untrusted code

3. **Bug Fix Agent**
   - FixOrchestrator already has security scans (pre-commit)
   - Respect quality thresholds

## Testing Strategy

1. **Unit Tests**
   - BugFinder: Mock pytest output, test parsing logic
   - BugFixCoordinator: Mock FixOrchestrator, test coordination
   - CommitManager: Mock git operations, test commit logic

2. **Integration Tests**
   - Test with real pytest execution (small test suite)
   - Test with mock test failures
   - Test full flow with mock FixOrchestrator

3. **E2E Tests**
   - Test with real test suite (controlled failures)
   - Test full cycle: find → fix → commit
   - Test error handling and edge cases

## Deployment Considerations

1. **CLI Integration**
   - Add command to `tapps_agents/cli/main.py`
   - Add parser to `tapps_agents/cli/parsers/top_level.py`
   - Add command handler to `tapps_agents/cli/commands/continuous_bug_fix.py`

2. **Dependencies**
   - No new external dependencies (reuse existing)
   - pytest-json-report plugin optional (fallback to text parsing)

3. **Configuration**
   - Add config schema to `tapps_agents/core/config.py`
   - Default values for all settings
