# Step 2: User Stories - IDE Clutter Management Implementation

**Workflow ID**: `ide-clutter-management-20250116-000000`  
**Step**: 2 - User Stories  
**Date**: 2025-01-16

---

## User Stories

### Story 1: Exclude Backup Directories from IDE Indexing

**As a** TappsCodingAgents user  
**I want** backup directories to be excluded from Cursor IDE autocomplete  
**So that** my IDE autocomplete is cleaner and more focused

**Acceptance Criteria**:
- [ ] `.tapps-agents/backups/` pattern is added to `.cursorignore` during `init`
- [ ] Pattern is added if missing, existing patterns are preserved
- [ ] Backup directories remain accessible via file explorer
- [ ] Pattern works correctly on Windows and Unix systems

**Story Points**: 2  
**Priority**: High  
**Estimate**: 30 minutes

**Technical Notes**:
- Update `init` command to append pattern if missing
- Use pattern matching to avoid duplicates
- Preserve user customizations

---

### Story 2: Cleanup Workflow Documentation Directories

**As a** TappsCodingAgents user  
**I want** to clean up old workflow documentation directories  
**So that** my project doesn't accumulate hundreds of workflow directories

**Acceptance Criteria**:
- [ ] `CleanupTool.cleanup_workflow_docs()` method exists
- [ ] Method supports `keep_latest` parameter (default: 5)
- [ ] Method supports `retention_days` parameter (default: 30)
- [ ] Method supports `archive_dir` parameter
- [ ] Method supports `dry_run` mode
- [ ] Method returns dictionary with cleanup results
- [ ] Old workflows are archived (not deleted) when retention period expires
- [ ] Latest N workflows are always kept visible

**Story Points**: 5  
**Priority**: High  
**Estimate**: 1.5 hours

**Technical Notes**:
- Scan `docs/workflows/simple-mode/` directory
- Sort workflows by modification time (newest first)
- Keep latest N workflows
- Archive workflows older than retention_days
- Use `shutil.move()` or copy + delete for Windows compatibility

---

### Story 3: Configure Workflow Cleanup Retention Policies

**As a** TappsCodingAgents user  
**I want** to configure retention policies for workflow cleanup  
**So that** I can customize cleanup behavior per project

**Acceptance Criteria**:
- [ ] `WorkflowDocsCleanupConfig` Pydantic model exists
- [ ] Model has fields: `enabled`, `keep_latest`, `retention_days`, `archive_enabled`, `archive_dir`
- [ ] Model is integrated into `ProjectConfig.cleanup` section
- [ ] Default values are sensible (keep_latest=5, retention_days=30)
- [ ] Configuration is validated on load
- [ ] Configuration can be updated via config file

**Story Points**: 3  
**Priority**: Medium  
**Estimate**: 45 minutes

**Technical Notes**:
- Use Pydantic BaseModel for validation
- Add to `ProjectConfig` class
- Provide sensible defaults
- Document configuration options

---

### Story 4: CLI Command for Workflow Cleanup

**As a** TappsCodingAgents user  
**I want** a CLI command to clean up workflow documentation  
**So that** I can easily manage workflow directories

**Acceptance Criteria**:
- [ ] `tapps-agents cleanup workflow-docs` command exists
- [ ] Command supports `--keep-latest` option (default: 5)
- [ ] Command supports `--retention-days` option (default: 30)
- [ ] Command supports `--archive` flag (enables archival)
- [ ] Command supports `--dry-run` flag (preview only)
- [ ] Command shows summary of what would be cleaned/archived
- [ ] Command integrates with `CleanupTool.cleanup_workflow_docs()`
- [ ] Command provides clear error messages

**Story Points**: 5  
**Priority**: High  
**Estimate**: 1 hour

**Technical Notes**:
- Add subcommand to `cleanup` command group
- Parse arguments using argparse
- Call `CleanupTool.cleanup_workflow_docs()`
- Format output for user readability
- Handle errors gracefully

---

### Story 5: Auto-Update .cursorignore During Init

**As a** TappsCodingAgents user  
**I want** `.cursorignore` to be automatically updated with TappsCodingAgents patterns  
**So that** I don't have to manually manage IDE ignore patterns

**Acceptance Criteria**:
- [ ] `init` command updates `.cursorignore` if missing patterns
- [ ] Missing patterns are appended (not overwritten)
- [ ] Existing user patterns are preserved
- [ ] Patterns added: `.tapps-agents/backups/`, `.tapps-agents/archives/`, `.tapps-agents/artifacts/`
- [ ] Duplicate patterns are not added
- [ ] Update is idempotent (safe to run multiple times)

**Story Points**: 3  
**Priority**: Medium  
**Estimate**: 45 minutes

**Technical Notes**:
- Create `_update_cursorignore_patterns()` helper function
- Read existing `.cursorignore` file
- Check for missing patterns
- Append missing patterns with comments
- Preserve existing content and formatting

---

### Story 6: Integrate Workflow Cleanup into Cleanup All

**As a** TappsCodingAgents user  
**I want** workflow cleanup to be part of the general cleanup command  
**So that** I can clean up all artifacts with one command

**Acceptance Criteria**:
- [ ] `CleanupTool.cleanup_all()` includes workflow docs cleanup
- [ ] Method accepts `workflow_keep_latest` parameter
- [ ] Method accepts `workflow_retention_days` parameter
- [ ] Workflow cleanup respects `dry_run` flag
- [ ] Summary includes workflow cleanup results

**Story Points**: 2  
**Priority**: Low  
**Estimate**: 30 minutes

**Technical Notes**:
- Update `cleanup_all()` method signature
- Call `cleanup_workflow_docs()` with appropriate parameters
- Include results in summary dictionary

---

## Story Dependencies

```
Story 3 (Config) → Story 2 (CleanupTool) → Story 4 (CLI)
Story 1 (cursorignore) → Story 5 (Init)
Story 2 (CleanupTool) → Story 6 (Cleanup All)
```

## Story Estimates Summary

| Story | Points | Estimate | Priority |
|-------|--------|----------|----------|
| Story 1: Backup Exclusion | 2 | 30 min | High |
| Story 2: Cleanup Method | 5 | 1.5 hours | High |
| Story 3: Configuration | 3 | 45 min | Medium |
| Story 4: CLI Command | 5 | 1 hour | High |
| Story 5: Init Enhancement | 3 | 45 min | Medium |
| Story 6: Integration | 2 | 30 min | Low |
| **Total** | **20** | **~5 hours** | |

## Implementation Order

1. **Story 1**: Backup Exclusion (quick win, low risk)
2. **Story 3**: Configuration Schema (foundation for cleanup)
3. **Story 2**: Cleanup Method (core functionality)
4. **Story 4**: CLI Command (user-facing feature)
5. **Story 5**: Init Enhancement (user experience)
6. **Story 6**: Integration (polish)

## Risk Assessment

**Low Risk**:
- Story 1: Simple pattern addition
- Story 3: Configuration schema (well-defined)
- Story 5: Append-only pattern update

**Medium Risk**:
- Story 2: File operations need careful testing
- Story 4: CLI integration needs validation

**Mitigation**:
- Dry-run mode by default
- Comprehensive testing
- Windows compatibility testing
- Error handling and validation

---

## Next Steps

Proceed to Step 3: Architecture Design to define component structure and integration patterns.
