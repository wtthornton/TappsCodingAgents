# Step 4: Component Design Specifications

## API Specifications and Data Models

This document provides detailed specifications for all components, including method signatures, data models, error handling, and design contracts.

---

## 1. WorktreeManager Enhancement

### File: `tapps_agents/workflow/worktree_manager.py`

### Method: `_delete_branch()`

**Purpose:** Delete a Git branch safely (attempts safe delete first, then force delete if needed).

**Signature:**
```python
def _delete_branch(self, branch_name: str) -> bool:
    """
    Delete a Git branch (safe delete with force fallback).
    
    Args:
        branch_name: Name of the branch to delete (e.g., "workflow/...")
    
    Returns:
        True if branch was deleted or didn't exist, False on error
    
    Raises:
        None (all errors are caught and logged)
    """
```

**Algorithm:**
1. Verify branch exists using `git rev-parse --verify <branch>`
2. If branch doesn't exist, return True (success - nothing to delete)
3. Attempt safe delete: `git branch -d <branch>`
4. If safe delete fails (branch not merged), attempt force delete: `git branch -D <branch>`
5. Log all operations (info for success, warning for failures)
6. Return True on success, False on error

**Error Handling:**
- Catch `subprocess.CalledProcessError` for git command failures
- Log warnings but don't raise exceptions
- Return False only if both safe and force delete fail

**Usage Example:**
```python
manager = WorktreeManager(project_root)
success = manager._delete_branch("workflow/my-workflow-step")
if not success:
    logger.warning("Failed to delete branch, but continuing...")
```

---

### Method: `remove_worktree()` (Enhanced)

**Current Signature:**
```python
async def remove_worktree(self, worktree_name: str) -> None:
```

**Enhanced Behavior:**
1. Remove worktree directory (existing behavior)
2. **NEW:** Get branch name using `_branch_for(worktree_name)`
3. **NEW:** Check configuration for `delete_branches_on_cleanup` flag
4. **NEW:** If enabled, call `_delete_branch(branch_name)`
5. Log cleanup results

**Configuration Check:**
```python
# Load config (with defaults)
config = load_config()
should_delete = (
    config.workflow.branch_cleanup.delete_branches_on_cleanup
    if config.workflow.branch_cleanup.enabled
    else False
)
```

