"""
Test Failure Analyzer and Auto-Fixer

Analyzes test failures and automatically fixes common patterns.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TestFailure:
    """Represents a test failure."""

    test_name: str
    file_path: str
    error_type: str
    error_message: str
    line_number: int | None = None
    pattern: str | None = None  # Pattern category (async, auth, mock, etc.)
    confidence: float = 0.0  # Confidence in auto-fix (0.0-1.0)


class TestFixer:
    """
    Analyzes test failures and automatically fixes common patterns.

    Supported patterns:
    - TestClient → AsyncClient migration
    - Missing await in async tests
    - Authentication header issues
    - Mock configuration errors
    - Import errors
    """

    def __init__(self, project_root: Path | None = None):
        """
        Initialize test fixer.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path.cwd()

        # Pattern matchers
        self.patterns = {
            "async": {
                "keywords": ["async", "await", "coroutine", "asyncio"],
                "fixes": self._fix_async_issues,
            },
            "auth": {
                "keywords": ["authentication", "authorization", "token", "header"],
                "fixes": self._fix_auth_issues,
            },
            "mock": {
                "keywords": ["mock", "patch", "MagicMock", "Mock"],
                "fixes": self._fix_mock_issues,
            },
            "import": {
                "keywords": ["ImportError", "ModuleNotFoundError", "import"],
                "fixes": self._fix_import_issues,
            },
        }

    def analyze_failures(
        self, test_output: str, test_dir: Path | str | None = None
    ) -> list[TestFailure]:
        """
        Analyze test output to identify failures.

        Args:
            test_output: Pytest output or test failure log
            test_dir: Optional test directory path

        Returns:
            List of identified test failures
        """
        failures: list[TestFailure] = []

        # Parse pytest output format
        # Pattern: "FAILED test_file.py::test_name - Error message"
        failure_pattern = r"FAILED\s+([^\s]+)::([^\s]+)\s+-\s+(.+)"
        matches = re.finditer(failure_pattern, test_output, re.MULTILINE)

        for match in matches:
            file_path = match.group(1)
            test_name = match.group(2)
            error_message = match.group(3)

            # Categorize failure
            failure = self._categorize_failure(
                test_name, file_path, error_message, test_output
            )
            failures.append(failure)

        return failures

    def _categorize_failure(
        self, test_name: str, file_path: str, error_message: str, full_output: str
    ) -> TestFailure:
        """Categorize a test failure by pattern."""
        error_lower = error_message.lower()
        output_lower = full_output.lower()

        # Check each pattern
        for pattern_name, pattern_info in self.patterns.items():
            if any(keyword in error_lower or keyword in output_lower for keyword in pattern_info["keywords"]):
                confidence = self._calculate_confidence(pattern_name, error_message)
                return TestFailure(
                    test_name=test_name,
                    file_path=file_path,
                    error_type=pattern_name,
                    error_message=error_message,
                    pattern=pattern_name,
                    confidence=confidence,
                )

        # Default: unknown pattern
        return TestFailure(
            test_name=test_name,
            file_path=file_path,
            error_type="unknown",
            error_message=error_message,
            confidence=0.0,
        )

    def _calculate_confidence(self, pattern: str, error_message: str) -> float:
        """Calculate confidence in auto-fix."""
        # Base confidence by pattern
        base_confidence = {
            "async": 0.9,
            "auth": 0.7,
            "mock": 0.8,
            "import": 0.6,
        }.get(pattern, 0.5)

        # Adjust based on error message specificity
        if "missing await" in error_message.lower():
            return min(base_confidence + 0.1, 1.0)
        if "TestClient" in error_message and "AsyncClient" in error_message:
            return min(base_confidence + 0.1, 1.0)

        return base_confidence

    def fix_failures(
        self,
        failures: list[TestFailure],
        pattern: str | None = None,
        auto_fix: bool = False,
    ) -> dict[str, Any]:
        """
        Fix test failures.

        Args:
            failures: List of test failures
            pattern: Optional pattern to filter by
            auto_fix: Whether to automatically apply fixes

        Returns:
            Fix results
        """
        # Filter by pattern if specified
        if pattern:
            failures = [f for f in failures if f.pattern == pattern]

        results: dict[str, Any] = {
            "failures_analyzed": len(failures),
            "fixes_applied": [],
            "fixes_suggested": [],
            "errors": [],
        }

        # Group failures by file
        failures_by_file: dict[str, list[TestFailure]] = {}
        for failure in failures:
            if failure.file_path not in failures_by_file:
                failures_by_file[failure.file_path] = []
            failures_by_file[failure.file_path].append(failure)

        # Fix each file
        for file_path, file_failures in failures_by_file.items():
            try:
                fix_result = self._fix_file_failures(
                    file_path, file_failures, auto_fix=auto_fix
                )
                if auto_fix and fix_result.get("fixed"):
                    results["fixes_applied"].append(fix_result)
                else:
                    results["fixes_suggested"].append(fix_result)
            except Exception as e:
                logger.error(f"Error fixing {file_path}: {e}", exc_info=True)
                results["errors"].append({"file": file_path, "error": str(e)})

        return results

    def _fix_file_failures(
        self, file_path: str, failures: list[TestFailure], auto_fix: bool = False
    ) -> dict[str, Any]:
        """Fix failures in a specific test file."""
        test_path = Path(file_path)
        if not test_path.is_absolute():
            test_path = self.project_root / test_path

        if not test_path.exists():
            raise FileNotFoundError(f"Test file not found: {test_path}")

        # Read test file
        test_code = test_path.read_text(encoding="utf-8")
        original_code = test_code

        # Apply fixes based on failure patterns
        fixes_applied = []
        for failure in failures:
            if failure.pattern and failure.confidence > 0.7:
                fix_func = self.patterns[failure.pattern]["fixes"]
                fixed_code, fix_description = fix_func(test_code, failure)
                if fixed_code != test_code:
                    test_code = fixed_code
                    fixes_applied.append(fix_description)

        # Write fixed code if auto_fix and changes were made
        if auto_fix and test_code != original_code:
            test_path.write_text(test_code, encoding="utf-8")

        return {
            "file": str(test_path),
            "failures": len(failures),
            "fixes_applied": fixes_applied,
            "fixed": test_code != original_code,
        }

    def _fix_async_issues(
        self, code: str, failure: TestFailure
    ) -> tuple[str, str]:
        """Fix async/await issues."""
        fixed_code = code
        fixes = []

        # Fix: TestClient → AsyncClient
        if "TestClient" in code and "AsyncClient" not in code:
            fixed_code = re.sub(
                r"from fastapi\.testclient import TestClient",
                "from httpx import AsyncClient",
                fixed_code,
            )
            fixed_code = re.sub(r"TestClient\(", "AsyncClient(", fixed_code)
            fixes.append("Migrated TestClient to AsyncClient")

        # Fix: Missing await in async test
        if "async def test_" in code and "await" not in code:
            # This is more complex - would need AST parsing for proper fix
            # For now, just suggest
            fixes.append("Potential missing await in async test")

        return fixed_code, "; ".join(fixes) if fixes else "No async fixes needed"

    def _fix_auth_issues(
        self, code: str, failure: TestFailure
    ) -> tuple[str, str]:
        """Fix authentication issues."""
        fixed_code = code
        fixes = []

        # Fix: Missing authentication headers
        if "X-Internal-Service" in failure.error_message:
            # Add internal service header
            if "headers" not in code.lower() or "X-Internal-Service" not in code:
                # Would need context-aware insertion
                fixes.append("Add X-Internal-Service header")

        return fixed_code, "; ".join(fixes) if fixes else "No auth fixes needed"

    def _fix_mock_issues(
        self, code: str, failure: TestFailure
    ) -> tuple[str, str]:
        """Fix mock configuration issues."""
        fixed_code = code
        fixes = []

        # Fix: Mock not configured properly
        if "MagicMock" in code or "Mock" in code:
            # Check for common mock issues
            if "return_value" not in code and "side_effect" not in code:
                fixes.append("Mock may need return_value or side_effect")

        return fixed_code, "; ".join(fixes) if fixes else "No mock fixes needed"

    def _fix_import_issues(
        self, code: str, failure: TestFailure
    ) -> tuple[str, str]:
        """Fix import errors."""
        fixed_code = code
        fixes = []

        # Extract module name from error
        match = re.search(r"ModuleNotFoundError.*'([^']+)'", failure.error_message)
        if match:
            module_name = match.group(1)
            # Try to fix common import issues
            if module_name.startswith("src."):
                # Remove src. prefix
                new_import = module_name.replace("src.", "")
                fixed_code = re.sub(
                    f"import {module_name}|from {module_name}",
                    f"import {new_import}|from {new_import}",
                    fixed_code,
                )
                fixes.append(f"Fixed import: {module_name} → {new_import}")

        return fixed_code, "; ".join(fixes) if fixes else "No import fixes needed"

