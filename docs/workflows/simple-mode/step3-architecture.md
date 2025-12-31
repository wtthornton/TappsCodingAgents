# Step 3: Architecture Design - Git Workflow Branch Cleanup

## System Architecture Overview

This enhancement extends the existing TappsCodingAgents workflow system with automatic Git branch cleanup capabilities. The architecture builds upon the existing `WorktreeManager` component and introduces a new `BranchCleanupService` for orphaned branch management.

---

## Component Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Execution Layer                  │
│                                                               │
│  ┌──────────────────┐         ┌──────────────────────────┐  │
│  │ CursorExecutor   │────────▶│   WorktreeManager        │  │
│  │                  │         │   (Enhanced)             │  │
│  └──────────────────┘         │  • remove_worktree()     │  │
│                                │  • _delete_branch() NEW  │  │
│                                └────────────┬─────────────┘  │
│                                             │                │
│                                ┌────────────▼─────────────┐  │
│                                │  BranchCleanupService    │  │
│                                │  (NEW)                   │  │
│                                │  • detect_orphaned()     │  │
│                                │  • cleanup_orphaned()    │  │
│                                └────────────┬─────────────┘  │
└─────────────────────────────────────────────┼────────────────┘
                                              │
┌─────────────────────────────────────────────▼────────────────┐
│                   Configuration Layer                         │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         ProjectConfig (Extended)                        │  │
│  │  workflow.branch_cleanup:                               │  │
│  │    • enabled: bool                                      │  │
│  │    • delete_branches_on_cleanup: bool                   │  │
│  │    • retention_days: int                                │  │
│  │    • auto_cleanup_on_completion: bool                   │  │
│  │    • patterns: {workflow: str, agent: str}              │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
                                              │
┌─────────────────────────────────────────────▼────────────────┐
│                      CLI Layer                                 │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │    workflow_commands.py                                │  │
│  │    • cleanup_branches_command() NEW                    │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Enhanced WorktreeManager

**File:** `tapps_agents/workflow/worktree_manager.py`

**Responsibilities:**
- Create and manage Git worktrees for workflow steps
- **NEW:** Delete Git branches when removing worktrees
- Provide branch naming conventions

**Key Methods:**

```python
class WorktreeManager:
    async def remove_worktree(self, worktree_name: str) -> None:
        """
        Remove a worktree and its associated Git branch.
        
        Enhanced to delete the Git branch after worktree removal.
        """
        # 1. Remove worktree directory
        # 2. Delete associated Git branch (NEW)
        # 3. Handle errors gracefully
    
    def _delete_branch(self, branch_name: str) -> bool:
        """
        Delete a Git branch (safe delete with force fallback).
        
        Returns:
            True if branch was deleted or didn't exist, False on error
        """
        # 1. Verify branch exists
        # 2. Attempt safe delete (git branch -d)
        # 3. Fallback to force delete (git branch -D) if needed
        # 4. Log all operations
```

**Integration Points:**
- Called by `CursorWorkflowExecutor` after step completion
- Uses existing `_branch_for()` method for branch name resolution

**Error Handling:**
- Never fails workflow execution
- Logs warnings for cleanup failures
- Gracefully handles non-existent branches

---

### 2. BranchCleanupService (NEW)

**File:** `tapps_agents/workflow/branch_cleanup.py` (new file)

**Responsibilities:**
- Detect orphaned branches (branches without worktrees)
- Clean up orphaned branches based on retention policies
- Provide reporting and dry-run capabilities

**Class Structure:**

```python
class BranchCleanupService:
    def __init__(self, project_root: Path, config: BranchCleanupConfig):
        """Initialize cleanup service with configuration."""
    
    async def detect_orphaned_branches(
        self,
        pattern: str = "workflow/*",
        retention_days: int | None = None
    ) -> list[OrphanedBranch]:
        """
        Detect branches without associated worktrees.
        
        Returns:
            List of orphaned branch information
        """
    
    async def cleanup_orphaned_branches(
        self,
        pattern: str = "workflow/*",
        retention_days: int | None = None,
        dry_run: bool = False,
        keep_active: bool = True
    ) -> CleanupReport:
        """
        Clean up orphaned branches.
        
        Returns:
            Cleanup report with statistics
        """
    
    def _get_branch_list(self, pattern: str) -> list[str]:
        """Get all branches matching pattern."""
    
    def _get_branch_metadata(self, branch_name: str) -> BranchMetadata:
        """Extract metadata for a branch."""
    
    def _worktree_exists_for_branch(self, branch_name: str) -> bool:
        """Check if worktree exists for branch."""
```

**Data Models:**

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

