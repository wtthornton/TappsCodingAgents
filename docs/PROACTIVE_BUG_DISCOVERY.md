# Proactive Bug Discovery

## Overview

The `ProactiveBugFinder` class provides proactive bug discovery without requiring test failures. It analyzes source code files using the Reviewer Agent to find potential bugs, security vulnerabilities, type issues, and edge cases.

## Usage

```python
from tapps_agents.continuous_bug_fix import ProactiveBugFinder, BugInfo
from pathlib import Path

# Initialize finder
finder = ProactiveBugFinder(project_root=Path.cwd())

# Find bugs
bugs = await finder.find_bugs(
    target_path="src/",  # Directory or file to analyze
    max_bugs=20,         # Maximum number of bugs to find
    file_pattern="**/*.py"  # Glob pattern for files
)

# Process bugs
for bug in bugs:
    print(f"Bug in {bug.file_path}: {bug.error_message}")
```

## Integration with Continuous Bug Fix

The `ProactiveBugFinder` returns `BugInfo` objects that are compatible with the existing `BugFixCoordinator` and `ContinuousBugFixer` infrastructure. This allows proactive bug discovery to be integrated into automated fixing workflows.

## Implementation Details

- Uses `ReviewerAgent` to analyze code files
- Extracts bugs from review scores, issues, and feedback
- Filters out test files and build artifacts
- Limits analysis to prevent timeouts (max 50 files per run)
- Returns up to `max_bugs` BugInfo objects

## Future Enhancements

- Integration with `ContinuousBugFixer` for automated overnight execution
- CLI command for proactive bug discovery
- Batch processing of large codebases
- Custom bug detection patterns
