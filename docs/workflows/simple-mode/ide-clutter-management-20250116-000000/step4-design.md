# Step 4: Component Design Specifications - IDE Clutter Management Implementation

**Workflow ID**: `ide-clutter-management-20250116-000000`  
**Step**: 4 - Component Design  
**Date**: 2025-01-16

---

## API Specifications

### 1. CleanupTool.cleanup_workflow_docs()

**Signature**:
```python
def cleanup_workflow_docs(
    self,
    keep_latest: int = 5,
    retention_days: int = 30,
    archive_dir: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
```

**Parameters**:
- `keep_latest` (int): Number of most recent workflows to keep visible (default: 5)
- `retention_days` (int): Archive workflows older than this many days (default: 30)
- `archive_dir` (Path | None): Directory for archived workflows. If None, archival disabled.
- `dry_run` (bool): If True, preview changes without making them (default: False)

**Returns**:
```python
{
    "archived": int,           # Number of workflows archived
    "kept": int,               # Number of workflows kept visible
    "total_size_mb": float,    # Total size of archived workflows in MB
    "archived_workflows": list[str],  # List of archived workflow IDs
    "kept_workflows": list[str],      # List of kept workflow IDs
    "dry_run": bool,           # Whether this was a dry run
    "errors": list[str],        # List of error messages (if any)
}
```

**Algorithm**:
1. Locate `docs/workflows/simple-mode/` directory
2. Scan for workflow directories (pattern: `*-*-*` or check for `step*.md` files)
3. Filter out non-workflow directories (e.g., `latest`, `README.md`)
4. Sort directories by modification time (newest first)
5. Keep latest N workflows (always visible)
6. For remaining workflows:
   - Check if older than `retention_days`
   - If archive enabled and old enough, move to archive directory
   - If archive disabled, skip (keep visible)
7. Return summary dictionary

**Error Handling**:
- Missing `docs/workflows/simple-mode/` directory → Return empty results
- Permission errors → Log error, continue with other operations
- Archive failures → Log error, continue with next workflow

**Example Usage**:
```python
tool = CleanupTool()
results = tool.cleanup_workflow_docs(
    keep_latest=5,
    retention_days=30,
    archive_dir=Path(".tapps-agents/archives/workflows/"),
    dry_run=False,
)
print(f"Archived {results['archived']} workflows")
print(f"Kept {results['kept']} workflows visible")
```

---

### 2. WorkflowDocsCleanupConfig

**Class Definition**:
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
        le=100,
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
        description="Directory for archived workflows (relative to project root)"
    )
    exclude_patterns: list[str] = Field(
        default_factory=list,
        description="Workflow IDs or patterns to never archive"
    )
```

**Validation Rules**:
- `keep_latest`: Must be between 1 and 100
- `retention_days`: Must be >= 1
- `archive_dir`: Must be a valid path (relative or absolute)

**Default Configuration** (YAML):
```yaml
cleanup:
  workflow_docs:
    enabled: true
    keep_latest: 5
    retention_days: 30
    archive_enabled: true
    archive_dir: ".tapps-agents/archives/workflows/"
    exclude_patterns: []
```

---

### 3. CLI Command: `cleanup workflow-docs`

**Command Syntax**:
```bash
tapps-agents cleanup workflow-docs [OPTIONS]
```

**Options**:
- `--keep-latest N`: Keep N most recent workflows (overrides config)
- `--retention-days N`: Archive workflows older than N days (overrides config)
- `--archive`: Enable archival (overrides config)
- `--no-archive`: Disable archival (overrides config)
- `--dry-run`: Preview changes without making them

**Examples**:
```bash
# Preview cleanup (dry-run)
tapps-agents cleanup workflow-docs --dry-run

# Cleanup with defaults from config
tapps-agents cleanup workflow-docs

# Custom retention policy
tapps-agents cleanup workflow-docs --keep-latest 10 --retention-days 60

# Cleanup without archiving (delete old workflows)
tapps-agents cleanup workflow-docs --no-archive
```

**Output Format**:
```
Cleaning up workflow documentation...

Configuration:
  Keep latest: 5 workflows
  Retention: 30 days
  Archive enabled: Yes
  Archive directory: .tapps-agents/archives/workflows/

