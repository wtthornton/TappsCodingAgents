# Step 1: Enhanced Prompt - Git Workflow Branch Cleanup Enhancement

## Original Prompt

Implement automatic branch cleanup for TappsCodingAgents workflow branches - evaluate recommendations, enhance them, validate the approach, and execute the implementation

## Enhanced Prompt with Requirements Analysis

### Problem Statement

TappsCodingAgents creates Git worktrees and branches for workflow step isolation. Currently, when workflow steps complete, the worktree directories are removed but the associated Git branches remain orphaned in the repository. This leads to:
- Repository clutter with abandoned workflow branches
- Potential confusion about active vs completed workflows
- Storage inefficiency (though minimal)
- Maintenance overhead for manual cleanup

### Scope Analysis

**In Scope:**
- Enhance `WorktreeManager.remove_worktree()` to delete Git branches when removing worktrees
- Add automated cleanup mechanisms for orphaned branches
- Implement configuration options for cleanup policies
- Create retention policies for branch lifecycle management
- Add cleanup utilities for immediate manual cleanup
- Ensure backward compatibility with existing workflows

**Out of Scope:**
- Remote branch deletion (can be added later)
- Branch force-push protection
- Branch locking mechanisms
- Custom branch naming schemes (uses existing patterns)

### Functional Requirements