**Backward Compatibility:**
- Default behavior: If configuration not present, don't delete branches
- Existing callers unaffected (returns None, doesn't raise)
- Graceful degradation on errors

---

## 2. BranchCleanupService

### File: `tapps_agents/workflow/branch_cleanup.py` (NEW)

### Class Definition

```python
class BranchCleanupService:
    """
    Service for detecting and cleaning up orphaned Git branches.
    
    Detects branches that no longer have associated worktrees and provides
    cleanup functionality based on retention policies.
    """
    
    def __init__(
        self,
        project_root: Path,
        config: BranchCleanupConfig | None = None
    ):
        """
        Initialize branch cleanup service.
        
        Args:
            project_root: Root directory of the project
            config: Branch cleanup configuration (uses defaults if None)
        """
```

### Method: `detect_orphaned_branches()`

**Signature:**
```python
async def detect_orphaned_branches(
    self,
    pattern: str = "workflow/*",
    retention_days: int | None = None
) -> list[OrphanedBranch]:
    """
    Detect branches that no longer have associated worktrees.
    
    Args:
        pattern: Branch name pattern to match (default: "workflow/*")
        retention_days: Only return branches older than N days (None = no age filter)
    
    Returns:
        List of orphaned branch information, sorted by age (oldest first)
    
    Raises:
        RuntimeError: If git command execution fails critically
    """
```

**Algorithm:**
1. Get branch list matching pattern: `git branch -a | grep <pattern>`
2. For each branch:
   - Extract branch name (remove remote prefix if present)
   - Get branch metadata (last commit date, message)
   - Check if worktree exists: `_worktree_exists_for_branch()`
   - Calculate age in days
   - If `retention_days` specified, filter by age
3. Return list of `OrphanedBranch` objects, sorted by age (oldest first)

**Performance:**
- Batch git operations where possible
- Cache worktree list to avoid repeated queries
- Early exit for branches that don't match pattern

---

### Method: `cleanup_orphaned_branches()`

**Signature:**
```python
async def cleanup_orphaned_branches(
    self,
    pattern: str = "workflow/*",
    retention_days: int | None = None,
    dry_run: bool = False,
    keep_active: bool = True
) -> CleanupReport:
    """
    Clean up orphaned branches based on retention policies.
    
    Args:
        pattern: Branch name pattern to match (default: "workflow/*")
        retention_days: Only delete branches older than N days (None = use config default)
        dry_run: If True, preview what would be deleted without actually deleting
        keep_active: If True, preserve branches with uncommitted changes
    
    Returns:
        CleanupReport with detailed results
    
    Raises:
        None (all errors are logged in report)
    """
```

**Algorithm:**
1. Detect orphaned branches using `detect_orphaned_branches()`
2. If `dry_run`, return report with preview only
3. For each orphaned branch:
   - If `keep_active`, check for uncommitted changes
   - Skip branch if it has uncommitted changes
   - Attempt branch deletion: `git branch -D <branch>`
   - Track result (deleted, skipped, failed)
4. Generate and return `CleanupReport`

**Safety Checks:**
- Only delete branches matching safe patterns
- Never delete branches outside `workflow/*` or `agent/*` patterns
- Verify branch name format before deletion
- Log all deletion attempts

---

### Helper Methods

#### `_get_branch_list()`

```python
def _get_branch_list(self, pattern: str) -> list[str]:
    """
    Get all branches matching the specified pattern.
    
    Args:
        pattern: Branch name pattern (e.g., "workflow/*")
    
    Returns:
        List of branch names (local and remote)
    """
```

**Implementation:**
- Execute: `git branch -a`
- Filter by pattern using regex or fnmatch
- Normalize branch names (remove `remotes/origin/` prefix)
- Return sorted list

#### `_get_branch_metadata()`

```python
def _get_branch_metadata(self, branch_name: str) -> BranchMetadata:
    """
    Extract metadata for a branch.
    
    Args:
        branch_name: Name of the branch
    
    Returns:
        BranchMetadata with commit date, message, etc.
    """
```

**Implementation:**
- Execute: `git log -1 --format=%ct|%s <branch>`
- Parse timestamp and commit message
- Calculate age in days
- Return `BranchMetadata` object

#### `_worktree_exists_for_branch()`

```python
def _worktree_exists_for_branch(self, branch_name: str) -> bool:
    """
    Check if a worktree exists for the given branch.
    
    Args:
        branch_name: Name of the branch
    
    Returns:
        True if worktree exists, False otherwise
    """
```

**Implementation:**
- Extract worktree name from branch name (remove `workflow/` prefix)
- Check if directory exists: `.tapps-agents/worktrees/<worktree_name>`
- Verify it's a valid worktree (check for `.git` or git metadata)
- Return boolean

---

## 3. Data Models

### OrphanedBranch

```python
@dataclass
class OrphanedBranch:
    """Information about an orphaned branch."""
    name: str
    pattern: str
    age_days: float
    last_commit_date: datetime
    last_commit_message: str
    worktree_exists: bool
    
    def __post_init__(self):
        """Validate branch information."""
        if not self.name:
            raise ValueError("Branch name cannot be empty")
        if self.age_days < 0:
            raise ValueError("Age cannot be negative")
```

**Fields:**
- `name`: Full branch name (e.g., "workflow/my-workflow-step")
- `pattern`: Pattern that matched this branch
- `age_days`: Age in days (float for precision)
- `last_commit_date`: Datetime of last commit
- `last_commit_message`: First line of last commit message
- `worktree_exists`: Boolean (should always be False for orphaned branches)

---

### BranchMetadata

```python
@dataclass
class BranchMetadata:
    """Metadata for a Git branch."""
    last_commit_date: datetime
    last_commit_message: str
    commit_hash: str
    
    @property
    def age_days(self) -> float:
        """Calculate age in days."""
        delta = datetime.now() - self.last_commit_date
        return delta.total_seconds() / 86400.0
```

**Fields:**
- `last_commit_date`: Datetime of last commit
- `last_commit_message`: First line of commit message
- `commit_hash`: Full commit hash

---

### CleanupReport

```python
@dataclass
class CleanupReport:
    """Results of branch cleanup operation."""
    branches_deleted: int
    branches_skipped: int
    branches_failed: int
    deleted_branches: list[str]
    skipped_branches: list[str]
    failed_branches: list[tuple[str, str]]  # (branch_name, error_message)
    dry_run: bool
    execution_time_seconds: float
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "branches_deleted": self.branches_deleted,
            "branches_skipped": self.branches_skipped,
            "branches_failed": self.branches_failed,
            "deleted_branches": self.deleted_branches,
            "skipped_branches": self.skipped_branches,
            "failed_branches": [
                {"branch": b[0], "error": b[1]}
                for b in self.failed_branches
            ],
            "dry_run": self.dry_run,
            "execution_time_seconds": self.execution_time_seconds,
        }
    
    def __str__(self) -> str:
        """Human-readable summary."""
        status = "DRY RUN" if self.dry_run else "COMPLETED"
        return (
            f"Cleanup {status}: "
            f"{self.branches_deleted} deleted, "
            f"{self.branches_skipped} skipped, "
            f"{self.branches_failed} failed"
        )
```

**Fields:**
- `branches_deleted`: Count of successfully deleted branches
- `branches_skipped`: Count of skipped branches (with uncommitted changes, etc.)
- `branches_failed`: Count of failed deletions
- `deleted_branches`: List of branch names that were deleted
- `skipped_branches`: List of branch names that were skipped (with reasons)
- `failed_branches`: List of tuples (branch_name, error_message) for failures
- `dry_run`: Boolean indicating if this was a dry-run
- `execution_time_seconds`: Time taken for cleanup operation

---

## 4. Configuration Models

### BranchCleanupConfig

```python
@dataclass
class BranchCleanupConfig:
    """Configuration for branch cleanup behavior."""
    enabled: bool = True
    delete_branches_on_cleanup: bool = True
    retention_days: int = 7
    auto_cleanup_on_completion: bool = True
    patterns: dict[str, str] = field(default_factory=lambda: {
        "workflow": "workflow/*",
        "agent": "agent/*"
    })
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BranchCleanupConfig:
        """Create from dictionary (configuration file)."""
        return cls(
            enabled=data.get("enabled", True),
            delete_branches_on_cleanup=data.get("delete_branches_on_cleanup", True),
            retention_days=data.get("retention_days", 7),
            auto_cleanup_on_completion=data.get("auto_cleanup_on_completion", True),
            patterns=data.get("patterns", {
                "workflow": "workflow/*",
                "agent": "agent/*"
            })
        )
    
    def validate(self) -> None:
        """Validate configuration values."""
        if self.retention_days < 0:
            raise ValueError("retention_days must be non-negative")
        if not isinstance(self.patterns, dict):
            raise ValueError("patterns must be a dictionary")
```

**Configuration File Format (YAML):**
```yaml
workflow:
  branch_cleanup:
    enabled: true
    delete_branches_on_cleanup: true
    retention_days: 7
    auto_cleanup_on_completion: true
    patterns:
      workflow: "workflow/*"
      agent: "agent/*"
```

---

## 5. CLI Command Specification

### Command: `cleanup-branches`

**File:** `tapps_agents/cli/workflow_commands.py`

**Function Signature:**
```python
@workflow_command("cleanup-branches")
async def cleanup_branches_command(
    ctx: Context,
    dry_run: bool = False,
    retention_days: int | None = None,
    pattern: str | None = None,
    force: bool = False
) -> None:
    """
    Clean up orphaned workflow branches.
    
    Args:
        ctx: Click context
        dry_run: Preview what would be deleted without actually deleting
        retention_days: Override retention period (default: from config)
        pattern: Branch pattern to match (default: all configured patterns)
        force: Skip confirmation prompts
    """
```

**Command-Line Interface:**
```bash
tapps-agents workflow cleanup-branches [OPTIONS]

Options:
  --dry-run              Preview what would be deleted
  --retention-days INT   Override retention period (days)
  --pattern TEXT         Branch pattern to match (e.g., "workflow/*")
  --force                Skip confirmation prompts
  --help                 Show this message and exit
```

**Behavior:**
1. Load configuration from `.tapps-agents/config.yaml`
2. Initialize `BranchCleanupService` with configuration
3. Detect orphaned branches (using pattern and retention_days if provided)
4. Display preview of branches that would be deleted
5. If `--dry-run`, show preview and exit
6. If not `--force`, prompt user for confirmation
7. Execute cleanup operation
8. Display results summary

**Output Format:**
```
Branch Cleanup Preview
======================

Found 3 orphaned branches:
  - workflow/my-workflow-1 (age: 10 days)
  - workflow/my-workflow-2 (age: 8 days)
  - workflow/my-workflow-3 (age: 5 days)

Would delete 2 branches (older than 7 days):
  - workflow/my-workflow-1
  - workflow/my-workflow-2

Proceed with cleanup? [y/N]: y

Cleanup COMPLETED: 2 deleted, 0 skipped, 0 failed
Execution time: 0.5 seconds
```

---

## 6. Error Handling Specifications

### Error Types

#### GitCommandError
```python
class GitCommandError(Exception):
    """Raised when git command execution fails."""
    def __init__(self, command: str, returncode: int, stderr: str):
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"Git command failed: {command}")
```

**Handling Strategy:**
- Log error with context
- Return False/None instead of raising (where appropriate)
- Include error in CleanupReport for failed operations

#### ConfigurationError
```python
class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    def __init__(self, message: str, config_path: Path | None = None):
        self.config_path = config_path
        super().__init__(f"Configuration error: {message}")
```

**Handling Strategy:**
- Validate configuration on load
- Use sensible defaults if validation fails
- Log warning and continue with defaults

### Error Recovery

1. **Non-existent Branch:**
   - Treat as success (nothing to delete)
   - Log debug message
   - Continue operation

2. **Git Command Failure:**
   - Log warning with error details
   - Include in CleanupReport.failed_branches
   - Continue with next branch

3. **Configuration Missing:**
   - Use default configuration
   - Log info message
   - Continue operation

---

## 7. Logging Specifications

### Log Levels

- **DEBUG:** Detailed branch information, git command execution
- **INFO:** Cleanup operations, successful deletions, summary statistics
- **WARNING:** Failed deletions, configuration issues, non-critical errors
- **ERROR:** Critical failures, git command errors that prevent operation

### Log Format

```python
logger.info(
    f"Deleted branch: {branch_name}",
    extra={
        "branch": branch_name,
        "pattern": pattern,
        "age_days": age_days
    }
)
```

### Audit Trail

All branch deletions are logged with:
- Timestamp
- Branch name
- Pattern matched
- Age in days
- Success/failure status
- Error message (if failed)

---

## 8. Testing Contracts

### Unit Test Specifications

#### `_delete_branch()` Tests
- ✅ Delete existing branch (success)
- ✅ Delete non-existent branch (success - no error)
- ✅ Safe delete fails, force delete succeeds
- ✅ Both safe and force delete fail (returns False)
- ✅ Branch name validation
- ✅ Error logging verification

#### `detect_orphaned_branches()` Tests
- ✅ Detect orphaned branches correctly
- ✅ Filter by pattern
- ✅ Filter by retention_days
- ✅ Sort by age (oldest first)
- ✅ Handle git command errors gracefully
- ✅ Return empty list when no orphaned branches

#### `cleanup_orphaned_branches()` Tests
- ✅ Dry-run mode (no actual deletion)
- ✅ Delete orphaned branches older than retention period
- ✅ Skip branches with uncommitted changes (keep_active=True)
- ✅ Generate accurate CleanupReport
- ✅ Handle partial failures gracefully
- ✅ Confirmation prompt (when not force)

### Integration Test Specifications

- ✅ End-to-end workflow execution with branch cleanup
- ✅ CLI command execution with various options
- ✅ Configuration loading and validation
- ✅ Error recovery and logging
- ✅ Windows path handling
- ✅ Large number of branches (performance)

---

## 9. Performance Requirements

### Response Time Targets

- `_delete_branch()`: < 1 second per branch
- `detect_orphaned_branches()`: < 5 seconds for 100 branches
- `cleanup_orphaned_branches()`: < 10 seconds for 50 branches

### Resource Usage

- **Memory:** < 50 MB for 100 branches
- **CPU:** Minimal (git commands are I/O bound)
- **Disk I/O:** Only git metadata access

### Scalability

- Support 1000+ branches efficiently
- Streaming processing for large branch lists
- Batch operations where possible

---

## 10. Security Specifications

### Input Validation

- Branch names must match safe patterns
- Pattern validation (regex/fnmatch)
- Path traversal prevention
- Sanitize all user inputs

### Authorization

- Only delete branches matching configured patterns
- Never delete branches outside `workflow/*` or `agent/*`
- Verify branch name format before deletion

### Audit Logging

- Log all deletion attempts (success and failure)
- Include timestamp, branch name, user context
- Generate audit report for compliance

---

## Summary

This design specification provides:

✅ **Complete API contracts** - All methods fully specified  
✅ **Data models** - Comprehensive data structures  
✅ **Error handling** - Robust error recovery  
✅ **Configuration** - Flexible and validated  
✅ **CLI interface** - User-friendly command design  
✅ **Testing contracts** - Clear test requirements  
✅ **Performance targets** - Measurable goals  
✅ **Security requirements** - Safe operations  

**Proceed to Step 5: Implementation**