@dataclass
class CleanupReport:
    """Results of branch cleanup operation."""
    branches_deleted: int
    branches_skipped: int
    branches_failed: int
    deleted_branches: list[str]
    skipped_branches: list[str]
    failed_branches: list[tuple[str, str]]  # (branch, error)
    dry_run: bool
```

**Integration Points:**
- Uses `WorktreeManager` for branch naming conventions
- Reads from `ProjectConfig` for cleanup policies
- Can be called from CLI or programmatically

---

### 3. Configuration Extension

**File:** `tapps_agents/core/config.py`

**New Configuration Schema:**

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

@dataclass
class WorkflowConfig:
    """Extended workflow configuration."""
    # ... existing fields ...
    branch_cleanup: BranchCleanupConfig = field(
        default_factory=BranchCleanupConfig
    )
```

**Configuration File Format:**

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

**Default Values:**
- Sensible defaults ensure backward compatibility
- Works without configuration (opt-in enhancement)

---

### 4. CLI Integration

**File:** `tapps_agents/cli/workflow_commands.py`

**New Command:**

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
        dry_run: Preview what would be deleted
        retention_days: Override retention period
        pattern: Branch pattern to match
        force: Skip confirmation prompts
    """
    # 1. Load configuration
    # 2. Initialize BranchCleanupService
    # 3. Detect orphaned branches
    # 4. Show preview (unless force)
    # 5. Execute cleanup (unless dry_run)
    # 6. Display results
```

**Command Usage:**

```bash
# Preview cleanup (dry-run)
tapps-agents workflow cleanup-branches --dry-run

# Clean up branches older than 7 days
tapps-agents workflow cleanup-branches --retention-days 7

# Clean up specific pattern
tapps-agents workflow cleanup-branches --pattern "workflow/*"

# Force cleanup without confirmation
tapps-agents workflow cleanup-branches --force
```

---

## Data Flow

### Workflow Step Completion Flow

```
┌─────────────────┐
│ CursorExecutor  │
│ (Step Complete) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ WorktreeManager │
│ .remove_worktree│
└────────┬────────┘
         │
         ├─── Remove worktree directory
         │
         ├─── Check config.delete_branches_on_cleanup
         │
         ├─── YES ────▶ _delete_branch()
         │                │
         │                ├─── git branch -d (safe delete)
         │                │
         │                └─── git branch -D (force, if needed)
         │
         └─── Log result (success/failure)
```

### Orphaned Branch Cleanup Flow

```
┌──────────────────┐
│ CLI / Scheduled  │
│  Cleanup Task    │
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│ BranchCleanupService │
│ .cleanup_orphaned()  │
└────────┬─────────────┘
         │
         ├─── Load configuration
         │
         ├─── detect_orphaned_branches()
         │    │
         │    ├─── Get branch list (git branch -a)
         │    │
         │    ├─── Filter by pattern
         │    │
         │    ├─── Check worktree existence
         │    │
         │    └─── Filter by age (retention_days)
         │
         ├─── IF dry_run: Report preview, EXIT
         │
         ├─── IF NOT force: Confirm with user
         │
         ├─── For each orphaned branch:
         │    │
         │    ├─── Check keep_active flag
         │    │
         │    ├─── Delete branch (git branch -D)
         │    │
         │    └─── Track result
         │
         └─── Generate and return CleanupReport
```

---

## Design Patterns

### 1. Strategy Pattern (Cleanup Policies)

Different cleanup strategies can be configured:
- Age-based cleanup (retention_days)
- Pattern-based filtering
- Active branch protection (keep_active)

### 2. Command Pattern (CLI Commands)

CLI commands encapsulate cleanup operations:
- Dry-run mode (preview without execution)
- Parameterized execution
- Reusable command structure

### 3. Facade Pattern (BranchCleanupService)

Simple API hiding complex git operations:
- Git command abstraction
- Error handling encapsulation
- Configuration management

### 4. Template Method Pattern (WorktreeManager)

Consistent cleanup sequence:
- Template: remove_worktree() defines sequence
- Hooks: _delete_branch() for extension
- Configurable via configuration

---

## Integration Points

### With Existing Components

1. **WorktreeManager Integration:**
   - Extends existing `remove_worktree()` method
   - Reuses `_branch_for()` for branch name resolution
   - Maintains backward compatibility

2. **Configuration Integration:**
   - Extends `ProjectConfig` schema
   - Uses existing configuration loading
   - Supports default values

3. **CLI Integration:**
   - Follows existing command structure
   - Uses existing CLI framework
   - Consistent with other workflow commands

4. **Logging Integration:**
   - Uses existing logger infrastructure
   - Consistent log levels and formats
   - Audit trail for all operations

### External Dependencies

1. **Git Command-Line:**
   - Required: `git` executable
   - Commands: `branch`, `worktree`, `rev-parse`
   - Version: Git 2.0+ (worktree support)

2. **Python Standard Library:**
   - `subprocess`: Git command execution
   - `pathlib`: Path management
   - `dataclasses`: Data models
   - `datetime`: Age calculations

---

## Security Considerations

### Branch Deletion Safety

1. **Pattern Matching:**
   - Only delete branches matching safe patterns (`workflow/*`, `agent/*`)
   - Never delete branches outside these patterns
   - Explicit pattern validation

2. **Confirmation Prompts:**
   - Require user confirmation for bulk operations
   - Dry-run mode as default for CLI
   - Force flag only for automation

3. **Audit Logging:**
   - Log all branch deletion operations
   - Include branch name, timestamp, reason
   - Track success/failure status

### Error Handling

1. **Graceful Degradation:**
   - Never fail workflow execution due to cleanup failures
   - Log errors but continue operation
   - Return error status without raising exceptions

2. **Git Command Failures:**
   - Handle non-existent branches gracefully
   - Retry logic for transient failures
   - Clear error messages for troubleshooting

---

## Performance Considerations

### Optimization Strategies

1. **Async Operations:**
   - All methods are async to avoid blocking
   - Parallel branch metadata collection (if multiple branches)
   - Non-blocking git command execution

2. **Efficient Git Queries:**
   - Batch branch listing (single `git branch -a` call)
   - Cache worktree list to avoid repeated queries
   - Minimize git command invocations

3. **Early Exit Conditions:**
   - Skip worktree check if branch is too new
   - Pattern matching before metadata extraction
   - Age filtering before worktree existence check

### Resource Usage

- **Memory:** Minimal (streaming branch list processing)
- **Disk I/O:** Git commands only (no file copying)
- **CPU:** Low (simple string matching and git queries)
- **Network:** None (local git operations)

---

## Scalability

### Large Repository Support

- Handles 100+ orphaned branches efficiently
- Streaming branch list processing
- Batch operations where possible
- Progress reporting for long-running operations

### Extension Points

1. **Custom Patterns:**
   - Configuration allows custom branch patterns
   - Extensible pattern matching system

2. **Custom Cleanup Logic:**
   - Pluggable cleanup strategies
   - Hook system for custom behavior

3. **Remote Branch Support:**
   - Architecture supports remote branch cleanup (future)
   - Pattern applies to both local and remote

---

## Testing Strategy

### Unit Tests

- `WorktreeManager._delete_branch()` - Branch deletion logic
- `BranchCleanupService.detect_orphaned_branches()` - Detection logic
- `BranchCleanupService.cleanup_orphaned_branches()` - Cleanup logic
- Configuration parsing and validation

### Integration Tests

- Workflow execution with branch cleanup
- CLI command execution
- End-to-end cleanup scenarios
- Error handling and recovery

### Edge Cases

- Non-existent branches
- Protected branches
- Concurrent operations
- Windows path handling
- Large number of branches

---

## Migration Path

### Backward Compatibility

- Existing workflows continue to work without changes
- Configuration is optional (sensible defaults)
- Feature can be disabled via configuration
- No breaking API changes

### Upgrade Steps

1. Update TappsCodingAgents package
2. (Optional) Add configuration to `.tapps-agents/config.yaml`
3. Run `tapps-agents workflow cleanup-branches --dry-run` to preview
4. Enable auto-cleanup in configuration if desired

---

## Future Enhancements

### Phase 2 Features (Out of Scope)

1. **Remote Branch Cleanup:**
   - Delete remote tracking branches
   - Support for multiple remotes
   - Remote branch pattern matching

2. **Scheduled Cleanup:**
   - Automatic periodic cleanup
   - Cron-like scheduling
   - Background task execution

3. **Branch Protection:**
   - Whitelist/blacklist branches
   - Branch tagging for protection
   - Custom protection rules

4. **Advanced Reporting:**
   - Cleanup history tracking
   - Statistics and analytics
   - Dashboard integration

---

## Summary

This architecture provides:

✅ **Non-invasive enhancement** - Extends existing components without breaking changes  
✅ **Configurable behavior** - Flexible cleanup policies via configuration  
✅ **Safe operations** - Pattern matching, confirmation prompts, dry-run mode  
✅ **Comprehensive error handling** - Never breaks workflows, graceful degradation  
✅ **Extensible design** - Easy to add new cleanup strategies and features  
✅ **Performance optimized** - Efficient git operations, async execution  
✅ **Well-tested** - Unit, integration, and edge case coverage  

**Proceed to Step 4: Component Design Specifications**
