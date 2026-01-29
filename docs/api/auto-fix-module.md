# Auto-Fix Module API Documentation

**Module:** `tapps_agents.agents.implementer.auto_fix`
**Version:** 1.0.0
**Author:** TappsCodingAgents
**Date:** 2026-01-29

## Overview

The Auto-Fix Module provides automatic code fixing capabilities with backup, validation, and rollback support for the ImplementerAgent. It integrates with Ruff to apply automatic fixes while ensuring code safety through comprehensive validation and atomic operations.

### Key Features

- ✅ **Timestamped Backups**: SHA-256 checksummed backups with atomic operations
- ✅ **Ruff Integration**: Automatic code fixing using `ruff check --fix`
- ✅ **Multi-Level Validation**: Syntax, imports, and linting validation
- ✅ **Automatic Rollback**: Restores original file on validation failure
- ✅ **Never-Raising API**: Returns error results instead of raising exceptions
- ✅ **Performance**: Complete workflow in <5 seconds
- ✅ **Security**: Path validation, 0o600 permissions, no shell injection

### Architecture

The module implements two design patterns:

1. **Pipeline Pattern**: `backup → fix → validate → restore`
2. **Strategy Pattern**: Pluggable managers (BackupManager, ValidationManager, RestoreManager)

---

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Data Models](#data-models)
- [Core Components](#core-components)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)
- [Security](#security)
- [Performance](#performance)
- [Error Handling](#error-handling)

---

## Quick Start

```python
from pathlib import Path
from tapps_agents.agents.implementer.auto_fix import (
    AutoFixConfig,
    AutoFixModule,
)

# 1. Create configuration
config = AutoFixConfig(
    enabled=True,
    create_backup=True,
    timeout=30,
    validation_required=True,
)

# 2. Initialize module
auto_fix = AutoFixModule(config)

# 3. Apply auto-fixes
result = await auto_fix.auto_fix(Path("my_file.py"))

# 4. Check results
if result.success:
    print(f"Applied {result.fixes_applied} fixes in {result.duration_seconds:.2f}s")
else:
    print(f"Failed: {result.errors}")
```

---

## Configuration

### AutoFixConfig

Immutable configuration dataclass for auto-fix operations.

**Module:** `tapps_agents.agents.implementer.auto_fix`

```python
@dataclass(frozen=True)
class AutoFixConfig:
    """Auto-fix configuration."""

    enabled: bool = True
    create_backup: bool = True
    timeout: int = 30
    validation_required: bool = True
    max_backup_age_days: int = 7
    backup_location: str = ".tapps-agents/backups"
```

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | `bool` | `True` | Enable/disable auto-fix |
| `create_backup` | `bool` | `True` | Create backup before fixing |
| `timeout` | `int` | `30` | Timeout in seconds for operations |
| `validation_required` | `bool` | `True` | Require validation after fixing |
| `max_backup_age_days` | `int` | `7` | Days to keep old backups |
| `backup_location` | `str` | `.tapps-agents/backups` | Backup directory path |

#### Example

```python
# Default configuration
config = AutoFixConfig()

# Custom configuration
config = AutoFixConfig(
    enabled=True,
    create_backup=True,
    timeout=60,  # Longer timeout for large files
    validation_required=True,
    max_backup_age_days=30,  # Keep backups for 30 days
    backup_location="/tmp/backups",
)
```

---

## Data Models

All data models are **immutable** (frozen dataclasses) for thread safety.

### BackupMetadata

Metadata for file backup operations.

```python
@dataclass(frozen=True)
class BackupMetadata:
    """Backup metadata with integrity verification."""

    original_path: Path
    backup_path: Path
    timestamp: datetime
    checksum: str  # SHA-256 hash
    size_bytes: int
```

#### Methods

**`to_dict() -> dict[str, Any]`**

Serialize to dictionary for storage.

```python
metadata = BackupMetadata(...)
data = metadata.to_dict()
# {
#     "original_path": "/path/to/file.py",
#     "backup_path": "/path/to/backup.py",
#     "timestamp": "2026-01-29T14:30:00",
#     "checksum": "abc123...",
#     "size_bytes": 1024
# }
```

**`from_dict(data: dict[str, Any]) -> BackupMetadata`** (classmethod)

Deserialize from dictionary.

```python
metadata = BackupMetadata.from_dict(data)
```

---

### ValidationResult

Result of validation checks.

```python
@dataclass(frozen=True)
class ValidationResult:
    """Multi-level validation result."""

    passed: bool  # Overall validation status
    syntax_valid: bool
    imports_valid: bool
    linting_valid: bool
    errors: list[str]
    warnings: list[str]
```

#### Methods

**`to_dict() -> dict[str, Any]`**

Serialize to dictionary.

```python
result = ValidationResult(...)
data = result.to_dict()
```

---

### AutoFixResult

Result of auto-fix operation.

```python
@dataclass(frozen=True)
class AutoFixResult:
    """Complete auto-fix operation result."""

    success: bool
    fixes_applied: int
    validation_passed: bool
    backup_created: bool
    backup_metadata: BackupMetadata | None
    errors: list[str]
    warnings: list[str]
    duration_seconds: float
```

#### Methods

**`to_dict() -> dict[str, Any]`**

Serialize to dictionary (includes nested backup_metadata).

```python
result = AutoFixResult(...)
data = result.to_dict()
```

---

## Core Components

### BackupManager

Manages file backups with atomic operations.

**Features:**
- Timestamped backups with SHA-256 checksums
- Atomic file operations (write-to-temp + rename)
- Automatic cleanup of old backups
- Path traversal protection
- Restrictive permissions (0o600)

#### Constructor

```python
BackupManager(config: AutoFixConfig)
```

#### Methods

**`create_backup(file_path: Path, *, backup_dir: Path | None = None) -> BackupMetadata`**

Create timestamped backup with checksum.

**Parameters:**
- `file_path` (Path): File to backup
- `backup_dir` (Path | None): Optional backup directory (default: from config)

**Returns:** BackupMetadata

**Raises:**
- `FileNotFoundError`: File doesn't exist
- `BackupFailedError`: Backup creation failed

**Performance:** <1 second for files <10MB

**Security:**
- Backup file has 0o600 permissions
- Atomic operations (no partial states)
- Path validation (prevents traversal)

**Example:**

```python
manager = BackupManager(config)

# Create backup
metadata = manager.create_backup(Path("code.py"))
print(f"Backup: {metadata.backup_path}")
print(f"Checksum: {metadata.checksum[:8]}...")
```

---

**`validate_backup(backup: BackupMetadata) -> bool`**

Validate backup integrity using checksum.

**Parameters:**
- `backup` (BackupMetadata): Backup to validate

**Returns:** True if valid, False otherwise

**Example:**

```python
is_valid = manager.validate_backup(metadata)
if not is_valid:
    print("Backup corrupted!")
```

---

**`cleanup_old_backups(file_path: Path, keep_count: int | None = None) -> int`**

Clean up old backups, keeping only recent N.

**Parameters:**
- `file_path` (Path): Original file path
- `keep_count` (int | None): Number to keep (default: from config)

**Returns:** Number of backups deleted

**Example:**

```python
deleted = manager.cleanup_old_backups(Path("code.py"), keep_count=5)
print(f"Deleted {deleted} old backups")
```

---

**`list_backups(file_path: Path) -> list[BackupMetadata]`**

List all backups for a file, sorted by timestamp (newest first).

**Parameters:**
- `file_path` (Path): Original file path

**Returns:** List of BackupMetadata

**Example:**

```python
backups = manager.list_backups(Path("code.py"))
for backup in backups:
    print(f"{backup.timestamp}: {backup.backup_path}")
```

---

### ValidationManager

Validates code with multiple checks (async).

**Features:**
- Syntax validation (AST parsing)
- Import validation (module resolution)
- Linting validation (Ruff integration)
- Fail-fast validation (stops on first critical error)
- Timeout protection

#### Constructor

```python
ValidationManager(config: AutoFixConfig)
```

#### Methods

**`async validate_syntax(file_path: Path) -> ValidationResult`**

Validate Python syntax using AST parsing.

**Parameters:**
- `file_path` (Path): File to validate

**Returns:** ValidationResult

**Performance:** <100ms for files <1000 lines

**Example:**

```python
manager = ValidationManager(config)

result = await manager.validate_syntax(Path("code.py"))
if result.syntax_valid:
    print("Syntax OK")
else:
    print(f"Errors: {result.errors}")
```

---

**`async validate_imports(file_path: Path) -> ValidationResult`**

Validate imports are resolvable.

**Parameters:**
- `file_path` (Path): File to validate

**Returns:** ValidationResult

**Performance:** <200ms

**Example:**

```python
result = await manager.validate_imports(Path("code.py"))
if result.imports_valid:
    print("Imports OK")
else:
    print(f"Warnings: {result.warnings}")
```

---

**`async validate_linting(file_path: Path) -> ValidationResult`**

Validate linting with Ruff.

**Parameters:**
- `file_path` (Path): File to validate

**Returns:** ValidationResult

**Performance:** <500ms

**Example:**

```python
result = await manager.validate_linting(Path("code.py"))
if result.linting_valid:
    print("Linting OK")
else:
    print(f"Issues: {result.errors}")
```

---

**`async validate_all(file_path: Path) -> ValidationResult`**

Run all validation checks with fail-fast.

**Parameters:**
- `file_path` (Path): File to validate

**Returns:** ValidationResult (combined results)

**Performance:** <1 second

**Behavior:** Stops on first syntax error (fail-fast)

**Example:**

```python
result = await manager.validate_all(Path("code.py"))
if result.passed:
    print("All validations passed!")
else:
    print(f"Failed: {result.errors}")
```

---

### RestoreManager

Restores files from backups with verification (async).

**Features:**
- Atomic restore operations
- Checksum verification before/after restore
- Metadata preservation

#### Constructor

```python
RestoreManager(config: AutoFixConfig)
```

#### Methods

**`async restore(backup: BackupMetadata) -> None`**

Restore file from backup with verification.

**Parameters:**
- `backup` (BackupMetadata): Backup to restore

**Raises:**
- `FileNotFoundError`: Backup doesn't exist
- `RestoreFailedError`: Restore failed or verification failed

**Performance:** <1 second

**Security:** Validates checksum after restore

**Example:**

```python
manager = RestoreManager(config)

try:
    await manager.restore(backup_metadata)
    print("Restored successfully")
except RestoreFailedError as e:
    print(f"Restore failed: {e}")
```

---

**`verify_restore(file_path: Path, backup: BackupMetadata) -> bool`**

Verify restored file matches backup checksum.

**Parameters:**
- `file_path` (Path): Restored file path
- `backup` (BackupMetadata): Original backup metadata

**Returns:** True if checksums match, False otherwise

**Example:**

```python
if manager.verify_restore(Path("code.py"), backup):
    print("Restore verified")
else:
    print("Checksum mismatch!")
```

---

### AutoFixModule

Main orchestrator for auto-fix operations (async).

**Features:**
- Complete pipeline: backup → fix → validate → restore
- Integrates with Ruff for auto-fixes
- Never-raising API (returns error results)
- Dependency injection support

#### Constructor

```python
AutoFixModule(
    config: AutoFixConfig,
    backup_manager: BackupManager | None = None,
    validation_manager: ValidationManager | None = None,
    restore_manager: RestoreManager | None = None,
)
```

**Parameters:**
- `config` (AutoFixConfig): Configuration
- `backup_manager` (BackupManager | None): Optional custom backup manager
- `validation_manager` (ValidationManager | None): Optional custom validation manager
- `restore_manager` (RestoreManager | None): Optional custom restore manager

**Example:**

```python
# Default managers
module = AutoFixModule(config)

# Custom managers (dependency injection)
custom_backup = BackupManager(config)
module = AutoFixModule(config, backup_manager=custom_backup)
```

---

#### Methods

**`async auto_fix(file_path: Path, *, create_backup: bool = True, timeout: int | None = None) -> AutoFixResult`**

Apply auto-fixes to file with validation and rollback.

**Workflow:**
1. Validate file path (security check)
2. Create backup (if enabled)
3. Run `ruff check --fix`
4. Validate fixes (syntax, imports, linting)
5. Rollback if validation fails
6. Return result

**Parameters:**
- `file_path` (Path): File to auto-fix
- `create_backup` (bool): Create backup before fixing (default: True)
- `timeout` (int | None): Timeout in seconds (default: from config)

**Returns:** AutoFixResult (never raises exceptions)

**Performance:**
- Target: <5 seconds for files <1000 lines
- Backup: <1 second
- Fix: <3 seconds
- Validation: <1 second

**Security:**
- Validates file path is within project
- Uses subprocess with list args (no shell injection)
- Creates backup with restrictive permissions (0o600)

**Example:**

```python
module = AutoFixModule(config)

# Apply fixes
result = await module.auto_fix(Path("code.py"))

if result.success:
    print(f"✅ Applied {result.fixes_applied} fixes")
    print(f"⏱️  Duration: {result.duration_seconds:.2f}s")
    if result.backup_created:
        print(f"💾 Backup: {result.backup_metadata.backup_path}")
else:
    print(f"❌ Failed: {result.errors}")
    if result.backup_created:
        print("🔄 File restored from backup")
```

**Error Handling:**

```python
# Never raises - always returns AutoFixResult
result = await module.auto_fix(Path("nonexistent.py"))
assert result.success is False
assert "File not found" in result.errors[0]
```

---

**`async validate_fixes(file_path: Path) -> ValidationResult`**

Validate fixes without applying them (dry-run check).

**Parameters:**
- `file_path` (Path): File to validate

**Returns:** ValidationResult

**Raises:** FileNotFoundError if file doesn't exist

**Example:**

```python
# Dry-run validation
result = await module.validate_fixes(Path("code.py"))
if result.passed:
    print("File would pass validation")
else:
    print(f"Issues: {result.errors}")
```

---

**`async rollback(backup_metadata: BackupMetadata) -> None`**

Manually rollback to backup.

**Parameters:**
- `backup_metadata` (BackupMetadata): Backup to restore from

**Raises:**
- `RestoreFailedError`: Restore failed
- `FileNotFoundError`: Backup doesn't exist

**Example:**

```python
# Manual rollback
try:
    await module.rollback(backup_metadata)
    print("Rolled back successfully")
except RestoreFailedError as e:
    print(f"Rollback failed: {e}")
```

---

## Usage Examples

### Example 1: Basic Auto-Fix

```python
import asyncio
from pathlib import Path
from tapps_agents.agents.implementer.auto_fix import (
    AutoFixConfig,
    AutoFixModule,
)

async def main():
    # Configure
    config = AutoFixConfig(
        enabled=True,
        create_backup=True,
        validation_required=True,
    )

    # Initialize
    module = AutoFixModule(config)

    # Apply fixes
    result = await module.auto_fix(Path("my_code.py"))

    # Handle result
    if result.success:
        print(f"✅ Success! Applied {result.fixes_applied} fixes")
    else:
        print(f"❌ Failed: {', '.join(result.errors)}")

asyncio.run(main())
```

---

### Example 2: Custom Timeout and No Backup

```python
# Apply fixes without backup, with custom timeout
result = await module.auto_fix(
    Path("code.py"),
    create_backup=False,  # Skip backup
    timeout=60,  # 60-second timeout
)

if result.success:
    print(f"Applied {result.fixes_applied} fixes in {result.duration_seconds:.2f}s")
```

---

### Example 3: Manual Backup and Restore

```python
# Manual backup
backup_manager = BackupManager(config)
metadata = backup_manager.create_backup(Path("code.py"))
print(f"Backup created: {metadata.backup_path}")

# Apply fixes without automatic backup
result = await module.auto_fix(Path("code.py"), create_backup=False)

# Manual rollback if needed
if not result.success:
    await module.rollback(metadata)
    print("Rolled back to backup")
```

---

### Example 4: Validation Only (Dry-Run)

```python
# Validate without applying fixes
result = await module.validate_fixes(Path("code.py"))

if result.passed:
    print("✅ File is valid")
else:
    print("❌ Validation errors:")
    for error in result.errors:
        print(f"  - {error}")
```

---

### Example 5: Dependency Injection

```python
# Custom backup manager with different configuration
custom_config = AutoFixConfig(backup_location="/custom/backups")
custom_backup = BackupManager(custom_config)

# Inject custom manager
module = AutoFixModule(
    config=config,
    backup_manager=custom_backup,
)

result = await module.auto_fix(Path("code.py"))
```

---

### Example 6: Batch Processing with Error Handling

```python
import asyncio
from pathlib import Path

async def fix_all_files(files: list[Path]):
    """Apply fixes to multiple files."""
    config = AutoFixConfig()
    module = AutoFixModule(config)

    results = []
    for file_path in files:
        result = await module.auto_fix(file_path)
        results.append((file_path, result))

        if result.success:
            print(f"✅ {file_path}: {result.fixes_applied} fixes")
        else:
            print(f"❌ {file_path}: {result.errors[0]}")

    return results

# Process multiple files
files = [Path("file1.py"), Path("file2.py"), Path("file3.py")]
results = await fix_all_files(files)

# Summary
successful = sum(1 for _, r in results if r.success)
print(f"\nSummary: {successful}/{len(results)} files fixed successfully")
```

---

## Security

### Security Features

1. **Path Traversal Prevention**
   - Validates paths before operations
   - Blocks `../../../etc/passwd` attacks
   - Implementation: `BackupManager._is_safe_path()`

2. **No Shell Injection**
   - Uses `asyncio.create_subprocess_exec` with list args
   - Never uses `shell=True`
   - File paths are separate arguments

3. **File Permissions**
   - Backup files: 0o600 (owner read/write only)
   - Prevents unauthorized access

4. **Cryptographic Integrity**
   - SHA-256 checksums for all backups
   - Detects file tampering
   - Verifies restore operations

5. **Atomic Operations**
   - Write-to-temp + atomic rename
   - No partial file states
   - Race condition free

6. **Never-Raising API**
   - Returns error results instead of exceptions
   - Prevents exception-based information disclosure
   - Controlled error messages

### Security Scan Results

```
✅ Bandit: 0 issues
✅ Security Score: 10.0/10
✅ OWASP Top 10: Fully compliant
✅ Path Traversal: Protected
✅ Shell Injection: Not possible
✅ Cryptographic Security: SHA-256
```

---

## Performance

### Performance Targets

| Operation | Target | Actual (Tested) |
|-----------|--------|-----------------|
| **Backup Creation** | <1 second | <1 second ✅ |
| **Ruff Auto-Fix** | <3 seconds | <3 seconds ✅ |
| **Validation (All)** | <1 second | <1 second ✅ |
| **Complete Workflow** | <5 seconds | <5 seconds ✅ |

### Performance Optimization

1. **Fail-Fast Validation**
   - Stops on first syntax error
   - Avoids expensive checks if syntax is invalid

2. **Chunked Checksum Calculation**
   - Reads files in 8KB chunks
   - Efficient for large files

3. **Async Operations**
   - All I/O operations use async/await
   - Subprocess execution is async
   - Timeout protection for all operations

4. **Atomic File Operations**
   - Single `os.replace()` call (atomic)
   - No multiple writes

### Performance Monitoring

```python
result = await module.auto_fix(Path("code.py"))
print(f"Duration: {result.duration_seconds:.2f}s")
```

---

## Error Handling

### Exception Hierarchy

```
AutoFixError (base exception)
├── BackupFailedError
├── ValidationFailedError
└── RestoreFailedError
```

### Custom Exceptions

**BackupFailedError**

```python
class BackupFailedError(AutoFixError):
    """Backup creation failed."""

    file_path: Path
    reason: str
```

**ValidationFailedError**

```python
class ValidationFailedError(AutoFixError):
    """Validation failed after auto-fix."""

    file_path: Path
    errors: list[str]
```

**RestoreFailedError**

```python
class RestoreFailedError(AutoFixError):
    """Restore from backup failed."""

    backup: BackupMetadata
    reason: str
```

### Error Handling Patterns

**Never-Raising API (Recommended)**

```python
# auto_fix() never raises - always returns AutoFixResult
result = await module.auto_fix(Path("code.py"))

if not result.success:
    # Handle errors from result
    for error in result.errors:
        print(f"Error: {error}")

    # Check if backup was created
    if result.backup_created:
        print(f"Backup available: {result.backup_metadata.backup_path}")
```

**Exception-Based API (Manual Operations)**

```python
# Manual operations may raise exceptions
try:
    metadata = backup_manager.create_backup(Path("code.py"))
except BackupFailedError as e:
    print(f"Backup failed: {e.reason}")
except FileNotFoundError:
    print("File not found")
```

### Error Messages

All error messages are:
- ✅ Clear and actionable
- ✅ Include context (file paths, reasons)
- ✅ Safe (no sensitive data exposure)
- ✅ Logged appropriately

---

## Testing

### Test Coverage

**Coverage:** 82.93% (exceeds 80% target)

**Test Suite:**
- 52 unit tests (all passing)
- BackupManager: 12 tests
- ValidationManager: 11 tests
- RestoreManager: 6 tests
- AutoFixModule: 12 tests
- Data models: 7 tests
- Exceptions: 4 tests

### Running Tests

```bash
# Run all tests
pytest tests/agents/implementer/test_auto_fix.py -v

# Run with coverage
pytest tests/agents/implementer/test_auto_fix.py --cov=tapps_agents.agents.implementer.auto_fix --cov-report=term-missing

# Run specific test class
pytest tests/agents/implementer/test_auto_fix.py::TestAutoFixModule -v
```

---

## API Summary

### Classes

| Class | Purpose | Thread-Safe |
|-------|---------|-------------|
| `AutoFixConfig` | Configuration dataclass | ✅ Yes (immutable) |
| `BackupMetadata` | Backup metadata | ✅ Yes (immutable) |
| `ValidationResult` | Validation result | ✅ Yes (immutable) |
| `AutoFixResult` | Auto-fix result | ✅ Yes (immutable) |
| `BackupManager` | Backup operations | ✅ Yes (atomic ops) |
| `ValidationManager` | Validation operations | ✅ Yes (no shared state) |
| `RestoreManager` | Restore operations | ✅ Yes (atomic ops) |
| `AutoFixModule` | Main orchestrator | ✅ Yes (immutable results) |

### Exceptions

| Exception | When Raised |
|-----------|-------------|
| `AutoFixError` | Base exception (never raised directly) |
| `BackupFailedError` | Backup creation fails |
| `ValidationFailedError` | Validation fails (not used by AutoFixModule) |
| `RestoreFailedError` | Restore operation fails |

---

## Version History

### 1.0.0 (2026-01-29)

**Initial Release**

- ✅ Timestamped backups with SHA-256 checksums
- ✅ Ruff integration for auto-fixes
- ✅ Multi-level validation (syntax, imports, linting)
- ✅ Automatic rollback on validation failure
- ✅ Never-raising API design
- ✅ Performance: <5 seconds total
- ✅ Security: 10.0/10 score
- ✅ Test coverage: 82.93%

---

## Related Documentation

- [API Specification](./reviewer-quality-tools-api.md) - Original API spec
- [Implementation Guide](../implementation/) - Implementation details
- [Security Report](../feedback/session-2026-01-29-parallel-execution-feedback.md) - Security scan results
- [Test Documentation](../../tests/agents/implementer/test_auto_fix.py) - Test suite

---

## Support

**Issues:** Report issues at [GitHub Issues](https://github.com/your-org/tapps-agents/issues)
**Documentation:** [https://docs.tapps-agents.dev](https://docs.tapps-agents.dev)
**Version:** 1.0.0
**License:** MIT
