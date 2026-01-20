"""
Centralized path validation for agent file operations.

Implements root-based path validation to prevent directory traversal
and ensure all file operations occur within allowed boundaries.
"""

from __future__ import annotations

from pathlib import Path


class PathValidationError(ValueError):
    """Raised when path validation fails."""

    pass


def assert_write_allowed(
    path: str | Path,
    project_root: str | Path,
    allowed_paths_write: list[str] | None = None,
) -> None:
    """
    Assert that a write to `path` is allowed by the path allowlist (plan 2.2).

    When allowed_paths_write is empty or None: path must be under project_root.
    When non-empty: path must be under project_root and the first component
    of the relative path must be one of the allowed prefixes
    (e.g. src, tests, docs, .tapps-agents).

    Call from implementer agent and artifact writers before writing.

    Args:
        path: File or dir path to write to
        project_root: Project root directory
        allowed_paths_write: Allowed prefix dirs, or None/[] for “only under project_root”

    Raises:
        PathValidationError: If the path is not allowed
    """
    path = Path(path).resolve()
    project_root = Path(project_root).resolve()
    try:
        rel = path.relative_to(project_root)
    except ValueError:
        raise PathValidationError(
            f"Write path {path} is not under project root {project_root}"
        ) from None
    # Under project root is enough when no allowlist
    if not allowed_paths_write:
        return
    parts = rel.parts
    if not parts:
        return  # writing project root itself
    first = parts[0]
    if first in allowed_paths_write:
        return
    raise PathValidationError(
        f"Write path {path} is not under an allowed prefix. "
        f"Allowed: {allowed_paths_write}. First component: {first}"
    )