Results:
  ✅ Kept 5 workflows visible
  📦 Archived 12 workflows (45.2 MB)
  ⚠️  Skipped 2 workflows (excluded patterns)

Archived workflows:
  - automation-system-20250101-000000
  - build-md-files-fix-20251231-013115
  ...

Kept workflows:
  - ide-clutter-management-20250116-000000
  - phase3-documentation-20250116-000000
  ...
```

---

### 4. Init Command Enhancement: `_update_cursorignore_patterns()`

**Function Signature**:
```python
def _update_cursorignore_patterns(
    project_root: Path,
    force: bool = False,
) -> dict[str, Any]:
    """
    Update .cursorignore with TappsCodingAgents patterns.
    
    Args:
        project_root: Project root directory
        force: If True, update even if patterns exist
        
    Returns:
        Dictionary with update results:
        {
            "updated": bool,
            "patterns_added": list[str],
            "patterns_existing": list[str],
        }
    """
```

**Patterns to Add**:
```python
PATTERNS_TO_ADD = [
    ".tapps-agents/backups/",
    ".tapps-agents/archives/",
    ".tapps-agents/artifacts/",
]
```

**Algorithm**:
1. Read existing `.cursorignore` file (if exists)
2. Check which patterns are missing
3. If missing patterns found:
   - Append section header comment
   - Append missing patterns
   - Write updated file
4. Return update results

**Preservation Logic**:
- Never overwrite existing content
- Append to end of file
- Add comment section header
- Preserve existing formatting

**Example Output**:
```diff
# Existing .cursorignore content
.venv/
__pycache__/

+# TappsCodingAgents generated artifacts (auto-added)
+.tapps-agents/backups/
+.tapps-agents/archives/
+.tapps-agents/artifacts/
```

---

### 5. CleanupTool.cleanup_all() Extension

**Updated Signature**:
```python
def cleanup_all(
    self,
    worktree_days: int = 7,
    analytics_days: int = 90,
    cache_days: int = 30,
    workflow_keep_latest: int | None = None,      # NEW
    workflow_retention_days: int | None = None,  # NEW
    workflow_archive: bool | None = None,        # NEW
    dry_run: bool = False,
) -> dict[str, Any]:
```

**New Parameters**:
- `workflow_keep_latest`: Keep N most recent workflows (None = use config)
- `workflow_retention_days`: Archive workflows older than N days (None = use config)
- `workflow_archive`: Enable archival (None = use config)

**Updated Return Value**:
```python
{
    "worktrees": {...},
    "analytics": {...},
    "cache": {...},
    "workflow_docs": {        # NEW
        "archived": int,
        "kept": int,
        "total_size_mb": float,
        ...
    },
    "summary": {
        "total_removed": int,
        "total_size_mb": float,
        "dry_run": bool,
    },
}
```

---

## Data Structures

### Workflow Directory Structure

```
docs/workflows/simple-mode/
├── {workflow-id-1}/          # Workflow directory
│   ├── step1-enhanced-prompt.md
│   ├── step2-user-stories.md
│   ├── step3-architecture.md
│   └── ...
├── {workflow-id-2}/
│   └── ...
├── latest/                   # Symlink/pointer (excluded from cleanup)
└── README.md                 # Index file (excluded from cleanup)
```

### Archive Directory Structure

```
.tapps-agents/archives/workflows/
├── {workflow-id-1}/         # Archived workflow
│   ├── step1-enhanced-prompt.md
│   └── ...
├── {workflow-id-2}/
│   └── ...
└── .archive-metadata.json    # Optional: Archive index
```

---

## Implementation Details

### Workflow Directory Detection

**Pattern Matching**:
```python
def is_workflow_directory(path: Path) -> bool:
    """Check if directory is a workflow directory"""
    # Exclude special directories
    if path.name in ["latest", "README.md"]:
        return False
    
    # Check for workflow ID pattern: {name}-{timestamp}
    # Pattern: contains hyphen and timestamp-like suffix
    if "-" in path.name:
        parts = path.name.split("-")
        if len(parts) >= 2:
            # Check if last part looks like timestamp (YYYYMMDD-HHMMSS)
            last_part = parts[-1]
            if len(last_part) == 13 and last_part.replace("-", "").isdigit():
                return True
    
    # Fallback: Check for step files
    step_files = list(path.glob("step*.md"))
    return len(step_files) > 0
