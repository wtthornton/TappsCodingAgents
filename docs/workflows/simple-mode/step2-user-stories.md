# Step 2: User Stories and Planning

## Epic: Git Workflow Branch Cleanup Enhancement

**Epic Description:** Enhance TappsCodingAgents workflow branch management to automatically clean up orphaned Git branches after workflow step completion, preventing repository clutter and improving maintainability.

**Epic Priority:** High
**Epic Complexity:** Medium (5 story points)
**Business Value:** Reduces maintenance overhead, improves repository hygiene, prevents confusion about active workflows

---

## User Stories

### Story 1: Delete Git Branches When Removing Worktrees

**Story ID:** BRANCH-CLEANUP-001  
**Story Points:** 3  
**Priority:** Critical  
**Complexity:** Medium

**User Story:**
As a TappsCodingAgents user, I want Git branches to be automatically deleted when workflow step worktrees are removed, so that I don't accumulate orphaned branches in my repository.

**Acceptance Criteria:**
1. ✅ When `WorktreeManager.remove_worktree()` is called, it deletes the associated Git branch
2. ✅ Safe delete (`git branch -d`) is attempted first, then force delete (`git branch -D`) if needed
3. ✅ Branch deletion failures are logged but do not cause workflow execution to fail
4. ✅ Branch existence is verified before attempting deletion
5. ✅ Works correctly when branch doesn't exist (no error thrown)
6. ✅ Backward compatible - existing workflows continue to work
7. ✅ Windows compatibility verified (path handling, git commands)

**Technical Tasks:**
1. Add `_delete_branch()` helper method to `WorktreeManager`
2. Enhance `remove_worktree()` to call `_delete_branch()` after worktree removal
3. Implement safe delete with fallback to force delete
4. Add comprehensive error handling and logging
5. Update method docstring with new behavior
6. Add type hints for all new methods

**Dependencies:** None (foundational story)

**Test Coverage Required:**
- Unit tests for branch deletion logic
- Test branch deletion when branch exists
- Test branch deletion when branch doesn't exist
- Test error handling for git command failures
- Integration tests with actual workflow execution

---

### Story 2: Detect Orphaned Workflow Branches

**Story ID:** BRANCH-CLEANUP-002  
**Story Points:** 5  
**Priority:** High  
**Complexity:** High

**User Story:**
As a TappsCodingAgents user, I want to detect branches that no longer have associated worktrees, so that I can identify which branches need cleanup.

**Acceptance Criteria:**
1. ✅ Method to list all branches matching `workflow/*` pattern
2. ✅ Method to list all branches matching `agent/*` pattern
3. ✅ For each branch, check if corresponding worktree directory exists
4. ✅ Return list of orphaned branches with metadata:
   - Branch name
   - Age (last commit date)
   - Last commit message
   - Size/diff stats (optional)
5. ✅ Filter by age (branches older than retention period)
6. ✅ Filter by pattern (workflow vs agent branches)
7. ✅ Handle errors gracefully (non-existent branches, git command failures)

**Technical Tasks:**
1. Create `BranchCleanupService` class in new file `tapps_agents/workflow/branch_cleanup.py`
2. Implement `detect_orphaned_branches()` method
3. Add `_get_branch_list()` helper to get branches matching pattern
4. Add `_get_branch_metadata()` helper to extract branch information
5. Add `_worktree_exists_for_branch()` helper to check worktree existence
6. Implement age-based filtering logic
7. Add comprehensive error handling

**Dependencies:** Story 1 (uses branch naming conventions)

**Test Coverage Required:**
- Unit tests for orphaned branch detection
- Test with various branch patterns
- Test age filtering logic
- Test error handling
- Integration tests with real repository state

---

### Story 3: Automated Cleanup of Orphaned Branches

**Story ID:** BRANCH-CLEANUP-003  
**Story Points:** 5  
**Priority:** High  
**Complexity:** High

**User Story:**
As a TappsCodingAgents user, I want orphaned branches to be automatically cleaned up based on retention policies, so that my repository stays clean without manual intervention.

**Acceptance Criteria:**
1. ✅ `cleanup_orphaned_branches()` method deletes orphaned branches older than retention period
2. ✅ Respects `keep_active` flag - preserves branches with uncommitted changes
3. ✅ Configurable retention period (default: 7 days)
4. ✅ Dry-run mode available to preview what would be deleted
5. ✅ Returns cleanup report:
   - Number of branches deleted
   - List of deleted branch names
   - Errors encountered (if any)
6. ✅ Safe execution - doesn't delete branches outside `workflow/` and `agent/` patterns
7. ✅ Logs all cleanup operations for audit trail

**Technical Tasks:**
1. Implement `cleanup_orphaned_branches()` method in `BranchCleanupService`
2. Integrate with `detect_orphaned_branches()` from Story 2
3. Add retention period calculation logic
4. Implement dry-run mode
5. Add branch deletion with progress reporting
6. Generate cleanup report with detailed information
7. Add comprehensive error handling and recovery

**Dependencies:** Story 2 (uses orphaned branch detection)

**Test Coverage Required:**
- Unit tests for cleanup logic
- Test retention period filtering
- Test dry-run mode
- Test `keep_active` flag behavior
- Test error handling and partial failures
- Integration tests with cleanup execution

---

### Story 4: Configuration Management for Branch Cleanup

**Story ID:** BRANCH-CLEANUP-004  
**Story Points:** 3  
**Priority:** Medium  
**Complexity:** Medium

**User Story:**
As a TappsCodingAgents user, I want to configure branch cleanup behavior via configuration file, so that I can customize cleanup policies for my project.