class PathValidator:
    """
    Validates file paths against allowed roots.

    Allowed roots:
    - Project root (directory containing .tapps-agents/ or current working directory)
    - .tapps-agents/ directory
    - Test temporary directories (pytest)
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize path validator.

        Args:
            project_root: Project root directory. If None, auto-detects from .tapps-agents/
        """
        if project_root is None:
            project_root = self._detect_project_root()

        self.project_root = project_root.resolve()
        self.tapps_agents_dir = project_root / ".tapps-agents"

    @staticmethod
    def _detect_project_root() -> Path:
        """
        Detect project root by looking for .tapps-agents/ directory.

        Returns:
            Project root Path (current directory if .tapps-agents/ not found)
        """
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / ".tapps-agents").exists():
                return parent
        return current

    def _is_within_allowed_root(self, resolved_path: Path) -> bool:
        """
        Check if resolved path is within an allowed root.

        Args:
            resolved_path: Resolved, absolute path

        Returns:
            True if path is within allowed roots
        """
        # Check if within project root
        try:
            resolved_path.relative_to(self.project_root)
            return True
        except ValueError:
            pass

        # Check if within .tapps-agents/
        if self.tapps_agents_dir.exists():
            try:
                resolved_path.relative_to(self.tapps_agents_dir.resolve())
                return True
            except ValueError:
                pass

        return False

    def _is_test_path(self, resolved_path: Path) -> bool:
        """
        Check if path is a legitimate test temporary path.

        Args:
            resolved_path: Resolved, absolute path

        Returns:
            True if path is a test temporary path
        """
        import tempfile
        
        path_str = str(resolved_path)
        
        # Check for pytest temporary directory patterns
        # Pattern 1: pytest-of-<username>/pytest-<number>/ (pytest tmp_path fixture)
        if "pytest-of-" in path_str or "pytest-" in path_str:
            # Also check if it's in a temp directory to be safe
            temp_dir = Path(tempfile.gettempdir())
            try:
                resolved_path.relative_to(temp_dir)
                return True
            except ValueError:
                pass
        
        # Pattern 2: Explicit tmp_path in path (legacy check)
        if "pytest" in path_str and "tmp_path" in path_str:
            return True
        
        return False

    def _check_traversal_patterns(self, file_path: Path) -> None:
        """
        Check for path traversal patterns in the input path.

        Args:
            file_path: Path to check

        Raises:
            PathValidationError: If traversal patterns detected
        """
        path_str = str(file_path)

        # Check for basic traversal sequences
        if ".." in path_str:
            # Allow if it's part of a legitimate path that resolves correctly
            # (e.g., "a/../b" resolves to "b")
            resolved = file_path.resolve()
            # If resolved path doesn't exist or is suspicious, block it
            if not resolved.exists() or not self._is_within_allowed_root(resolved):
                raise PathValidationError(
                    f"Path traversal detected: {file_path}. "
                    f"Resolved to: {resolved}"
                )

        # Check for URL-encoded traversal attempts
        suspicious_patterns = ["%2e%2e", "%2f", "%5c"]
        if any(pattern in path_str.lower() for pattern in suspicious_patterns):
            raise PathValidationError(f"Suspicious path pattern detected: {file_path}")

    def validate_path(
        self,
        file_path: Path,
        must_exist: bool = True,
        max_file_size: int | None = 10 * 1024 * 1024,
        allow_write: bool = True,
    ) -> Path:
        """
        Validate a file path against allowed roots and security rules.

        Args:
            file_path: Path to validate (can be relative or absolute)
            must_exist: If True, file must exist (default: True)
            max_file_size: Maximum file size in bytes (default: 10MB, None to disable)
            allow_write: If False, only validates read access (default: True)

        Returns:
            Resolved Path object

        Raises:
            PathValidationError: If path validation fails
            FileNotFoundError: If must_exist=True and file doesn't exist
        """
        # Convert to Path if string
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Resolve to absolute, canonical path
        try:
            resolved_path = file_path.resolve()
        except (OSError, RuntimeError) as e:
            raise PathValidationError(f"Cannot resolve path {file_path}: {e}") from e

        # Check for traversal patterns in original path
        self._check_traversal_patterns(file_path)

        # Allow test paths
        if self._is_test_path(resolved_path):
            # Still check existence and size if required
            if must_exist and not resolved_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            if max_file_size and resolved_path.exists():
                file_size = resolved_path.stat().st_size
                if file_size > max_file_size:
                    raise PathValidationError(
                        f"File too large: {file_size} bytes (max {max_file_size} bytes)"
                    )
            return resolved_path

        # Check if within allowed roots
        if not self._is_within_allowed_root(resolved_path):
            raise PathValidationError(
                f"Path outside allowed roots: {resolved_path}. "
                f"Allowed roots: {self.project_root}, {self.tapps_agents_dir}"
            )

        # Check file existence
        if must_exist and not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check file size (only for existing files)
        if max_file_size and resolved_path.exists() and resolved_path.is_file():
            file_size = resolved_path.stat().st_size
            if file_size > max_file_size:
                raise PathValidationError(
                    f"File too large: {file_size} bytes (max {max_file_size} bytes)"
                )

        return resolved_path

    def validate_write_path(self, file_path: Path) -> Path:
        """
        Validate a path for write operations.

        Args:
            file_path: Path to validate

        Returns:
            Resolved Path object

        Raises:
            PathValidationError: If path validation fails
        """
        return self.validate_path(
            file_path, must_exist=False, allow_write=True, max_file_size=None
        )

    def validate_read_path(
        self, file_path: Path, max_file_size: int | None = 10 * 1024 * 1024
    ) -> Path:
        """
        Validate a path for read operations.

        Args:
            file_path: Path to validate
            max_file_size: Maximum file size in bytes (default: 10MB)

        Returns:
            Resolved Path object

        Raises:
            PathValidationError: If path validation fails
            FileNotFoundError: If file doesn't exist
        """
        return self.validate_path(
            file_path, must_exist=True, allow_write=False, max_file_size=max_file_size
        )


# Global validator instance (lazy initialization)
_global_validator: PathValidator | None = None


def get_path_validator(project_root: Path | None = None) -> PathValidator:
    """
    Get or create global path validator instance.

    Args:
        project_root: Project root directory (only used on first call)

    Returns:
        PathValidator instance
    """
    global _global_validator
    if _global_validator is None:
        _global_validator = PathValidator(project_root)
    return _global_validator


def reset_path_validator():
    """Reset global path validator (useful for testing)."""
    global _global_validator
    _global_validator = None

