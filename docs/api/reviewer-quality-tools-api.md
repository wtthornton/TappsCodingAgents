# API Design Specification: ReviewerAgent Quality Tool Improvements

**Version**: 1.0.0
**Date**: 2026-01-29
**Status**: Design Complete
**Target**: Python 3.9+

---

## Table of Contents

1. [Data Models](#data-models)
2. [AutoFixModule API](#autofixmodule-api)
3. [BackupManager API](#backupmanager-api)
4. [ValidationManager API](#validationmanager-api)
5. [RestoreManager API](#restoremanager-api)
6. [ScopedMypyExecutor API](#scopedmypyexecutor-api)
7. [RuffGroupingParser API](#ruffgroupingparser-api)
8. [GroupedRenderer API](#groupedrenderer-api)
9. [Configuration Models](#configuration-models)
10. [Error Handling Contracts](#error-handling-contracts)
11. [Usage Examples](#usage-examples)

---

## 1. Data Models

All data models use frozen dataclasses for immutability and thread safety.

### BackupMetadata

```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass(frozen=True)
class BackupMetadata:
    """
    Metadata for file backup operations.

    Attributes:
        original_path: Path to original file
        backup_path: Path to backup file
        timestamp: When backup was created
        checksum: SHA-256 hash of original file
        size_bytes: Size of original file in bytes

    Example:
        >>> metadata = BackupMetadata(
        ...     original_path=Path("src/module.py"),
        ...     backup_path=Path(".tapps-agents/backups/module.py.2026-01-29_143022"),
        ...     timestamp=datetime.now(),
        ...     checksum="a1b2c3d4...",
        ...     size_bytes=4096
        ... )
    """
    original_path: Path
    backup_path: Path
    timestamp: datetime
    checksum: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "original_path": str(self.original_path),
            "backup_path": str(self.backup_path),
            "timestamp": self.timestamp.isoformat(),
            "checksum": self.checksum,
            "size_bytes": self.size_bytes
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackupMetadata":
        """Create from dictionary."""
        return cls(
            original_path=Path(data["original_path"]),
            backup_path=Path(data["backup_path"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            checksum=data["checksum"],
            size_bytes=data["size_bytes"]
        )
```

### AutoFixResult

```python
@dataclass(frozen=True)
class AutoFixResult:
    """
    Result of auto-fix operation.

    Attributes:
        success: Whether auto-fix succeeded
        fixes_applied: Number of issues fixed
        validation_passed: Whether validation passed after fixing
        backup_created: Whether backup was created
        backup_metadata: Backup metadata if created
        errors: List of error messages
        warnings: List of warning messages
        duration_seconds: Time taken for operation

    Example:
        >>> result = AutoFixResult(
        ...     success=True,
        ...     fixes_applied=5,
        ...     validation_passed=True,
        ...     backup_created=True,
        ...     backup_metadata=metadata,
        ...     errors=[],
        ...     warnings=[],
        ...     duration_seconds=2.5
        ... )
    """
    success: bool
    fixes_applied: int
    validation_passed: bool
    backup_created: bool
    backup_metadata: BackupMetadata | None
    errors: list[str]
    warnings: list[str]
    duration_seconds: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "fixes_applied": self.fixes_applied,
            "validation_passed": self.validation_passed,
            "backup_created": self.backup_created,
            "backup_metadata": self.backup_metadata.to_dict() if self.backup_metadata else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "duration_seconds": self.duration_seconds
        }
```

### ValidationResult

```python
@dataclass(frozen=True)
class ValidationResult:
    """
    Result of validation checks.

    Attributes:
        passed: Overall validation passed
        syntax_valid: Syntax validation passed
        imports_valid: Import validation passed
        linting_valid: Linting validation passed
        errors: List of validation errors
        warnings: List of validation warnings

    Example:
        >>> result = ValidationResult(
        ...     passed=True,
        ...     syntax_valid=True,
        ...     imports_valid=True,
        ...     linting_valid=True,
        ...     errors=[],
        ...     warnings=["Line too long on line 42"]
        ... )
    """
    passed: bool
    syntax_valid: bool
    imports_valid: bool
    linting_valid: bool
    errors: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "passed": self.passed,
            "syntax_valid": self.syntax_valid,
            "imports_valid": self.imports_valid,
            "linting_valid": self.linting_valid,
            "errors": self.errors,
            "warnings": self.warnings
        }
```

### MypyIssue

```python
@dataclass(frozen=True)
class MypyIssue:
    """
    Single mypy type checking issue.

    Attributes:
        file_path: Path to file with issue
        line: Line number
        column: Column number
        severity: Issue severity (error, warning, note)
        message: Issue message
        error_code: Mypy error code (e.g., "arg-type")

    Example:
        >>> issue = MypyIssue(
        ...     file_path=Path("src/module.py"),
        ...     line=42,
        ...     column=10,
        ...     severity="error",
        ...     message="Argument 1 has incompatible type",
        ...     error_code="arg-type"
        ... )
    """
    file_path: Path
    line: int
    column: int
    severity: str
    message: str
    error_code: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_path": str(self.file_path),
            "line": self.line,
            "column": self.column,
            "severity": self.severity,
            "message": self.message,
            "error_code": self.error_code
        }
```

### MypyResult

```python
@dataclass(frozen=True)
class MypyResult:
    """
    Result of scoped mypy execution.

    Attributes:
        issues: List of type checking issues
        duration_seconds: Execution time
        files_checked: Number of files checked
        success: Whether mypy completed successfully

    Example:
        >>> result = MypyResult(
        ...     issues=[issue1, issue2],
        ...     duration_seconds=3.5,
        ...     files_checked=1,
        ...     success=True
        ... )
    """
    issues: list[MypyIssue]
    duration_seconds: float
    files_checked: int
    success: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "issues": [issue.to_dict() for issue in self.issues],
            "duration_seconds": self.duration_seconds,
            "files_checked": self.files_checked,
            "success": self.success
        }
```

### RuffIssue

```python
@dataclass(frozen=True)
class RuffIssue:
    """
    Single Ruff linting issue.

    Attributes:
        code: Ruff error code (e.g., "F401")
        message: Issue message
        line: Line number
        column: Column number
        severity: Issue severity (error, warning, info)
        fixable: Whether issue is auto-fixable

    Example:
        >>> issue = RuffIssue(
        ...     code="F401",
        ...     message="'os' imported but unused",
        ...     line=5,
        ...     column=1,
        ...     severity="error",
        ...     fixable=True
        ... )
    """
    code: str
    message: str
    line: int
    column: int
    severity: str
    fixable: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "code": self.code,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "severity": self.severity,
            "fixable": self.fixable
        }
```

### GroupedRuffIssues

```python
@dataclass(frozen=True)
class GroupedRuffIssues:
    """
    Grouped Ruff issues by error code.

    Attributes:
        groups: Dictionary mapping error code to list of issues
        total_issues: Total number of issues
        unique_codes: Number of unique error codes
        severity_summary: Count of issues by severity
        fixable_count: Number of auto-fixable issues

    Example:
        >>> grouped = GroupedRuffIssues(
        ...     groups={"F401": [issue1, issue2], "E501": [issue3]},
        ...     total_issues=3,
        ...     unique_codes=2,
        ...     severity_summary={"error": 3},
        ...     fixable_count=2
        ... )
    """
    groups: dict[str, list[RuffIssue]]
    total_issues: int
    unique_codes: int
    severity_summary: dict[str, int]
    fixable_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "groups": {
                code: [issue.to_dict() for issue in issues]
                for code, issues in self.groups.items()
            },
            "total_issues": self.total_issues,
            "unique_codes": self.unique_codes,
            "severity_summary": self.severity_summary,
            "fixable_count": self.fixable_count
        }
```

---

## 2. AutoFixModule API

Main orchestrator for auto-fix operations.

```python
from pathlib import Path
from typing import Any
import logging

class AutoFixModule:
    """
    Auto-fix module for ImplementerAgent.

    Orchestrates backup → fix → validate → restore workflow.
    Integrates with Ruff for auto-fixes.

    Thread-safe: Yes (immutable results, no shared state)
    Async: Yes (uses async subprocess)

    Example:
        >>> module = AutoFixModule(config)
        >>> result = await module.auto_fix(Path("src/module.py"))
        >>> if result.success:
        ...     print(f"Applied {result.fixes_applied} fixes")
    """

    def __init__(
        self,
        config: AutoFixConfig,
        backup_manager: BackupManager | None = None,
        validation_manager: ValidationManager | None = None,
        restore_manager: RestoreManager | None = None
    ):
        """
        Initialize AutoFixModule.

        Args:
            config: Auto-fix configuration
            backup_manager: Optional custom backup manager
            validation_manager: Optional custom validation manager
            restore_manager: Optional custom restore manager

        Raises:
            ValueError: If config is invalid
        """
        self.config = config
        self.backup_manager = backup_manager or BackupManager(config)
        self.validation_manager = validation_manager or ValidationManager(config)
        self.restore_manager = restore_manager or RestoreManager(config)
        self.logger = logging.getLogger(__name__)

    async def auto_fix(
        self,
        file_path: Path,
        *,
        create_backup: bool = True,
        timeout: int | None = None
    ) -> AutoFixResult:
        """
        Apply auto-fixes to file with validation and rollback.

        Workflow:
        1. Validate file path (security check)
        2. Create backup (if enabled)
        3. Run `ruff check --fix`
        4. Validate fixes (syntax, imports, linting)
        5. Rollback if validation fails
        6. Return result

        Args:
            file_path: Path to file to auto-fix
            create_backup: Whether to create backup before fixing (default: True)
            timeout: Optional timeout in seconds (default: from config)

        Returns:
            AutoFixResult with success status and metadata

        Raises:
            Never raises - returns failure result instead

        Performance:
            - Target: <5 seconds for files <1000 lines
            - Backup: <1 second
            - Fix: <3 seconds
            - Validation: <1 second

        Security:
            - Validates file path is within project
            - Uses subprocess with list args (no shell injection)
            - Creates backup with restrictive permissions (0o600)

        Example:
            >>> result = await module.auto_fix(Path("src/module.py"))
            >>> if result.success:
            ...     print(f"Fixed {result.fixes_applied} issues")
            ... else:
            ...     print(f"Failed: {result.errors}")
        """
        ...

    async def validate_fixes(
        self,
        file_path: Path
    ) -> ValidationResult:
        """
        Validate fixes without applying them (dry-run check).

        Useful for checking if file would pass validation before auto-fixing.

        Args:
            file_path: Path to file to validate

        Returns:
            ValidationResult with validation status

        Raises:
            FileNotFoundError: If file doesn't exist

        Example:
            >>> result = await module.validate_fixes(Path("src/module.py"))
            >>> if result.passed:
            ...     print("File would pass validation")
        """
        ...

    async def rollback(
        self,
        backup_metadata: BackupMetadata
    ) -> None:
        """
        Manually rollback to backup.

        Useful for CLI commands or manual recovery.

        Args:
            backup_metadata: Backup to restore from

        Raises:
            RestoreFailedError: If restore fails
            FileNotFoundError: If backup doesn't exist

        Example:
            >>> await module.rollback(result.backup_metadata)
        """
        ...
```

---

## 3. BackupManager API

Manages file backups with checksums and verification.

```python
class BackupManager:
    """
    Manage file backups with atomic operations.

    Features:
    - Timestamped backups
    - SHA-256 checksums
    - Atomic file operations
    - Automatic cleanup of old backups

    Thread-safe: Yes (atomic operations, no shared state)

    Example:
        >>> manager = BackupManager(config)
        >>> metadata = manager.create_backup(Path("src/module.py"))
        >>> manager.validate_backup(metadata)  # True
    """

    def __init__(self, config: AutoFixConfig):
        """
        Initialize BackupManager.

        Args:
            config: Auto-fix configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    def create_backup(
        self,
        file_path: Path,
        *,
        backup_dir: Path | None = None
    ) -> BackupMetadata:
        """
        Create timestamped backup with checksum.

        Backup filename format: {stem}.backup_{timestamp}{suffix}
        Example: module.py.backup_20260129_143022

        Args:
            file_path: Path to file to backup
            backup_dir: Optional backup directory (default: from config)

        Returns:
            BackupMetadata with backup information

        Raises:
            BackupFailedError: If backup creation fails
            FileNotFoundError: If file doesn't exist

        Security:
            - Backup file has 0o600 permissions (owner read/write only)
            - Atomic file operations (write to temp, then rename)
            - Path validation (no traversal)

        Performance:
            - Target: <1 second for files <10MB
            - Uses shutil.copy2 (preserves metadata)

        Example:
            >>> metadata = manager.create_backup(Path("src/module.py"))
            >>> print(f"Backup created: {metadata.backup_path}")
        """
        ...

    def validate_backup(
        self,
        backup: BackupMetadata
    ) -> bool:
        """
        Validate backup integrity using checksum.

        Args:
            backup: Backup metadata to validate

        Returns:
            True if backup is valid, False otherwise

        Example:
            >>> if manager.validate_backup(metadata):
            ...     print("Backup is valid")
        """
        ...

    def cleanup_old_backups(
        self,
        file_path: Path,
        keep_count: int | None = None
    ) -> int:
        """
        Clean up old backups, keeping only recent N.

        Args:
            file_path: Original file path
            keep_count: Number of backups to keep (default: from config)

        Returns:
            Number of backups deleted

        Example:
            >>> deleted = manager.cleanup_old_backups(Path("src/module.py"), keep_count=5)
            >>> print(f"Deleted {deleted} old backups")
        """
        ...

    def list_backups(
        self,
        file_path: Path
    ) -> list[BackupMetadata]:
        """
        List all backups for a file, sorted by timestamp (newest first).

        Args:
            file_path: Original file path

        Returns:
            List of backup metadata

        Example:
            >>> backups = manager.list_backups(Path("src/module.py"))
            >>> for backup in backups:
            ...     print(f"{backup.timestamp}: {backup.backup_path}")
        """
        ...
```

---

## 4. ValidationManager API

Validates code after auto-fix operations.

```python
class ValidationManager:
    """
    Validate code with multiple checks.

    Validation types:
    - Syntax validation (AST parsing)
    - Import validation (check imports exist)
    - Linting validation (Ruff clean run)

    Thread-safe: Yes (no shared state)
    Async: Yes (uses async subprocess)

    Example:
        >>> manager = ValidationManager(config)
        >>> result = await manager.validate_all(Path("src/module.py"))
        >>> if result.passed:
        ...     print("All validation checks passed")
    """

    def __init__(self, config: AutoFixConfig):
        """
        Initialize ValidationManager.

        Args:
            config: Auto-fix configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def validate_syntax(
        self,
        file_path: Path
    ) -> ValidationResult:
        """
        Validate Python syntax using AST parsing.

        Args:
            file_path: Path to file to validate

        Returns:
            ValidationResult with syntax validation status

        Performance:
            - Target: <100ms for files <1000 lines
            - Uses ast.parse (no subprocess)

        Example:
            >>> result = await manager.validate_syntax(Path("src/module.py"))
            >>> if result.syntax_valid:
            ...     print("Syntax is valid")
        """
        ...

    async def validate_imports(
        self,
        file_path: Path
    ) -> ValidationResult:
        """
        Validate imports are resolvable.

        Checks that all imports in the file can be resolved.

        Args:
            file_path: Path to file to validate

        Returns:
            ValidationResult with import validation status

        Performance:
            - Target: <200ms
            - Parses imports from AST
            - Checks module existence

        Example:
            >>> result = await manager.validate_imports(Path("src/module.py"))
            >>> if result.imports_valid:
            ...     print("All imports are valid")
        """
        ...

    async def validate_linting(
        self,
        file_path: Path
    ) -> ValidationResult:
        """
        Validate linting with Ruff (check for new issues).

        Runs Ruff and checks if any new errors were introduced.

        Args:
            file_path: Path to file to validate

        Returns:
            ValidationResult with linting validation status

        Performance:
            - Target: <500ms
            - Uses `ruff check` subprocess

        Example:
            >>> result = await manager.validate_linting(Path("src/module.py"))
            >>> if result.linting_valid:
            ...     print("No new linting errors")
        """
        ...

    async def validate_all(
        self,
        file_path: Path
    ) -> ValidationResult:
        """
        Run all validation checks.

        Runs syntax, imports, and linting validation in sequence.
        Stops on first failure for performance.

        Args:
            file_path: Path to file to validate

        Returns:
            ValidationResult with all validation statuses

        Performance:
            - Target: <1 second
            - Fails fast on first error

        Example:
            >>> result = await manager.validate_all(Path("src/module.py"))
            >>> if result.passed:
            ...     print("All checks passed")
            ... else:
            ...     print(f"Errors: {result.errors}")
        """
        ...
```

---

## 5. RestoreManager API

Restores files from backups with verification.

```python
class RestoreManager:
    """
    Restore files from backups with atomic operations.

    Features:
    - Atomic restore (write to temp, then rename)
    - Checksum verification
    - Metadata preservation

    Thread-safe: Yes (atomic operations)

    Example:
        >>> manager = RestoreManager(config)
        >>> await manager.restore(backup_metadata)
    """

    def __init__(self, config: AutoFixConfig):
        """
        Initialize RestoreManager.

        Args:
            config: Auto-fix configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def restore(
        self,
        backup: BackupMetadata
    ) -> None:
        """
        Restore file from backup with verification.

        Args:
            backup: Backup metadata

        Raises:
            RestoreFailedError: If restore fails
            FileNotFoundError: If backup doesn't exist

        Performance:
            - Target: <1 second
            - Uses atomic rename

        Security:
            - Validates checksum after restore
            - Uses atomic operations (no partial states)

        Example:
            >>> await manager.restore(backup_metadata)
        """
        ...

    def verify_restore(
        self,
        file_path: Path,
        backup: BackupMetadata
    ) -> bool:
        """
        Verify restored file matches backup checksum.

        Args:
            file_path: Restored file path
            backup: Original backup metadata

        Returns:
            True if checksums match, False otherwise

        Example:
            >>> if manager.verify_restore(Path("src/module.py"), backup):
            ...     print("Restore verified")
        """
        ...
```

---

## 6. ScopedMypyExecutor API

Execute mypy with file-level scoping for performance.

```python
class ScopedMypyExecutor:
    """
    Execute mypy with scoped imports for performance.

    Key optimizations:
    - --follow-imports=skip: Don't check imported modules
    - --no-site-packages: Skip stdlib/site-packages
    - Filter results to target file only

    Thread-safe: Yes (no shared state)
    Async: Yes (uses async subprocess)

    Example:
        >>> executor = ScopedMypyExecutor(config)
        >>> result = await executor.execute_scoped(Path("src/module.py"))
        >>> print(f"Found {len(result.issues)} type issues in {result.duration_seconds:.2f}s")
    """

    def __init__(self, config: ScopedMypyConfig):
        """
        Initialize ScopedMypyExecutor.

        Args:
            config: Scoped mypy configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def execute_scoped(
        self,
        file_path: Path,
        *,
        timeout: int | None = None
    ) -> MypyResult:
        """
        Execute mypy with scoped imports and filter results.

        Args:
            file_path: Path to file to type-check
            timeout: Optional timeout in seconds (default: from config)

        Returns:
            MypyResult with issues scoped to file_path

        Raises:
            MypyTimeoutError: If mypy times out

        Performance:
            - Target: <10 seconds (vs 30-60s unscoped)
            - 70% reduction in execution time

        Example:
            >>> result = await executor.execute_scoped(Path("src/module.py"))
            >>> for issue in result.issues:
            ...     print(f"Line {issue.line}: {issue.message}")
        """
        ...

    def parse_output(
        self,
        raw_output: str,
        file_path: Path
    ) -> list[MypyIssue]:
        """
        Parse mypy output and filter to target file.

        Mypy output format:
            file.py:10:5: error: Message here [error-code]

        Args:
            raw_output: Raw mypy stdout
            file_path: Target file path (for filtering)

        Returns:
            List of MypyIssue for target file only

        Example:
            >>> issues = executor.parse_output(output, Path("src/module.py"))
            >>> print(f"Found {len(issues)} issues")
        """
        ...

    def get_scoped_flags(self) -> list[str]:
        """
        Get mypy flags for scoped execution.

        Returns:
            List of mypy command-line flags

        Default flags:
            - --follow-imports=skip
            - --no-site-packages
            - --show-column-numbers
            - --show-error-codes

        Example:
            >>> flags = executor.get_scoped_flags()
            >>> print(" ".join(flags))
        """
        ...
```

---

## 7. RuffGroupingParser API

Parse and group Ruff issues by error code.

```python
class RuffGroupingParser:
    """
    Parse and group Ruff issues by error code.

    Features:
    - Group by error code (F401, E501, etc.)
    - Sort by severity/count/code
    - Render in multiple formats (markdown, HTML, JSON)

    Thread-safe: Yes (no shared state, immutable results)

    Example:
        >>> parser = RuffGroupingParser(config)
        >>> grouped = parser.parse_and_group(ruff_json)
        >>> print(f"Found {grouped.total_issues} issues in {grouped.unique_codes} categories")
    """

    def __init__(self, config: RuffGroupingConfig):
        """
        Initialize RuffGroupingParser.

        Args:
            config: Ruff grouping configuration
        """
        self.config = config

    def parse_and_group(
        self,
        ruff_json: str
    ) -> GroupedRuffIssues:
        """
        Parse Ruff JSON output and group by error code.

        Args:
            ruff_json: Ruff output in JSON format

        Returns:
            GroupedRuffIssues with issues organized by code

        Raises:
            RuffParsingError: If JSON parsing fails

        Performance:
            - Target: <100ms for 100 issues

        Example:
            >>> grouped = parser.parse_and_group(ruff_output)
            >>> for code, issues in grouped.groups.items():
            ...     print(f"{code}: {len(issues)} issues")
        """
        ...

    def sort_groups(
        self,
        groups: dict[str, list[RuffIssue]],
        by: str = "severity"
    ) -> list[tuple[str, list[RuffIssue]]]:
        """
        Sort groups by severity, count, or code.

        Args:
            groups: Grouped issues
            by: Sort method ("severity", "count", "code")

        Returns:
            Sorted list of (code, issues) tuples

        Sort order:
            - severity: error > warning > info, then by count descending
            - count: descending count
            - code: alphabetical

        Example:
            >>> sorted_groups = parser.sort_groups(grouped.groups, by="severity")
            >>> for code, issues in sorted_groups[:5]:  # Top 5
            ...     print(f"{code}: {len(issues)} issues")
        """
        ...

    def render_grouped(
        self,
        groups: GroupedRuffIssues,
        format: str = "markdown"
    ) -> str:
        """
        Render grouped issues in specified format.

        Args:
            groups: Grouped issues
            format: Output format ("markdown", "html", "json")

        Returns:
            Formatted string

        Formats:
            - markdown: GitHub-flavored markdown with headers
            - html: HTML with collapsible groups
            - json: JSON with full structure

        Example:
            >>> markdown = parser.render_grouped(grouped, format="markdown")
            >>> print(markdown)
        """
        ...
```

---

## 8. GroupedRenderer API

Render grouped Ruff issues in review reports.

```python
class GroupedRenderer:
    """
    Render grouped Ruff issues in multiple formats.

    Features:
    - Markdown rendering with headers and lists
    - HTML rendering with collapsible groups
    - JSON rendering for API consumption

    Thread-safe: Yes (no shared state)

    Example:
        >>> renderer = GroupedRenderer()
        >>> markdown = renderer.render_markdown(grouped_issues)
    """

    def render_markdown(
        self,
        groups: GroupedRuffIssues,
        *,
        max_issues_per_group: int = 10,
        include_fixable_badge: bool = True
    ) -> str:
        """
        Render grouped issues as Markdown.

        Args:
            groups: Grouped Ruff issues
            max_issues_per_group: Max issues to show per group
            include_fixable_badge: Show "X auto-fixable" badge

        Returns:
            Markdown string

        Format:
            ### Issues by Code

            #### F401 (5 issues, error)
            *3 auto-fixable*

            - Line 10: 'os' imported but unused
            - Line 15: 'sys' imported but unused
            - ... and 3 more

        Example:
            >>> markdown = renderer.render_markdown(grouped)
            >>> print(markdown)
        """
        ...

    def render_html(
        self,
        groups: GroupedRuffIssues,
        *,
        collapsible: bool = True
    ) -> str:
        """
        Render grouped issues as HTML.

        Args:
            groups: Grouped Ruff issues
            collapsible: Use collapsible groups (details/summary)

        Returns:
            HTML string

        Example:
            >>> html = renderer.render_html(grouped, collapsible=True)
        """
        ...

    def render_json(
        self,
        groups: GroupedRuffIssues,
        *,
        indent: int = 2
    ) -> str:
        """
        Render grouped issues as JSON.

        Args:
            groups: Grouped Ruff issues
            indent: JSON indentation

        Returns:
            JSON string

        Example:
            >>> json_str = renderer.render_json(grouped)
            >>> data = json.loads(json_str)
        """
        ...
```

---

## 9. Configuration Models

Configuration dataclasses for all modules.

```python
@dataclass(frozen=True)
class AutoFixConfig:
    """
    Auto-fix configuration.

    Attributes:
        enabled: Enable auto-fix
        create_backup: Create backup before fixing
        timeout: Timeout in seconds
        validation_required: Require validation after fixing
        max_backup_age_days: Delete backups older than N days
        backup_location: Backup directory path
    """
    enabled: bool = True
    create_backup: bool = True
    timeout: int = 30
    validation_required: bool = True
    max_backup_age_days: int = 7
    backup_location: str = ".tapps-agents/backups"

@dataclass(frozen=True)
class ScopedMypyConfig:
    """
    Scoped mypy configuration.

    Attributes:
        enabled: Enable scoped mypy
        flags: List of mypy flags
        timeout: Timeout in seconds
        cache_results: Enable result caching
        cache_ttl: Cache TTL in seconds
    """
    enabled: bool = True
    flags: tuple[str, ...] = (
        "--follow-imports=skip",
        "--no-site-packages",
        "--show-column-numbers",
        "--show-error-codes"
    )
    timeout: int = 10
    cache_results: bool = True
    cache_ttl: int = 3600

@dataclass(frozen=True)
class RuffGroupingConfig:
    """
    Ruff grouping configuration.

    Attributes:
        enabled: Enable grouped output
        sort_by: Sort method (severity, count, code)
        include_fix_suggestions: Include fix suggestions
        max_issues_per_group: Max issues per group in report
    """
    enabled: bool = True
    sort_by: str = "severity"
    include_fix_suggestions: bool = True
    max_issues_per_group: int = 10
```

---

## 10. Error Handling Contracts

### Exception Hierarchy

```python
class AutoFixError(Exception):
    """Base exception for auto-fix errors."""
    pass

class BackupFailedError(AutoFixError):
    """Backup creation failed."""
    def __init__(self, file_path: Path, reason: str):
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"Backup failed for {file_path}: {reason}")

class ValidationFailedError(AutoFixError):
    """Validation failed after auto-fix."""
    def __init__(self, file_path: Path, errors: list[str]):
        self.file_path = file_path
        self.errors = errors
        super().__init__(f"Validation failed for {file_path}: {errors}")

class RestoreFailedError(AutoFixError):
    """Restore from backup failed."""
    def __init__(self, backup: BackupMetadata, reason: str):
        self.backup = backup
        self.reason = reason
        super().__init__(f"Restore failed for {backup.backup_path}: {reason}")

class ToolExecutionError(Exception):
    """Base exception for tool execution errors."""
    pass

class MypyTimeoutError(ToolExecutionError):
    """Mypy execution timed out."""
    def __init__(self, timeout: int):
        self.timeout = timeout
        super().__init__(f"Mypy timed out after {timeout}s")

class RuffParsingError(ToolExecutionError):
    """Ruff output parsing failed."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Ruff parsing failed: {reason}")
```

### Error Handling Contract

All methods follow these error handling principles:

1. **Never raise on expected failures**: Return error results instead
2. **Raise only on unexpected errors**: System errors, programming errors
3. **Always log errors**: Use appropriate log level (DEBUG, INFO, WARNING, ERROR)
4. **Include context in errors**: File paths, operation details, stack traces
5. **Graceful degradation**: Continue workflow when possible

---

## 11. Usage Examples

### Example 1: Auto-Fix with ImplementerAgent

```python
from pathlib import Path
from tapps_agents.agents.implementer.auto_fix import AutoFixModule
from tapps_agents.core.config import AutoFixConfig

# Initialize
config = AutoFixConfig(
    enabled=True,
    create_backup=True,
    timeout=30,
    validation_required=True
)
auto_fix = AutoFixModule(config)

# Auto-fix a file
file_path = Path("src/module.py")
result = await auto_fix.auto_fix(file_path)

if result.success:
    print(f"✅ Applied {result.fixes_applied} fixes in {result.duration_seconds:.2f}s")
    if result.backup_created:
        print(f"📁 Backup: {result.backup_metadata.backup_path}")
else:
    print(f"❌ Auto-fix failed: {result.errors}")
    if result.backup_created:
        # Rollback available
        await auto_fix.rollback(result.backup_metadata)
```

### Example 2: Scoped Mypy Execution

```python
from pathlib import Path
from tapps_agents.agents.reviewer.tools.scoped_mypy import ScopedMypyExecutor
from tapps_agents.core.config import ScopedMypyConfig

# Initialize
config = ScopedMypyConfig(
    enabled=True,
    flags=("--follow-imports=skip", "--no-site-packages"),
    timeout=10
)
executor = ScopedMypyExecutor(config)

# Run scoped mypy
file_path = Path("src/module.py")
result = await executor.execute_scoped(file_path)

print(f"⏱️  Completed in {result.duration_seconds:.2f}s")
print(f"🔍 Found {len(result.issues)} type issues")

for issue in result.issues[:5]:  # Show first 5
    print(f"  Line {issue.line}: {issue.message} [{issue.error_code}]")
```

### Example 3: Grouped Ruff Output

```python
from tapps_agents.agents.reviewer.tools.ruff_grouping import RuffGroupingParser
from tapps_agents.core.config import RuffGroupingConfig

# Initialize
config = RuffGroupingConfig(
    enabled=True,
    sort_by="severity",
    max_issues_per_group=10
)
parser = RuffGroupingParser(config)

# Parse and group Ruff output
ruff_output = '{"code": "F401", "message": "unused import", ...}'
grouped = parser.parse_and_group(ruff_output)

print(f"📊 {grouped.total_issues} issues in {grouped.unique_codes} categories")
print(f"🔧 {grouped.fixable_count} auto-fixable")

# Render as markdown
markdown = parser.render_grouped(grouped, format="markdown")
print(markdown)
```

### Example 4: Full Workflow Integration

```python
# In ImplementerAgent.implement()
async def implement(self, spec: str, file_path: str) -> dict[str, Any]:
    path = Path(file_path)

    # ... code generation ...

    # Auto-fix before review
    if self.config.agents.implementer.auto_fix.enabled:
        auto_fix_result = await self.auto_fix_module.auto_fix(path)
        if not auto_fix_result.success:
            logger.warning(f"Auto-fix failed: {auto_fix_result.errors}")

    # Review with scoped mypy and grouped Ruff
    if self.require_review:
        review_result = await self.reviewer.review_file(path)
        # review_result includes grouped Ruff issues and scoped mypy results

    return {
        "success": True,
        "file_path": str(path),
        "auto_fix_result": auto_fix_result.to_dict() if auto_fix_result else None,
        "review_result": review_result
    }
```

---

## API Contracts Summary

### Immutability Guarantees

All data models use `@dataclass(frozen=True)` for:
- Thread safety
- Hashability
- No accidental mutations

### Never-Raising Guarantees

These methods never raise exceptions (return error results instead):
- `AutoFixModule.auto_fix()` → Returns `AutoFixResult` with errors
- `ValidationManager.validate_all()` → Returns `ValidationResult` with errors

### Backward Compatibility

All APIs follow semantic versioning:
- Major version bump for breaking changes
- Minor version bump for new features
- Patch version bump for bug fixes

### Deterministic Output

All methods produce deterministic output for same inputs:
- No random behavior
- Timestamps in metadata only (not in core logic)
- Reproducible test results

---

**API Version**: 1.0.0
**Stability**: Stable
**Breaking Changes**: None planned
**Deprecations**: None