```

### Archive Operation (Windows-Compatible)

```python
def archive_workflow(
    source_dir: Path,
    archive_dir: Path,
    dry_run: bool = False,
) -> bool:
    """Archive a workflow directory (Windows-compatible)"""
    import sys
    import shutil
    
    dest_dir = archive_dir / source_dir.name
    
    if dry_run:
        print(f"Would archive: {source_dir} -> {dest_dir}")
        return True
    
    try:
        # Ensure archive directory exists
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        if sys.platform == "win32":
            # Windows: Copy then delete (more reliable than move)
            shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
            shutil.rmtree(source_dir)
        else:
            # Unix: Move (atomic operation)
            shutil.move(str(source_dir), str(dest_dir))
        
        return True
    except Exception as e:
        logger.error(f"Failed to archive {source_dir}: {e}")
        return False
```

### Size Calculation

```python
def calculate_directory_size(path: Path) -> int:
    """Calculate total size of directory in bytes"""
    total_size = 0
    try:
        for file_path in path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
    except Exception as e:
        logger.warning(f"Error calculating size for {path}: {e}")
    return total_size
```

---

## Error Handling Specifications

### Error Types

1. **MissingDirectoryError**: `docs/workflows/simple-mode/` doesn't exist
   - **Handling**: Return empty results, log info message
   - **User Impact**: None (expected for new projects)

2. **PermissionError**: Cannot read/write directories
   - **Handling**: Log error, skip problematic workflow, continue
   - **User Impact**: Partial cleanup, error message shown

3. **ArchiveError**: Archive operation failed
   - **Handling**: Log error, continue with next workflow
   - **User Impact**: Some workflows not archived, error in results

4. **PathValidationError**: Invalid path detected
   - **Handling**: Reject operation, return error
   - **User Impact**: Operation aborted, security maintained

---

## Testing Specifications

### Unit Test Cases

1. **cleanup_workflow_docs()**:
   - Test with empty directory
   - Test with 3 workflows (all kept)
   - Test with 10 workflows (5 kept, 5 archived)
   - Test with dry-run mode
   - Test with archive disabled
   - Test with custom retention days
   - Test with exclude patterns
   - Test error handling (permission errors)

2. **WorkflowDocsCleanupConfig**:
   - Test default values
   - Test validation (keep_latest bounds)
   - Test path validation
   - Test YAML loading

3. **_update_cursorignore_patterns()**:
   - Test with missing file
   - Test with existing file (no patterns)
   - Test with existing file (some patterns)
   - Test with existing file (all patterns)
   - Test pattern preservation

### Integration Test Cases

1. **CLI Command**:
   - Test `cleanup workflow-docs --dry-run`
   - Test `cleanup workflow-docs` with defaults
   - Test `cleanup workflow-docs` with overrides
   - Test error handling

2. **Init Command**:
   - Test `init` updates `.cursorignore`
   - Test idempotency (run twice)
   - Test pattern preservation

---

## Performance Specifications

### Target Performance

- **Directory Scanning**: < 1 second for 100 workflows
- **Archive Operation**: < 5 seconds per workflow (depends on size)
- **Total Cleanup**: < 30 seconds for typical project (50 workflows)

### Optimization Strategies

1. **Lazy Evaluation**: Only scan directories when needed
2. **Batch Operations**: Process multiple workflows in batch
3. **Progress Reporting**: Show progress for long operations
4. **Early Exit**: Stop if error threshold exceeded

---

## Security Specifications

### Path Validation

```python
def validate_path(path: Path, project_root: Path) -> bool:
    """Validate path is within project root"""
    try:
        resolved_path = path.resolve()
        resolved_root = project_root.resolve()
        return resolved_path.is_relative_to(resolved_root)
    except Exception:
        return False
```

### Input Sanitization

- Workflow IDs: Validate format (alphanumeric, hyphens, underscores)
- Archive paths: Validate against project root
- Pattern matching: Use safe glob patterns

---

## Next Steps

Proceed to Step 5: Implementation to write the actual code following these specifications.
