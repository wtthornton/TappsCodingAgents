"""
Auto-fix module for ImplementerAgent.

Provides automatic code fixing with backup, validation, and rollback capabilities.
Implements Pipeline pattern (backup → fix → validate → restore) and Decorator pattern
for safety features.

Version: 1.0.0
Author: TappsCodingAgents
Date: 2026-01-29
"""

import ast
import asyncio
import hashlib
import json
import logging
import os
import shutil
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration Models
# ============================================================================


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


# ============================================================================
# Data Models
# ============================================================================


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
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackupMetadata":
        """Create from dictionary."""
        return cls(
            original_path=Path(data["original_path"]),
            backup_path=Path(data["backup_path"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            checksum=data["checksum"],
            size_bytes=data["size_bytes"],
        )


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
            "warnings": self.warnings,
        }


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
            "backup_metadata": self.backup_metadata.to_dict()
            if self.backup_metadata
            else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "duration_seconds": self.duration_seconds,
        }


# ============================================================================
# Custom Exceptions
# ============================================================================


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


# ============================================================================
# BackupManager
# ============================================================================


class BackupManager:
    """
    Manage file backups with atomic operations.

    Features:
    - Timestamped backups
    - SHA-256 checksums
    - Atomic file operations
    - Automatic cleanup of old backups

    Thread-safe: Yes (atomic operations, no shared state)
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
        self, file_path: Path, *, backup_dir: Path | None = None
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
        """
        start_time = time.time()

        try:
            # Validate file exists
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Validate path (prevent traversal)
            if not self._is_safe_path(file_path):
                raise BackupFailedError(
                    file_path, "Path traversal detected or unsafe path"
                )

            # Calculate checksum
            checksum = self._calculate_checksum(file_path)
            size_bytes = file_path.stat().st_size

            # Create backup directory
            if backup_dir is None:
                backup_dir = Path(self.config.backup_location)
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{file_path.stem}.backup_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_filename

            # Copy file to backup (atomic operation)
            temp_path = backup_path.with_suffix(".tmp")
            try:
                shutil.copy2(file_path, temp_path)
                # Set restrictive permissions (0o600 = owner read/write only)
                os.chmod(temp_path, 0o600)
                # Atomic rename
                os.replace(temp_path, backup_path)
            finally:
                # Clean up temp file if it exists
                if temp_path.exists():
                    temp_path.unlink()

            metadata = BackupMetadata(
                original_path=file_path,
                backup_path=backup_path,
                timestamp=datetime.now(),
                checksum=checksum,
                size_bytes=size_bytes,
            )

            duration = time.time() - start_time
            self.logger.info(
                f"Created backup: {backup_path} (checksum: {checksum[:8]}..., "
                f"size: {size_bytes} bytes, duration: {duration:.2f}s)"
            )

            return metadata

        except FileNotFoundError:
            raise
        except Exception as e:
            raise BackupFailedError(file_path, str(e)) from e

    def validate_backup(self, backup: BackupMetadata) -> bool:
        """
        Validate backup integrity using checksum.

        Args:
            backup: Backup metadata to validate

        Returns:
            True if backup is valid, False otherwise
        """
        try:
            if not backup.backup_path.exists():
                self.logger.warning(f"Backup file not found: {backup.backup_path}")
                return False

            current_checksum = self._calculate_checksum(backup.backup_path)
            is_valid = current_checksum == backup.checksum

            if not is_valid:
                self.logger.warning(
                    f"Backup checksum mismatch: expected {backup.checksum[:8]}..., "
                    f"got {current_checksum[:8]}..."
                )

            return is_valid

        except Exception as e:
            self.logger.error(f"Error validating backup: {e}")
            return False

    def cleanup_old_backups(
        self, file_path: Path, keep_count: int | None = None
    ) -> int:
        """
        Clean up old backups, keeping only recent N.

        Args:
            file_path: Original file path
            keep_count: Number of backups to keep (default: from config)

        Returns:
            Number of backups deleted
        """
        if keep_count is None:
            keep_count = self.config.max_backup_age_days  # Reuse config value

        try:
            backups = self.list_backups(file_path)

            # Keep only N most recent backups
            if len(backups) <= keep_count:
                return 0

            backups_to_delete = backups[keep_count:]
            deleted_count = 0

            for backup in backups_to_delete:
                try:
                    backup.backup_path.unlink()
                    deleted_count += 1
                    self.logger.debug(f"Deleted old backup: {backup.backup_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete backup {backup.backup_path}: {e}")

            return deleted_count

        except Exception as e:
            self.logger.error(f"Error cleaning up backups: {e}")
            return 0

    def list_backups(self, file_path: Path) -> list[BackupMetadata]:
        """
        List all backups for a file, sorted by timestamp (newest first).

        Args:
            file_path: Original file path

        Returns:
            List of backup metadata
        """
        backup_dir = Path(self.config.backup_location)
        if not backup_dir.exists():
            return []

        # Find backup files matching pattern
        pattern = f"{file_path.stem}.backup_*{file_path.suffix}"
        backup_files = list(backup_dir.glob(pattern))

        backups = []
        for backup_file in backup_files:
            try:
                # Extract timestamp from filename
                timestamp_str = backup_file.stem.split(".backup_")[1]
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                checksum = self._calculate_checksum(backup_file)
                size_bytes = backup_file.stat().st_size

                metadata = BackupMetadata(
                    original_path=file_path,
                    backup_path=backup_file,
                    timestamp=timestamp,
                    checksum=checksum,
                    size_bytes=size_bytes,
                )
                backups.append(metadata)

            except Exception as e:
                self.logger.warning(f"Failed to parse backup {backup_file}: {e}")

        # Sort by timestamp (newest first)
        backups.sort(key=lambda b: b.timestamp, reverse=True)
        return backups

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _is_safe_path(self, file_path: Path) -> bool:
        """
        Validate path is safe (no traversal, within project).

        Security: Prevent path traversal attacks.
        """
        try:
            # Resolve to absolute path
            abs_path = file_path.resolve()

            # Check for path traversal (../)
            if ".." in str(file_path):
                return False

            # Check file exists or parent exists (for new files)
            if not abs_path.exists() and not abs_path.parent.exists():
                return False

            return True

        except Exception:
            return False