#### FR1: Branch Deletion on Worktree Removal
- **Priority:** Critical
- **Description:** When `remove_worktree()` is called, it must delete the associated Git branch
- **Acceptance Criteria:**
  - Branch is deleted after worktree removal succeeds
  - Safe delete (`-d`) attempted first, then force delete (`-D`) if needed
  - Graceful handling of branch deletion failures (log warning, don't fail workflow)
  - Works for both local and tracked remote branches

#### FR2: Orphaned Branch Detection
- **Priority:** High
- **Description:** Ability to identify branches that no longer have associated worktrees
- **Acceptance Criteria:**
  - Detect branches matching `workflow/*` pattern without corresponding worktrees
  - Detect branches matching `agent/*` pattern without corresponding worktrees
  - Age-based filtering (branches older than retention period)
  - Report orphaned branches with metadata (age, last commit, etc.)

#### FR3: Automated Cleanup Service
- **Priority:** High
- **Description:** Periodic cleanup of orphaned branches based on retention policies
- **Acceptance Criteria:**
  - Configurable retention period (default: 7 days)
  - Respects `keep_active` flag (preserve branches with uncommitted changes)
  - Safe execution (dry-run mode available)
  - Reporting of cleanup results (branches deleted, space freed)

#### FR4: Configuration Management
- **Priority:** Medium
- **Description:** Configuration options for cleanup behavior
- **Acceptance Criteria:**
  - Config file options in `.tapps-agents/config.yaml`
  - Separate policies for workflow vs agent branches
  - Enable/disable auto-cleanup flag
  - Retention period configuration

#### FR5: Manual Cleanup Utilities
- **Priority:** Medium
- **Description:** CLI commands and utilities for immediate manual cleanup
- **Acceptance Criteria:**
  - CLI command: `tapps-agents workflow cleanup-branches [--dry-run] [--retention-days N]`
  - Safe preview before deletion (dry-run mode)
  - Progress reporting during cleanup

### Non-Functional Requirements

#### NFR1: Backward Compatibility
- **Priority:** Critical
- **Description:** Changes must not break existing workflows or worktree operations
- **Acceptance Criteria:**
  - Existing `remove_worktree()` calls continue to work
  - No breaking changes to API signatures
  - Graceful degradation if git commands fail

#### NFR2: Error Handling
- **Priority:** High
- **Description:** Robust error handling for git operations
- **Acceptance Criteria:**
  - Never fail workflow execution due to cleanup failures
  - Log all errors with appropriate severity
  - Fallback mechanisms when git operations fail
  - Clear error messages for troubleshooting

#### NFR3: Performance
- **Priority:** Medium
- **Description:** Cleanup operations should not significantly impact workflow performance
- **Acceptance Criteria:**
  - Branch deletion completes in <1 second per branch
  - Bulk cleanup operations can handle 100+ branches efficiently
  - Non-blocking execution (async operations)

#### NFR4: Windows Compatibility
- **Priority:** Critical
- **Description:** All operations must work correctly on Windows
- **Acceptance Criteria:**
  - Handle Windows path separators correctly
  - Handle Windows git command quirks
  - Test on Windows environment
  - Encoding-safe error messages

#### NFR5: Security
- **Priority:** High
- **Description:** Prevent accidental deletion of important branches
- **Acceptance Criteria:**
  - Never delete branches outside `workflow/` and `agent/` patterns
  - Require explicit confirmation for bulk operations
  - Respect branch protection rules if configured
  - Dry-run mode as default for destructive operations

### Architecture Guidance

#### Component Structure

1. **WorktreeManager Enhancement** (`tapps_agents/workflow/worktree_manager.py`)
   - Extend `remove_worktree()` to delete branches
   - Add `_delete_branch()` helper method
   - Add branch existence checking before deletion

2. **Branch Cleanup Service** (new file: `tapps_agents/workflow/branch_cleanup.py`)
   - `BranchCleanupService` class
   - Methods:
     - `detect_orphaned_branches()` - Find branches without worktrees
     - `cleanup_orphaned_branches()` - Execute cleanup
     - `list_orphaned_branches()` - Reporting utility

3. **Configuration Extension** (`tapps_agents/core/config.py`)
   - Add `branch_cleanup` section to config schema
   - Settings:
     - `enabled`: bool
     - `delete_branches_on_cleanup`: bool
     - `retention_days`: int
     - `auto_cleanup_on_completion`: bool

4. **CLI Command** (`tapps_agents/cli/workflow_commands.py`)
   - New command: `cleanup-branches`
   - Options: `--dry-run`, `--retention-days`, `--pattern`

#### Design Patterns

- **Strategy Pattern:** Configurable cleanup policies
- **Command Pattern:** CLI commands for cleanup operations
- **Facade Pattern:** Simple API hiding complex git operations

#### Integration Points

- Integrates with existing `WorktreeManager`
- Uses `ProjectConfig` for settings
- Leverages existing logging infrastructure
- Follows existing async patterns

### Codebase Context

#### Key Files to Modify

1. **`tapps_agents/workflow/worktree_manager.py`**
   - Current `remove_worktree()` method (line 302-329)
   - `_branch_for()` method for branch name generation (line 76-81)
   - Need to add branch deletion logic

2. **`tapps_agents/workflow/cursor_executor.py`**
   - Workflow executor calls `remove_worktree()` (line 1711, 1872)
   - Ensure cleanup doesn't break workflow execution

3. **`tapps_agents/core/config.py`**
   - Configuration schema definition
   - Add branch cleanup configuration section

4. **`tapps_agents/cli/workflow_commands.py`**
   - CLI command registration
   - Add cleanup-branches command handler

#### Existing Patterns to Follow

- Async/await pattern (all methods are async)
- Error handling with try/except and logging
- Subprocess usage for git commands (see existing code)
- Configuration access via `ProjectConfig`

### Quality Standards

#### Code Quality
- **Complexity:** Keep methods under 30 lines
- **Test Coverage:** Minimum 80% coverage
- **Type Hints:** All methods must have type hints
- **Docstrings:** All public methods documented

#### Security Standards
- **Input Validation:** Validate branch names before deletion
- **Pattern Matching:** Only delete branches matching safe patterns
- **Confirmation:** Require explicit confirmation for bulk operations
- **Logging:** Log all branch deletion operations for audit trail

#### Testing Requirements
- **Unit Tests:** Test branch deletion logic
- **Integration Tests:** Test workflow cleanup scenarios
- **Edge Cases:** Test with non-existent branches, protected branches
- **Windows Tests:** Verify Windows compatibility

#### Documentation
- **API Documentation:** Document new methods and configuration
- **User Guide:** Document cleanup commands and configuration
- **Migration Guide:** Document any configuration changes

### Implementation Strategy

#### Phase 1: Core Enhancement (Priority: Critical)
1. Enhance `WorktreeManager.remove_worktree()` with branch deletion
2. Add `_delete_branch()` helper method
3. Add comprehensive error handling
4. Update tests for new behavior

#### Phase 2: Cleanup Service (Priority: High)
1. Create `BranchCleanupService` class
2. Implement orphaned branch detection
3. Implement cleanup logic with retention policies
4. Add configuration support

#### Phase 3: CLI Integration (Priority: Medium)
1. Add CLI command for manual cleanup
2. Implement dry-run mode
3. Add progress reporting
4. Create user documentation

#### Phase 4: Configuration & Documentation (Priority: Medium)
1. Extend configuration schema
2. Update configuration documentation
3. Add migration guide if needed
4. Update user guides

### Dependencies

#### Internal Dependencies
- `tapps_agents.core.config.ProjectConfig`
- `tapps_agents.core.logging` (existing logger)
- `tapps_agents.workflow.models` (for type hints)

#### External Dependencies
- `git` command-line tool (already required)
- Python standard library (subprocess, pathlib, datetime)

#### Testing Dependencies
- `pytest` (existing)
- `pytest-asyncio` (for async tests)
- Git test fixtures (may need to create)

### Risk Assessment

#### High Risk Items
1. **Breaking Existing Workflows:** Mitigation - comprehensive testing, backward compatibility checks
2. **Accidental Branch Deletion:** Mitigation - pattern matching, dry-run mode, confirmation prompts
3. **Git Command Failures:** Mitigation - graceful error handling, fallback mechanisms

#### Medium Risk Items
1. **Performance Impact:** Mitigation - async operations, efficient git queries
2. **Windows Compatibility:** Mitigation - Windows-specific testing, path handling

#### Low Risk Items
1. **Configuration Complexity:** Mitigation - sensible defaults, clear documentation
2. **User Adoption:** Mitigation - opt-in features, clear migration path

### Success Criteria

1. ✅ All workflow branches are automatically cleaned up after step completion
2. ✅ Orphaned branches can be detected and cleaned up via CLI
3. ✅ Configuration allows flexible cleanup policies
4. ✅ No breaking changes to existing workflows
5. ✅ Comprehensive test coverage (≥80%)
6. ✅ Windows compatibility verified
7. ✅ Documentation complete and accurate

## Next Steps

This enhanced prompt provides:
- ✅ Clear problem statement and scope
- ✅ Detailed functional and non-functional requirements
- ✅ Architecture guidance with component structure
- ✅ Codebase context with key files identified
- ✅ Quality standards for implementation
- ✅ Phased implementation strategy
- ✅ Risk assessment and mitigation

**Proceed to Step 2: User Stories and Planning**
