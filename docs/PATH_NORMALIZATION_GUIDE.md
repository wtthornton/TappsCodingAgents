# Path Normalization Guide

**Date:** 2026-01-20  
**Purpose:** Guide for using path normalization utilities in TappsCodingAgents

## Overview

The path normalization utilities (`tapps_agents.core.path_normalizer`) provide cross-platform path handling, especially for Windows absolute paths that can cause CLI command failures.

## Problem

On Windows, absolute paths like `c:/cursor/TappsCodingAgents/src/file.py` can cause CLI commands to fail with errors like:

```
Error: Command failed to spawn: path should be a `path.relative()`d string, but got "c:/cursor/TappsCodingAgents"
```

## Solution

The path normalizer automatically converts absolute paths to relative paths based on the project root, ensuring CLI commands work correctly on all platforms.

## Functions

### `normalize_path(path, project_root)`

Normalizes a path to relative format for CLI commands.

**Parameters:**
- `path` (str | Path): Path to normalize (can be absolute or relative)
- `project_root` (Path): Project root directory for relative path calculation

**Returns:**
- `str`: Normalized relative path string, or absolute path string if outside project root

**Examples:**

```python
from pathlib import Path
from tapps_agents.core.path_normalizer import normalize_path

# Project root
project_root = Path("c:/cursor/TappsCodingAgents")

# Windows absolute path → relative path
result = normalize_path("c:/cursor/TappsCodingAgents/src/file.py", project_root)
# Returns: "src/file.py"

# Already relative path → unchanged
result = normalize_path("src/file.py", project_root)
# Returns: "src/file.py"

# Path outside project root → returns absolute path with warning
result = normalize_path("c:/other/project/file.py", project_root)
# Returns: "c:/other/project/file.py" (with warning logged)
```

### `ensure_relative_path(path, project_root)`

Ensures path is relative to project root, raising error if outside.

**Parameters:**
- `path` (str | Path): Path to normalize
- `project_root` (Path): Project root directory

**Returns:**
- `str`: Relative path string

**Raises:**
- `ValueError`: If path is outside project root

**Examples:**

```python
from tapps_agents.core.path_normalizer import ensure_relative_path

# Valid relative path
result = ensure_relative_path("src/file.py", project_root)
# Returns: "src/file.py"

# Absolute path within project
result = ensure_relative_path("c:/cursor/TappsCodingAgents/src/file.py", project_root)
# Returns: "src/file.py"

# Path outside project → raises ValueError
try:
    ensure_relative_path("c:/other/file.py", project_root)
except ValueError as e:
    print(f"Error: {e}")
    # Error: Path c:/other/file.py is outside project root...
```

### `normalize_for_cli(path, project_root)`

Normalizes path for CLI command execution (most permissive).

**Parameters:**
- `path` (str | Path): Path to normalize
- `project_root` (Path): Project root directory

**Returns:**
- `str`: CLI-safe path string (uses forward slashes on all platforms)

**Examples:**

```python
from tapps_agents.core.path_normalizer import normalize_for_cli

# Windows path with backslashes → forward slashes
result = normalize_for_cli("c:\\cursor\\TappsCodingAgents\\src\\file.py", project_root)
# Returns: "src/file.py" (forward slashes)

# Already relative → unchanged
result = normalize_for_cli("src/file.py", project_root)
# Returns: "src/file.py"
```

### `normalize_project_root(project_root)`

Normalizes project root path for consistent handling.

**Parameters:**
- `project_root` (str | Path): Project root path (can be absolute or relative)

**Returns:**
- `Path`: Resolved Path object

**Examples:**

```python
from tapps_agents.core.path_normalizer import normalize_project_root

# Absolute path → resolved
result = normalize_project_root("c:/cursor/TappsCodingAgents")
# Returns: Path("c:/cursor/TappsCodingAgents") (resolved)

# Relative path → resolved to absolute
result = normalize_project_root(".")
# Returns: Path("/current/working/directory") (resolved)
```

## Usage in CLI Commands

### Simple Mode Build Command

The Simple Mode build handler automatically normalizes paths:

```python
from tapps_agents.core.path_normalizer import normalize_for_cli, normalize_project_root

def handle_simple_mode_build(args: object) -> None:
    project_root = normalize_project_root(Path.cwd())
    
    target_file = getattr(args, "file", None)
    if target_file:
        # Automatically normalize Windows absolute paths
        target_file = normalize_for_cli(target_file, project_root)
    
    # Use normalized path in workflow
    # ...
```

### Workflow Executor

The workflow executor normalizes paths before passing to agents:

```python
def _get_step_params(self, step: WorkflowStep, target_path: Path | None) -> dict[str, Any]:
    params: dict[str, Any] = {}
    
    if target_path:
        try:
            # Try relative path first
            params["target_file"] = str(target_path.relative_to(self.project_root))
        except ValueError:
            # Fallback to path normalizer
            from ...core.path_normalizer import normalize_for_cli
            params["target_file"] = normalize_for_cli(target_path, self.project_root)
    
    return params
```

## Error Handling

### Path Outside Project Root

When a path is outside the project root:

```python
# normalize_path() returns absolute path with warning
result = normalize_path("c:/other/project/file.py", project_root)
# Returns: "c:/other/project/file.py"
# Logs: WARNING - Path is outside project root

# ensure_relative_path() raises ValueError
try:
    ensure_relative_path("c:/other/project/file.py", project_root)
except ValueError as e:
    # Handle error
    pass
```

### Empty Paths

Empty paths are handled gracefully:

```python
result = normalize_path("", project_root)
# Returns: ""
```

## Best Practices

1. **Use `normalize_for_cli()` for CLI commands** - Most permissive, handles all edge cases
2. **Use `ensure_relative_path()` when strict validation needed** - Raises error for paths outside project
3. **Normalize project root at start** - Use `normalize_project_root()` for consistent handling
4. **Handle errors gracefully** - Path normalization can fail for edge cases

## Platform-Specific Notes

### Windows

- Absolute paths use drive letters: `c:/path/to/file.py`
- Backslashes are converted to forward slashes in `normalize_for_cli()`
- Path normalization is especially important on Windows

### Linux/macOS

- Absolute paths start with `/`: `/path/to/file.py`
- Forward slashes are standard
- Path normalization still works but less critical

## Testing

Unit tests are available in `tests/unit/core/test_path_normalizer.py`:

```bash
# Run path normalizer tests
pytest tests/unit/core/test_path_normalizer.py -v

# Run with coverage
pytest tests/unit/core/test_path_normalizer.py --cov=tapps_agents.core.path_normalizer
```

## Related Documentation

- `docs/CLI_PATH_HANDLING_FIX_IMPLEMENTATION_PLAN.md` - Implementation plan
- `docs/CLI_PATH_HANDLING_FIX_IMPLEMENTATION_SUMMARY.md` - Implementation summary
- `tapps_agents/core/path_normalizer.py` - Source code with docstrings

## Troubleshooting

### Path Still Fails After Normalization

1. Check that project root is correct
2. Verify path exists and is accessible
3. Check for symlinks or special characters
4. Review error logs for warnings

### Path Outside Project Root

If you need to access files outside the project root:
- Use `normalize_path()` (returns absolute path)
- Or restructure to keep files within project root
- Or use `ensure_relative_path()` and handle ValueError

### Windows Path Issues

If Windows paths still cause issues:
- Ensure using `normalize_for_cli()` (converts backslashes)
- Check that project root is normalized
- Verify path doesn't contain invalid characters

---

**Last Updated:** 2026-01-20  
**Maintainer:** TappsCodingAgents Team