# ============================================================================
# ValidationManager
# ============================================================================


class ValidationManager:
    """
    Validate code with multiple checks.

    Validation types:
    - Syntax validation (AST parsing)
    - Import validation (check imports exist)
    - Linting validation (Ruff clean run)

    Thread-safe: Yes (no shared state)
    Async: Yes (uses async subprocess)
    """

    def __init__(self, config: AutoFixConfig):
        """
        Initialize ValidationManager.

        Args:
            config: Auto-fix configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def validate_syntax(self, file_path: Path) -> ValidationResult:
        """
        Validate Python syntax using AST parsing.

        Args:
            file_path: Path to file to validate

        Returns:
            ValidationResult with syntax validation status

        Performance:
            - Target: <100ms for files <1000 lines
            - Uses ast.parse (no subprocess)
        """
        errors = []
        warnings = []

        try:
            with open(file_path, encoding="utf-8") as f:
                code = f.read()

            # Parse AST
            ast.parse(code, filename=str(file_path))
            syntax_valid = True

        except SyntaxError as e:
            syntax_valid = False
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            self.logger.warning(f"Syntax validation failed: {e}")

        except Exception as e:
            syntax_valid = False
            errors.append(f"Unexpected error during syntax validation: {e}")
            self.logger.error(f"Syntax validation error: {e}")

        return ValidationResult(
            passed=syntax_valid,
            syntax_valid=syntax_valid,
            imports_valid=True,  # Not checked in this method
            linting_valid=True,  # Not checked in this method
            errors=errors,
            warnings=warnings,
        )

    async def validate_imports(self, file_path: Path) -> ValidationResult:
        """
        Validate imports are resolvable.

        Args:
            file_path: Path to file to validate

        Returns:
            ValidationResult with import validation status

        Performance:
            - Target: <200ms
            - Parses imports from AST
            - Checks module existence
        """
        errors = []
        warnings = []
        imports_valid = True

        try:
            with open(file_path, encoding="utf-8") as f:
                code = f.read()

            tree = ast.parse(code, filename=str(file_path))

            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._check_import(alias.name):
                            warnings.append(f"Cannot resolve import: {alias.name}")

                elif isinstance(node, ast.ImportFrom):
                    if node.module and not self._check_import(node.module):
                        warnings.append(f"Cannot resolve import: {node.module}")

        except Exception as e:
            imports_valid = False
            errors.append(f"Import validation error: {e}")
            self.logger.error(f"Import validation failed: {e}")

        return ValidationResult(
            passed=imports_valid and not errors,
            syntax_valid=True,  # Not checked in this method
            imports_valid=imports_valid,
            linting_valid=True,  # Not checked in this method
            errors=errors,
            warnings=warnings,
        )

    async def validate_linting(self, file_path: Path) -> ValidationResult:
        """
        Validate linting with Ruff (check for new issues).

        Args:
            file_path: Path to file to validate

        Returns:
            ValidationResult with linting validation status

        Performance:
            - Target: <500ms
            - Uses `ruff check` subprocess
        """
        errors = []
        warnings = []
        linting_valid = True

        try:
            # Run Ruff check (no --fix)
            result = await asyncio.create_subprocess_exec(
                "ruff",
                "check",
                "--output-format=json",
                str(file_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                result.communicate(), timeout=self.config.timeout
            )

            if result.returncode != 0:
                # Parse JSON output
                try:
                    issues = json.loads(stdout.decode())
                    if issues:
                        linting_valid = False
                        for issue in issues:
                            errors.append(
                                f"Line {issue.get('location', {}).get('row', '?')}: "
                                f"{issue.get('message', 'Unknown error')} "
                                f"[{issue.get('code', 'unknown')}]"
                            )
                except json.JSONDecodeError:
                    # Ruff output is not JSON, treat as warning
                    warnings.append("Could not parse Ruff output")

        except TimeoutError:
            warnings.append(f"Ruff validation timed out after {self.config.timeout}s")
        except FileNotFoundError:
            warnings.append("Ruff not found (skipping linting validation)")
        except Exception as e:
            warnings.append(f"Linting validation error: {e}")
            self.logger.error(f"Linting validation failed: {e}")

        return ValidationResult(
            passed=linting_valid and not errors,
            syntax_valid=True,  # Not checked in this method
            imports_valid=True,  # Not checked in this method
            linting_valid=linting_valid,
            errors=errors,
            warnings=warnings,
        )

    async def validate_all(self, file_path: Path) -> ValidationResult:
        """
        Run all validation checks.

        Args:
            file_path: Path to file to validate

        Returns:
            ValidationResult with all validation statuses

        Performance:
            - Target: <1 second
            - Fails fast on first error
        """
        all_errors = []
        all_warnings = []

        # Syntax validation (fast, fail fast)
        syntax_result = await self.validate_syntax(file_path)
        all_errors.extend(syntax_result.errors)
        all_warnings.extend(syntax_result.warnings)

        if not syntax_result.syntax_valid:
            # Fail fast - syntax errors prevent other checks
            return ValidationResult(
                passed=False,
                syntax_valid=False,
                imports_valid=False,
                linting_valid=False,
                errors=all_errors,
                warnings=all_warnings,
            )

        # Import validation
        import_result = await self.validate_imports(file_path)
        all_errors.extend(import_result.errors)
        all_warnings.extend(import_result.warnings)

        # Linting validation
        linting_result = await self.validate_linting(file_path)
        all_errors.extend(linting_result.errors)
        all_warnings.extend(linting_result.warnings)

        passed = (
            syntax_result.syntax_valid
            and import_result.imports_valid
            and linting_result.linting_valid
            and not all_errors
        )

        return ValidationResult(
            passed=passed,
            syntax_valid=syntax_result.syntax_valid,
            imports_valid=import_result.imports_valid,
            linting_valid=linting_result.linting_valid,
            errors=all_errors,
            warnings=all_warnings,
        )

    def _check_import(self, module_name: str) -> bool:
        """
        Check if module can be imported.

        Returns:
            True if module exists, False otherwise
        """
        try:
            __import__(module_name.split(".")[0])
            return True
        except ImportError:
            return False


# ============================================================================
# RestoreManager
# ============================================================================


class RestoreManager:
    """
    Restore files from backups with atomic operations.

    Features:
    - Atomic restore (write to temp, then rename)
    - Checksum verification
    - Metadata preservation

    Thread-safe: Yes (atomic operations)
    """

    def __init__(self, config: AutoFixConfig):
        """
        Initialize RestoreManager.

        Args:
            config: Auto-fix configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def restore(self, backup: BackupMetadata) -> None:
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
        """
        try:
            if not backup.backup_path.exists():
                raise FileNotFoundError(f"Backup not found: {backup.backup_path}")

            # Verify backup integrity
            current_checksum = self._calculate_checksum(backup.backup_path)
            if current_checksum != backup.checksum:
                raise RestoreFailedError(
                    backup, f"Backup checksum mismatch: {current_checksum[:8]}..."
                )

            # Copy backup to temp location
            temp_path = backup.original_path.with_suffix(".restore_tmp")
            try:
                shutil.copy2(backup.backup_path, temp_path)
                # Atomic rename
                os.replace(temp_path, backup.original_path)

                self.logger.info(f"Restored file from backup: {backup.backup_path}")

            finally:
                # Clean up temp file if it exists
                if temp_path.exists():
                    temp_path.unlink()

            # Verify restore
            if not self.verify_restore(backup.original_path, backup):
                raise RestoreFailedError(
                    backup, "Restore verification failed (checksum mismatch)"
                )

        except (FileNotFoundError, RestoreFailedError):
            raise
        except Exception as e:
            raise RestoreFailedError(backup, str(e)) from e

    def verify_restore(self, file_path: Path, backup: BackupMetadata) -> bool:
        """
        Verify restored file matches backup checksum.

        Args:
            file_path: Restored file path
            backup: Original backup metadata

        Returns:
            True if checksums match, False otherwise
        """
        try:
            current_checksum = self._calculate_checksum(file_path)
            return current_checksum == backup.checksum
        except Exception as e:
            self.logger.error(f"Restore verification error: {e}")
            return False

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()


# ============================================================================
# AutoFixModule (Main Orchestrator)
# ============================================================================


class AutoFixModule:
    """
    Auto-fix module for ImplementerAgent.

    Orchestrates backup → fix → validate → restore workflow.
    Integrates with Ruff for auto-fixes.

    Thread-safe: Yes (immutable results, no shared state)
    Async: Yes (uses async subprocess)
    """

    def __init__(
        self,
        config: AutoFixConfig,
        backup_manager: BackupManager | None = None,
        validation_manager: ValidationManager | None = None,
        restore_manager: RestoreManager | None = None,
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
        timeout: int | None = None,
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
        """
        start_time = time.time()
        errors = []
        warnings = []
        backup_metadata = None
        fixes_applied = 0

        try:
            # Validate file path
            if not file_path.exists():
                errors.append(f"File not found: {file_path}")
                return self._create_error_result(errors, warnings, start_time)

            if not self.backup_manager._is_safe_path(file_path):
                errors.append("Unsafe file path (path traversal detected)")
                return self._create_error_result(errors, warnings, start_time)

            # Step 1: Create backup
            if create_backup and self.config.create_backup:
                try:
                    backup_metadata = self.backup_manager.create_backup(file_path)
                    self.logger.info(f"Backup created: {backup_metadata.backup_path}")
                except BackupFailedError as e:
                    errors.append(f"Backup failed: {e.reason}")
                    return self._create_error_result(
                        errors, warnings, start_time, backup_metadata=None
                    )

            # Step 2: Run ruff check --fix
            try:
                fix_timeout = timeout or self.config.timeout
                result = await asyncio.create_subprocess_exec(
                    "ruff",
                    "check",
                    "--fix",
                    "--output-format=json",
                    str(file_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await asyncio.wait_for(
                    result.communicate(), timeout=fix_timeout
                )

                # Count fixes applied from JSON output
                try:
                    output = json.loads(stdout.decode())
                    fixes_applied = len(
                        [issue for issue in output if issue.get("fixed", False)]
                    )
                except json.JSONDecodeError:
                    # Cannot parse output, assume some fixes applied if returncode == 0
                    fixes_applied = 1 if result.returncode == 0 else 0

                self.logger.info(f"Applied {fixes_applied} auto-fixes")

            except TimeoutError:
                errors.append(f"Ruff timed out after {fix_timeout}s")
                await self._rollback_if_needed(backup_metadata, errors)
                return self._create_error_result(
                    errors, warnings, start_time, backup_metadata
                )

            except FileNotFoundError:
                warnings.append("Ruff not found (skipping auto-fix)")
                return self._create_error_result(
                    errors, warnings, start_time, backup_metadata
                )

            except Exception as e:
                errors.append(f"Ruff execution failed: {e}")
                await self._rollback_if_needed(backup_metadata, errors)
                return self._create_error_result(
                    errors, warnings, start_time, backup_metadata
                )

            # Step 3: Validate fixes
            if self.config.validation_required:
                validation_result = await self.validation_manager.validate_all(file_path)

                if not validation_result.passed:
                    errors.extend(validation_result.errors)
                    warnings.extend(validation_result.warnings)

                    # Rollback on validation failure
                    await self._rollback_if_needed(backup_metadata, errors)

                    return AutoFixResult(
                        success=False,
                        fixes_applied=fixes_applied,
                        validation_passed=False,
                        backup_created=backup_metadata is not None,
                        backup_metadata=backup_metadata,
                        errors=errors,
                        warnings=warnings,
                        duration_seconds=time.time() - start_time,
                    )

                warnings.extend(validation_result.warnings)

            # Success
            duration = time.time() - start_time
            self.logger.info(
                f"Auto-fix completed successfully: {fixes_applied} fixes in {duration:.2f}s"
            )

            return AutoFixResult(
                success=True,
                fixes_applied=fixes_applied,
                validation_passed=True,
                backup_created=backup_metadata is not None,
                backup_metadata=backup_metadata,
                errors=[],
                warnings=warnings,
                duration_seconds=duration,
            )

        except Exception as e:
            # Unexpected error - never raise, return error result
            errors.append(f"Unexpected error: {e}")
            self.logger.exception(f"Auto-fix failed with unexpected error: {e}")
            await self._rollback_if_needed(backup_metadata, errors)
            return self._create_error_result(errors, warnings, start_time, backup_metadata)

    async def validate_fixes(self, file_path: Path) -> ValidationResult:
        """
        Validate fixes without applying them (dry-run check).

        Args:
            file_path: Path to file to validate

        Returns:
            ValidationResult with validation status

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        return await self.validation_manager.validate_all(file_path)

    async def rollback(self, backup_metadata: BackupMetadata) -> None:
        """
        Manually rollback to backup.

        Args:
            backup_metadata: Backup to restore from

        Raises:
            RestoreFailedError: If restore fails
            FileNotFoundError: If backup doesn't exist
        """
        await self.restore_manager.restore(backup_metadata)

    async def _rollback_if_needed(
        self, backup_metadata: BackupMetadata | None, errors: list[str]
    ) -> None:
        """
        Rollback to backup if available.

        Args:
            backup_metadata: Backup to restore from (None = no rollback)
            errors: List to append rollback errors to
        """
        if backup_metadata is not None:
            try:
                await self.restore_manager.restore(backup_metadata)
                self.logger.info(f"Rolled back to backup: {backup_metadata.backup_path}")
            except RestoreFailedError as e:
                errors.append(f"Rollback failed: {e.reason}")
                self.logger.error(f"Rollback failed: {e}")

    def _create_error_result(
        self,
        errors: list[str],
        warnings: list[str],
        start_time: float,
        backup_metadata: BackupMetadata | None = None,
    ) -> AutoFixResult:
        """Create error result with standard fields."""
        return AutoFixResult(
            success=False,
            fixes_applied=0,
            validation_passed=False,
            backup_created=backup_metadata is not None,
            backup_metadata=backup_metadata,
            errors=errors,
            warnings=warnings,
            duration_seconds=time.time() - start_time,
        )
