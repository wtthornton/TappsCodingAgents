---
title: Coding Standards
version: 1.0.0
status: active
last_updated: 2026-02-06
tags: [architecture, coding-standards, style-guide]
---

# Coding Standards

This document defines the coding standards and conventions for TappsCodingAgents.

## Python Style Guide

### PEP 8 Compliance

- **Follow PEP 8** style guide
- **Maximum line length**: 88 characters (matches Black and Ruff configuration)
- **Use ruff format** or **black** for formatting (both configured to 88 characters)

### Type Hints

**Always use type hints for all function signatures:**

```python
from pathlib import Path
from typing import Any

def process_file(file_path: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
    """Process a file and return results."""
    pass
```

**Type Hint Requirements:**
- All public functions must have type hints
- All class methods must have type hints
- Use `T | None` for nullable types (Python 3.12+ native syntax)
- Use `T | U` for union types (Python 3.12+ native syntax)
- Use lowercase generics: `dict`, `list`, `tuple`, `set` (not `Dict`, `List`, etc.)
- Use `Any` sparingly (prefer specific types)

### Docstrings

**Use Google-style docstrings:**

```python
def calculate_score(code: str, weights: dict[str, float]) -> float:
    """
    Calculate code quality score.
    
    Args:
        code: Source code to analyze
        weights: Scoring weights for different metrics
    
    Returns:
        Overall quality score (0-100)
    
    Raises:
        ValueError: If weights don't sum to 1.0
    """
    pass
```

**Docstring Requirements:**
- All public functions must have docstrings
- All classes must have docstrings
- Include Args, Returns, and Raises sections
- Use clear, concise descriptions

## Code Organization

### File Structure

- **One class per file** (when possible)
- **Single responsibility** principle
- **DRY** (Don't Repeat Yourself)
- **Clear naming** conventions

### Module Organization

- Group related functionality together
- Use `__init__.py` for package-level exports
- Keep modules focused and cohesive

### Naming Conventions

**Functions and Variables:**
- Use `snake_case` for functions and variables
- Use descriptive names: `calculate_total_score()` not `calc()`
- Boolean variables: `is_valid`, `has_error`, `can_execute`

**Classes:**
- Use `PascalCase` for class names
- Use descriptive names: `WorkflowExecutor` not `Executor`

**Constants:**
- Use `UPPER_SNAKE_CASE` for constants
- Example: `MAX_RETRIES`, `DEFAULT_TIMEOUT`

**Private Members:**
- Use single underscore prefix: `_internal_method()`
- Use double underscore prefix for name mangling: `__private_attribute`

## Error Handling

### Exception Types

- Use specific exception types
- Create custom exceptions when appropriate
- Document exceptions in docstrings

**Example:**
```python
class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails."""
    pass

def execute_workflow(workflow: Workflow) -> Result:
    """
    Execute a workflow.
    
    Raises:
        WorkflowExecutionError: If workflow execution fails
        ValueError: If workflow is invalid
    """
    if not workflow.is_valid():
        raise ValueError("Invalid workflow")
    # ...
```

### Error Messages

- Use clear, actionable error messages
- Include context (file path, line number, etc.)
- Avoid exposing internal implementation details

## Code Quality

### Complexity

- Keep functions focused and single-purpose
- Maximum cyclomatic complexity: 10 (prefer lower)
- Refactor complex functions into smaller ones

### Dependencies

- Minimize dependencies between modules
- Use dependency injection when appropriate
- Avoid circular dependencies

### Testing

- Write tests for all new functionality
- Aim for 80%+ code coverage
- Use descriptive test names: `test_calculate_score_returns_sum_of_weights()`

## Formatting Tools

### Ruff (Primary)

**Configuration**: `pyproject.toml`

```bash
# Format code
ruff format .

# Lint code
ruff check .
```

### Black (Alternative)

**Configuration**: `pyproject.toml`

```bash
# Format code
black .
```

### Type Checking

**mypy Configuration**: `pyproject.toml`

```bash
# Type check
mypy tapps_agents/
```

## Windows Compatibility

### Encoding Requirements

**All Python scripts MUST:**

1. **Set UTF-8 encoding for console output:**
```python
import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        # Python < 3.7 - use environment variable only
        pass
```

2. **Always specify encoding when opening files:**
```python
# ✅ CORRECT - Always specify encoding
with open("file.txt", "r", encoding="utf-8") as f:
    content = f.read()

# ❌ WRONG - Relies on system default (CP1252 on Windows)
with open("file.txt", "r") as f:
    content = f.read()
```

3. **Specify encoding for subprocess output:**
```python
# ✅ CORRECT - Specify encoding and error handling
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",  # Replace invalid characters instead of failing
)
```

## Async/Await Patterns

### Async Functions

- Use `async def` for async functions
- Use `await` for async operations
- Use `asyncio.TaskGroup` for structured concurrency (Python 3.11+)

**Example:**
```python
async def process_files(files: List[Path]) -> List[Result]:
    """Process multiple files concurrently."""
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(process_file(f)) for f in files]
    return [task.result() for task in tasks]
```

### Context Managers

- Use `async with` for async context managers
- Implement `__aenter__` and `__aexit__` for custom async context managers

## Documentation Standards

### Inline Comments

- Use comments to explain "why", not "what"
- Keep comments up-to-date with code
- Remove commented-out code before committing

### Type Annotations

- Use type annotations instead of comments when possible
- Use `typing` module for complex types
- Use `typing_extensions` for newer type features if needed

## Related Documentation

- **Contributing Guide**: `CONTRIBUTING.md`
- **Architecture Overview**: `docs/ARCHITECTURE.md`
- **Test Stack**: `docs/test-stack.md`

---

**Last Updated:** 2026-02-06
**Maintained By:** TappsCodingAgents Team