**Acceptance Criteria:**
1. ✅ Configuration section in `.tapps-agents/config.yaml`:
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
2. ✅ Configuration schema extended in `ProjectConfig`
3. ✅ Sensible defaults if configuration not specified
4. ✅ Configuration validation on load
5. ✅ Configuration documentation updated
6. ✅ Backward compatible - works without configuration (uses defaults)

**Technical Tasks:**
1. Extend `ProjectConfig` schema in `tapps_agents/core/config.py`
2. Add `BranchCleanupConfig` dataclass/model
3. Implement default values
4. Add configuration validation
5. Update configuration documentation
6. Add migration guide if needed

**Dependencies:** None (standalone, but used by Stories 3, 5)

**Test Coverage Required:**
- Unit tests for configuration parsing
- Test default values
- Test configuration validation
- Test backward compatibility

---

### Story 5: CLI Command for Manual Branch Cleanup

**Story ID:** BRANCH-CLEANUP-005  
**Story Points:** 3  
**Priority:** Medium  
**Complexity:** Medium

**User Story:**
As a TappsCodingAgents user, I want a CLI command to manually clean up orphaned branches, so that I can immediately clean up old branches when needed.

**Acceptance Criteria:**
1. ✅ CLI command: `tapps-agents workflow cleanup-branches`
2. ✅ Command options:
   - `--dry-run`: Preview what would be deleted (default: false)
   - `--retention-days N`: Override retention period (default: from config)
   - `--pattern PATTERN`: Branch pattern to match (default: all patterns)
   - `--force`: Skip confirmation prompts (default: false)
3. ✅ Progress reporting during cleanup
4. ✅ Summary report after cleanup (branches deleted, errors, etc.)
5. ✅ Interactive confirmation before deletion (unless `--force`)
6. ✅ Clear error messages for troubleshooting

**Technical Tasks:**
1. Add command handler in `tapps_agents/cli/workflow_commands.py`
2. Create `cleanup_branches_command()` function
3. Integrate with `BranchCleanupService` from Story 3
4. Implement CLI argument parsing
5. Add progress reporting with rich/progress indicators
6. Add confirmation prompts
7. Format output for terminal display

**Dependencies:** Stories 3, 4 (uses cleanup service and configuration)

**Test Coverage Required:**
- Unit tests for CLI command parsing
- Test dry-run mode via CLI
- Test all command options
- Test error handling
- Integration tests for full CLI workflow

---

### Story 6: Documentation and User Guides

**Story ID:** BRANCH-CLEANUP-006  
**Story Points:** 2  
**Priority:** Medium  
**Complexity:** Low

**User Story:**
As a TappsCodingAgents user, I want comprehensive documentation about branch cleanup, so that I understand how to use and configure the feature.

**Acceptance Criteria:**
1. ✅ API documentation for all new methods and classes
2. ✅ User guide for branch cleanup configuration
3. ✅ CLI command documentation
4. ✅ Migration guide (if configuration changes needed)
5. ✅ Examples of common cleanup scenarios
6. ✅ Troubleshooting guide for common issues

**Technical Tasks:**
1. Add docstrings to all new methods and classes
2. Create user guide document
3. Update CLI help text
4. Add examples to documentation
5. Create troubleshooting section

**Dependencies:** All previous stories (documents the complete feature)

**Test Coverage Required:**
- Documentation review
- Example validation

---

## Story Dependency Graph

```
Story 1 (Foundation)
    ↓
Story 2 (Detection)
    ↓
Story 3 (Cleanup) ← Story 4 (Config)
    ↓
Story 5 (CLI) ← Story 4 (Config)
    ↓
Story 6 (Documentation)
```

**Execution Order:**
1. Story 1: Core enhancement (foundational)
2. Story 4: Configuration (can be parallel with Story 1)
3. Story 2: Detection (depends on Story 1)
4. Story 3: Cleanup (depends on Stories 2, 4)
5. Story 5: CLI (depends on Stories 3, 4)
6. Story 6: Documentation (depends on all stories)

---

## Effort Estimation

| Story | Points | Estimated Hours | Priority |
|-------|--------|----------------|----------|
| BRANCH-CLEANUP-001 | 3 | 6-8 hours | Critical |
| BRANCH-CLEANUP-002 | 5 | 10-12 hours | High |
| BRANCH-CLEANUP-003 | 5 | 10-12 hours | High |
| BRANCH-CLEANUP-004 | 3 | 6-8 hours | Medium |
| BRANCH-CLEANUP-005 | 3 | 6-8 hours | Medium |
| BRANCH-CLEANUP-006 | 2 | 4-6 hours | Medium |
| **Total** | **21** | **42-54 hours** | |

**Total Story Points:** 21 points  
**Estimated Duration:** 1-2 weeks (depending on parallelization)

---

## Risk Mitigation

### High-Risk Stories
- **Story 1:** Breaking existing workflows
  - **Mitigation:** Comprehensive testing, backward compatibility checks, feature flag option

### Medium-Risk Stories
- **Story 3:** Accidental branch deletion
  - **Mitigation:** Pattern matching, dry-run mode, confirmation prompts

---

## Success Metrics

1. ✅ All workflow branches automatically cleaned up after completion
2. ✅ CLI command successfully detects and cleans orphaned branches
3. ✅ Configuration allows flexible cleanup policies
4. ✅ Zero breaking changes to existing workflows
5. ✅ Test coverage ≥80% for all new code
6. ✅ Windows compatibility verified
7. ✅ Documentation complete and accurate

**Proceed to Step 3: Architecture Design**
