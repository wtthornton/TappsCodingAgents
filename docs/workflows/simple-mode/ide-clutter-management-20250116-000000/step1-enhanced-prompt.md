# Step 1: Enhanced Prompt - IDE Clutter Management Implementation

**Workflow ID**: `ide-clutter-management-20250116-000000`  
**Step**: 1 - Enhanced Prompt  
**Date**: 2025-01-16

---

## Original Prompt

Implement IDE clutter management improvements for TappsCodingAgents based on recommendations document. This includes:
- Adding `.tapps-agents/backups/` to `.cursorignore`
- Extending `CleanupTool` with workflow documentation cleanup
- Adding retention policies and archival system
- Updating `init` command to auto-generate `.cursorignore` patterns
- Creating CLI commands for workflow cleanup

---

## Enhanced Prompt (7-Stage Pipeline)

### Stage 1: Analysis

**Intent**: Implement comprehensive IDE clutter management system for TappsCodingAgents framework

**Domains**: 
- File system management
- IDE integration (Cursor)
- Cleanup automation
- Configuration management
- CLI tooling

**Scope**: 
- Framework-level changes to `tapps_agents/core/cleanup_tool.py`
- Configuration schema updates in `tapps_agents/core/config.py`
- CLI command additions in `tapps_agents/cli/`
- `.cursorignore` pattern management in `tapps_agents/cli/commands/top_level.py` (init command)
- Workflow documentation manager enhancements

**Workflow Type**: Framework enhancement (brownfield)

### Stage 2: Requirements

#### Functional Requirements

1. **Backup Directory Exclusion**
   - Add `.tapps-agents/backups/` pattern to `.cursorignore`
   - Ensure pattern is added during `init` command
   - Preserve existing `.cursorignore` patterns

2. **Workflow Documentation Cleanup**
   - Extend `CleanupTool` class with `cleanup_workflow_docs()` method
   - Support retention policy (keep latest N workflows)
   - Support archival of old workflows
   - Support dry-run mode for safety

3. **Retention Policy Configuration**
   - Add `WorkflowDocsCleanupConfig` to `ProjectConfig`
   - Configurable `keep_latest` count
   - Configurable `retention_days`
   - Enable/disable archival

4. **CLI Commands**
   - `tapps-agents cleanup workflow-docs` command
   - Options: `--keep-latest`, `--retention-days`, `--archive`, `--dry-run`
   - Integration with existing `cleanup_all()` method

5. **Init Command Enhancement**
   - Auto-generate/update `.cursorignore` patterns
   - Add missing TappsCodingAgents patterns
   - Preserve user customizations

#### Non-Functional Requirements

1. **Backward Compatibility**: All changes must be backward compatible
2. **Performance**: Cleanup operations should be fast (< 5 seconds for typical projects)
3. **Safety**: Dry-run mode by default, explicit confirmation for destructive operations
4. **Windows Compatibility**: Archive operations must work on Windows (no symlinks)
5. **Error Handling**: Graceful handling of missing directories, permission errors

### Stage 3: Architecture

**Design Patterns**:
- Strategy Pattern: Different cleanup strategies (delete vs archive)
- Builder Pattern: Configuration builder for cleanup options
- Template Method: Base cleanup logic with customizable steps

**Component Design**:

1. **CleanupTool Extension** (`tapps_agents/core/cleanup_tool.py`)
   - New method: `cleanup_workflow_docs()`
   - Integration with existing cleanup methods
   - Archive support via `shutil.move()` or copy + delete

2. **Configuration Schema** (`tapps_agents/core/config.py`)
   - New class: `WorkflowDocsCleanupConfig`
   - Fields: `enabled`, `keep_latest`, `retention_days`, `archive_enabled`, `archive_dir`

3. **CLI Parser** (`tapps_agents/cli/parsers/top_level.py`)
   - New subcommand: `cleanup workflow-docs`
   - Argument parsing for cleanup options

4. **CLI Command Handler** (`tapps_agents/cli/commands/top_level.py`)
   - New function: `handle_cleanup_workflow_docs_command()`
   - Integration with `CleanupTool`

5. **Init Command** (`tapps_agents/cli/commands/top_level.py`)
   - Enhancement: `_update_cursorignore_patterns()` function
   - Pattern management logic

**Technology Stack**:
- Python standard library: `pathlib`, `shutil`, `datetime`
- Existing TappsCodingAgents infrastructure
- No new external dependencies

### Stage 4: Codebase Context

**Related Files**:
- `tapps_agents/core/cleanup_tool.py` - Existing cleanup infrastructure
- `tapps_agents/core/config.py` - Configuration schema
- `tapps_agents/cli/parsers/top_level.py` - CLI argument parsing
- `tapps_agents/cli/commands/top_level.py` - CLI command handlers
- `tapps_agents/simple_mode/documentation_manager.py` - Workflow documentation manager
- `.cursorignore` - IDE ignore patterns (project root)
- `docs/IDE_CLUTTER_MANAGEMENT_RECOMMENDATIONS.md` - Requirements document

