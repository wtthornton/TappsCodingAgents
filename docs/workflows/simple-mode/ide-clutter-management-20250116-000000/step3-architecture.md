# Step 3: Architecture Design - IDE Clutter Management Implementation

**Workflow ID**: `ide-clutter-management-20250116-000000`  
**Step**: 3 - Architecture Design  
**Date**: 2025-01-16

---

## System Architecture Overview

The IDE Clutter Management system extends TappsCodingAgents with automated cleanup and IDE integration improvements. The architecture follows existing framework patterns and integrates seamlessly with current infrastructure.

```
┌─────────────────────────────────────────────────────────────┐
│                    TappsCodingAgents Framework              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐      ┌──────────────────────┐     │
│  │  CleanupTool     │◄─────►│  ProjectConfig        │     │
│  │  (Extended)      │       │  (Extended)          │     │
│  └────────┬─────────┘       └──────────┬───────────┘     │
│           │                              │                  │
│           │ cleanup_workflow_docs()      │                  │
│           │                              │                  │
│  ┌────────▼──────────────────────────────▼──────────┐     │
│  │         CLI Command Layer                         │     │
│  │  ┌──────────────────┐  ┌────────────────────┐  │     │
│  │  │ cleanup workflow │  │ init (enhanced)     │  │     │
│  │  │ -docs            │  │                    │  │     │
│  │  └──────────────────┘  └────────────────────┘  │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         File System Operations                     │   │
│  │  • Workflow directory scanning                      │   │
│  │  • Archive operations (Windows-compatible)         │   │
│  │  • .cursorignore pattern management                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. CleanupTool Extension

**File**: `tapps_agents/core/cleanup_tool.py`

**New Method**: `cleanup_workflow_docs()`

```python
def cleanup_workflow_docs(
    self,
    keep_latest: int = 5,
    retention_days: int = 30,
    archive_dir: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Clean up old workflow documentation directories.
    
    Algorithm:
    1. Scan docs/workflows/simple-mode/ for workflow directories
    2. Sort by modification time (newest first)
    3. Keep latest N workflows (always visible)
    4. Archive workflows older than retention_days
    5. Return summary of operations
    
    Returns:
        Dictionary with:
        - archived: int - Number of workflows archived
        - kept: int - Number of workflows kept
        - total_size_mb: float - Total size of archived workflows
        - dry_run: bool - Whether this was a dry run
    """
```

**Integration Points**:
- Uses `self.config.cleanup.workflow_docs` for default values
- Integrates with `cleanup_all()` method
- Uses `shutil.move()` or copy + delete for Windows compatibility

**Error Handling**:
- Graceful handling of missing directories
- Permission error handling
- Path validation to prevent directory traversal

---

### 2. Configuration Schema

**File**: `tapps_agents/core/config.py`

**New Class**: `WorkflowDocsCleanupConfig`

```python
class WorkflowDocsCleanupConfig(BaseModel):
    """Configuration for workflow documentation cleanup"""
    
    enabled: bool = Field(
        default=True,
        description="Enable workflow documentation cleanup"
    )
    keep_latest: int = Field(
        default=5,
        ge=1,
        description="Keep N most recent workflows visible"
    )
    retention_days: int = Field(
        default=30,
        ge=1,
        description="Archive workflows older than N days"
    )
    archive_enabled: bool = Field(
        default=True,
        description="Enable archival of old workflows"
    )
    archive_dir: Path = Field(
        default=Path(".tapps-agents/archives/workflows/"),
        description="Directory for archived workflows"
    )
    exclude_patterns: list[str] = Field(
        default_factory=list,
        description="Workflow IDs to never archive"
    )
```

**Integration**:
- Added to `CleanupConfig` class:
  ```python
  workflow_docs: WorkflowDocsCleanupConfig = Field(
      default_factory=WorkflowDocsCleanupConfig,
      description="Workflow documentation cleanup configuration"
  )
  ```

---

### 3. CLI Parser Extension

**File**: `tapps_agents/cli/parsers/top_level.py`

**New Subcommand**: `cleanup workflow-docs`

```python
# In cleanup_subparser group
workflow_docs_parser = cleanup_subparsers.add_parser(
    "workflow-docs",
    help="Clean up old workflow documentation directories"
)
workflow_docs_parser.add_argument(
    "--keep-latest",
    type=int,
    default=None,
    help="Keep N most recent workflows (default: from config)"
)
workflow_docs_parser.add_argument(
    "--retention-days",
    type=int,
    default=None,
    help="Archive workflows older than N days (default: from config)"
)
workflow_docs_parser.add_argument(
    "--archive",
    action="store_true",
    help="Enable archival (default: from config)"
)
workflow_docs_parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Preview changes without making them"
)
```

---

### 4. CLI Command Handler

**File**: `tapps_agents/cli/commands/top_level.py`

**New Function**: `handle_cleanup_workflow_docs_command()`

```python
def handle_cleanup_workflow_docs_command(args: object) -> None:
    """Handle 'cleanup workflow-docs' command"""
    from ...core.cleanup_tool import CleanupTool
    
    tool = CleanupTool()
    
    # Get config values or use command-line overrides
    config = tool.config.cleanup.workflow_docs
    keep_latest = getattr(args, "keep_latest", None) or config.keep_latest
    retention_days = getattr(args, "retention_days", None) or config.retention_days
    archive_enabled = getattr(args, "archive", False) or config.archive_enabled
    dry_run = getattr(args, "dry_run", False)
    
    # Execute cleanup
    results = tool.cleanup_workflow_docs(
        keep_latest=keep_latest,
        retention_days=retention_days,
        archive_dir=config.archive_dir if archive_enabled else None,
        dry_run=dry_run,
    )
    
    # Display results
    _print_workflow_cleanup_results(results)
```

---

### 5. Init Command Enhancement

**File**: `tapps_agents/cli/commands/top_level.py`

**New Function**: `_update_cursorignore_patterns()`

```python
def _update_cursorignore_patterns(project_root: Path) -> bool:
    """
    Update .cursorignore with TappsCodingAgents patterns.
    
    Returns:
        True if patterns were added, False if already present
    """
    cursorignore_path = project_root / ".cursorignore"
    
    # Patterns to add
    patterns_to_add = [
        ".tapps-agents/backups/",
        ".tapps-agents/archives/",
        ".tapps-agents/artifacts/",
    ]
    
    # Read existing file
    existing_content = ""
    if cursorignore_path.exists():
        existing_content = cursorignore_path.read_text(encoding="utf-8")
    
    # Check which patterns are missing
    missing_patterns = [
        p for p in patterns_to_add
        if p not in existing_content
    ]
    
    if not missing_patterns:
        return False  # All patterns already present
    
    # Append missing patterns
    new_content = existing_content
    if new_content and not new_content.endswith("\n"):
        new_content += "\n"
    
    new_content += "\n# TappsCodingAgents generated artifacts (auto-added)\n"
    for pattern in missing_patterns:
        new_content += f"{pattern}\n"
    
    cursorignore_path.write_text(new_content, encoding="utf-8")
    return True
```

**Integration**:
- Called from `handle_init_command()` after creating `.cursorignore` if needed

---

## Data Flow

### Workflow Cleanup Flow

```
User Command
    │
    ▼
CLI Parser (argparse)
    │
    ▼
Command Handler
    │
    ├─► Load Config (ProjectConfig)
    │       │
    │       └─► WorkflowDocsCleanupConfig
    │
    ▼
CleanupTool.cleanup_workflow_docs()
    │
    ├─► Scan docs/workflows/simple-mode/
    │       │
    │       └─► Find workflow directories
    │
    ├─► Sort by modification time
    │
    ├─► Apply retention policy
    │       │
    │       ├─► Keep latest N
    │       └─► Archive older than X days
    │
    └─► Return results
            │
            └─► Display summary
```

### Init Command Flow

```
User: tapps-agents init
    │
    ▼
handle_init_command()
    │
    ├─► Create directories
    ├─► Copy framework files
    ├─► Setup config
    │
    └─► _update_cursorignore_patterns()
            │
            ├─► Read .cursorignore
            ├─► Check for missing patterns
            └─► Append missing patterns
```

---

## Integration Patterns

### Pattern 1: Configuration-Driven Defaults

All cleanup operations use configuration defaults but allow CLI overrides:

```python
# Config provides defaults
config = tool.config.cleanup.workflow_docs

# CLI can override
keep_latest = args.keep_latest or config.keep_latest
```

### Pattern 2: Dry-Run by Default

All destructive operations support dry-run mode:

```python
if dry_run:
    print(f"Would archive: {workflow_dir}")
else:
    archive_workflow(workflow_dir)
```

### Pattern 3: Windows Compatibility

Archive operations work on Windows (no symlinks):

```python
if sys.platform == "win32":
    # Copy then delete (Windows-compatible)
    shutil.copytree(src, dest)
    shutil.rmtree(src)
else:
    # Move (Unix)
    shutil.move(src, dest)
```

---

## Error Handling Strategy

### 1. Missing Directories
- Check existence before operations
- Return empty results if directory doesn't exist
- Log warning but don't fail

### 2. Permission Errors
- Catch `PermissionError` exceptions
- Log error with context
- Continue with other operations
- Return partial results

### 3. Path Validation
- Validate all paths are within project root
- Prevent directory traversal attacks
- Use `Path.resolve()` to normalize paths

### 4. Archive Failures
- Try copy + delete on Windows
- Fallback to copy-only if delete fails
- Log warnings for partial failures

---

## Performance Considerations

### 1. Directory Scanning
- Use `pathlib.glob()` for efficient scanning
- Filter by pattern early (workflow ID format)
- Sort in-place to minimize memory

### 2. Archive Operations
- Batch operations where possible
- Progress reporting for large archives
- Estimate time remaining

### 3. Configuration Loading
- Cache config after first load
- Lazy load cleanup config section

---

## Security Considerations

### 1. Path Validation
- All paths validated against project root
- No absolute paths outside project
- Pattern matching for workflow IDs

### 2. Archive Directory
- Validate archive directory is within project
- Prevent archive to system directories
- Sanitize workflow IDs in archive paths

### 3. Permission Checks
- Check read/write permissions before operations
- Handle permission errors gracefully

---

## Testing Strategy

### Unit Tests
- `CleanupTool.cleanup_workflow_docs()` with various scenarios
- Configuration schema validation
- Path validation logic
- Archive operation logic

### Integration Tests
- End-to-end CLI command execution
- Config loading and defaults
- `.cursorignore` pattern updates
- Archive/restore workflows

### Manual Testing
- Test on Windows and Unix
- Test with various workflow directory counts
- Test dry-run mode
- Test error scenarios

---

## Migration Path

### For Existing Projects

1. Run `tapps-agents init --update-cursorignore` (if flag added)
2. Or manually add patterns to `.cursorignore`
3. Update `config.yaml` with cleanup settings (optional)
4. Run `tapps-agents cleanup workflow-docs --dry-run` to preview
5. Run cleanup with `--archive` to preserve history

---

## Next Steps

Proceed to Step 4: Component Design Specifications for detailed API design and implementation details.