**Existing Patterns**:
- Cleanup methods follow pattern: `cleanup_<type>(days, dry_run) -> dict`
- Configuration uses Pydantic BaseModel
- CLI commands use argparse with consistent structure
- Archive operations use `shutil.move()` or copy + delete

**Integration Points**:
- `CleanupTool.cleanup_all()` - Add workflow docs cleanup
- `ProjectConfig` - Add cleanup config section
- `init` command - Add `.cursorignore` update step

### Stage 5: Quality Standards

**Security**:
- Validate archive paths to prevent directory traversal
- Sanitize workflow IDs to prevent path injection
- Permission checks before file operations

**Testing**:
- Unit tests for `cleanup_workflow_docs()` method
- Unit tests for configuration schema
- Integration tests for CLI commands
- Test archive/restore functionality
- Test `.cursorignore` pattern updates

**Performance**:
- Efficient directory scanning (use `pathlib.glob()`)
- Batch operations where possible
- Progress reporting for long operations

**Documentation**:
- Docstrings for all new methods
- CLI help text for new commands
- Update command reference documentation

### Stage 6: Implementation Strategy

**Task Breakdown**:

1. **Phase 1: Configuration Schema** (30 min)
   - Add `WorkflowDocsCleanupConfig` class
   - Update `ProjectConfig` to include cleanup config
   - Add default values

2. **Phase 2: CleanupTool Extension** (1 hour)
   - Implement `cleanup_workflow_docs()` method
   - Add retention policy logic
   - Add archival support
   - Add dry-run support
   - Update `cleanup_all()` method

3. **Phase 3: CLI Integration** (45 min)
   - Add parser arguments for `cleanup workflow-docs`
   - Implement command handler
   - Add to command routing
   - Add help text

4. **Phase 4: Init Command Enhancement** (30 min)
   - Implement `_update_cursorignore_patterns()` function
   - Add pattern list
   - Add merge logic (preserve existing)
   - Integrate into init workflow

5. **Phase 5: Testing** (1 hour)
   - Write unit tests
   - Write integration tests
   - Manual testing
   - Edge case testing

**Dependencies**:
- No external dependencies
- Uses existing TappsCodingAgents infrastructure

**Risk Mitigation**:
- Dry-run mode by default
- Backup before archival (optional)
- Validation of all paths
- Graceful error handling

### Stage 7: Synthesis

**Final Enhanced Prompt**:

Implement a comprehensive IDE clutter management system for TappsCodingAgents that:

1. **Extends CleanupTool** with workflow documentation cleanup capabilities:
   - Add `cleanup_workflow_docs()` method supporting retention policies (keep latest N workflows, archive after X days)
   - Integrate with existing `cleanup_all()` method
   - Support dry-run mode and archival to `.tapps-agents/archives/workflows/`

2. **Adds Configuration Schema** for workflow cleanup:
   - Create `WorkflowDocsCleanupConfig` Pydantic model with fields: `enabled`, `keep_latest`, `retention_days`, `archive_enabled`, `archive_dir`
   - Integrate into `ProjectConfig.cleanup` section

3. **Creates CLI Command** `tapps-agents cleanup workflow-docs`:
   - Options: `--keep-latest`, `--retention-days`, `--archive`, `--dry-run`
   - Handler function that uses `CleanupTool.cleanup_workflow_docs()`
   - Proper error handling and user feedback

4. **Enhances Init Command** to auto-manage `.cursorignore`:
   - Add `_update_cursorignore_patterns()` function that appends missing TappsCodingAgents patterns
   - Patterns to add: `.tapps-agents/backups/`, `.tapps-agents/archives/`, `.tapps-agents/artifacts/`
   - Preserve existing user patterns

5. **Follows Framework Standards**:
   - Backward compatible changes
   - Comprehensive error handling
   - Windows-compatible archive operations
   - Unit and integration tests
   - Complete documentation

**Key Requirements**:
- All operations must support dry-run mode
- Archive operations must work on Windows (use copy + delete, not symlinks)
- Preserve user customizations in `.cursorignore`
- Follow existing code patterns and style
- Include comprehensive tests

**Success Criteria**:
- `tapps-agents cleanup workflow-docs --dry-run` works correctly
- `tapps-agents init` updates `.cursorignore` with missing patterns
- Old workflow directories are archived (not deleted) when retention period expires
- Configuration is properly validated and documented
- All tests pass

---

## Key Decisions

1. **Archive vs Delete**: Archive old workflows to preserve history, delete only very old (> 1 year)
2. **Windows Compatibility**: Use `shutil.move()` or copy + delete instead of symlinks
3. **Pattern Management**: Append-only approach for `.cursorignore` to preserve user customizations
4. **Default Retention**: Keep 5 latest workflows, archive after 30 days (configurable)

---

## Quality Standards

- **Security**: Validate all file paths, prevent directory traversal
- **Testing**: Unit tests for all new methods, integration tests for CLI commands
- **Performance**: Efficient directory scanning, progress reporting
- **Documentation**: Complete docstrings and CLI help text

---

## Next Steps

Proceed to Step 2: User Stories creation with acceptance criteria for each requirement.
