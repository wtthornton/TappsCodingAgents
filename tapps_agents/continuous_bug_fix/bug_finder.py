"""
Bug Finder - Detects bugs by running tests and parsing failures.
"""

import logging
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core.config import ProjectConfig, load_config

logger = logging.getLogger(__name__)


@dataclass
class BugInfo:
    """Information about a detected bug."""

    file_path: str  # Source file with bug (relative to project root)
    error_message: str  # Error description/message
    test_name: str  # Test function name that failed
    test_file: str  # Test file path (relative to project root)
    line_number: int | None = None  # Line number in source file (if available)
    traceback: str | None = None  # Full traceback (optional, for debugging)


class BugFinder:
    """Finds bugs by running tests and parsing failures."""

    def __init__(
        self,
        project_root: Path | None = None,
        config: ProjectConfig | None = None,
    ) -> None:
        """
        Initialize BugFinder.

        Args:
            project_root: Project root directory (default: current directory)
            config: Project configuration (optional)
        """
        self.project_root = project_root or Path.cwd()
        self.config = config or load_config()

    async def find_bugs(
        self,
        test_path: str | None = None,
    ) -> list[BugInfo]:
        """
        Run tests and return list of bugs found.

        Args:
            test_path: Test directory or file to run (default: tests/)

        Returns:
            List of BugInfo objects representing detected bugs
        """
        # Use default test path from config if not provided
        if test_path is None:
            test_path = getattr(self.config, "continuous_bug_fix", None)
            if test_path:
                test_path = test_path.test_path
            else:
                test_path = "tests/"

        # Validate test path
        test_path_obj = self.project_root / test_path
        if not test_path_obj.exists():
            logger.warning(f"Test path does not exist: {test_path_obj}")
            return []

        # Run pytest
        result = await self._run_pytest(test_path)

        if not result.get("success"):
            logger.warning(f"Pytest execution failed: {result.get('error')}")
            return []

        # Parse output
        bugs = self._parse_pytest_output(
            result.get("stdout", ""),
            result.get("stderr", ""),
        )

        logger.info(f"Found {len(bugs)} bugs from test failures")
        return bugs

    async def _run_pytest(
        self,
        test_path: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute pytest and capture output.

        Args:
            test_path: Test directory or file to run

        Returns:
            Dictionary with:
                - success: bool
                - return_code: int
                - stdout: str
                - stderr: str
                - error: str | None
        """
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(test_path) if test_path else "tests/",
            "-v",
            "--tb=short",
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,  # 5 minute timeout
            )

            return {
                "success": result.returncode == 0 or result.returncode == 1,  # 1 = failures, but tests ran
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": "",
                "error": "Test execution timeout (5 minutes)",
            }
        except Exception as e:
            logger.error(f"Error running pytest: {e}", exc_info=True)
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": "",
                "error": str(e),
            }

    def _parse_pytest_output(
        self,
        output: str,
        stderr: str,
    ) -> list[BugInfo]:
        """
        Parse pytest output to extract bug information.

        Args:
            output: pytest stdout
            stderr: pytest stderr

        Returns:
            List of BugInfo objects
        """
        bugs: list[BugInfo] = []
        combined_output = output + "\n" + stderr

        # Pattern to match test failures:
        # FAILED tests/test_file.py::test_function - Error message
        # or
        # tests/test_file.py::test_function FAILED
        failure_pattern = re.compile(
            r"FAILED\s+([^\s]+)::([^\s]+)\s*-?\s*(.+?)(?=\n|$)",
            re.MULTILINE | re.DOTALL,
        )

        # Also match: test_file.py::test_function FAILED
        failure_pattern2 = re.compile(
            r"([^\s]+)::([^\s]+)\s+FAILED",
            re.MULTILINE,
        )

        matches = list(failure_pattern.finditer(combined_output))
        matches.extend(failure_pattern2.finditer(combined_output))

        for match in matches:
            test_file = match.group(1)
            test_name = match.group(2)
            error_msg = match.group(3).strip() if len(match.groups()) > 2 else "Test failed"

            # Extract source file and line number from traceback
            source_file, line_number = self._extract_source_file(
                test_file,
                combined_output,
            )

            # Skip if source file is a test file or config file
            if source_file and (
                "test_" in source_file
                or "/tests/" in source_file
                or source_file.endswith("conftest.py")
                or source_file.endswith("pytest.ini")
            ):
                continue

            # Make paths relative to project root
            if source_file:
                try:
                    source_path = Path(source_file)
                    if source_path.is_absolute():
                        source_file = str(source_path.relative_to(self.project_root))
                except ValueError:
                    # Path not relative to project root, skip
                    continue

            try:
                test_path_obj = Path(test_file)
                if test_path_obj.is_absolute():
                    test_file = str(test_path_obj.relative_to(self.project_root))
            except ValueError:
                pass

            bugs.append(
                BugInfo(
                    file_path=source_file or test_file,  # Fallback to test file if source not found
                    error_message=error_msg[:500],  # Limit error message length
                    test_name=test_name,
                    test_file=test_file,
                    line_number=line_number,
                    traceback=combined_output[max(0, match.start() - 500) : match.end() + 500],
                )
            )

        return bugs

    def _extract_source_file(
        self,
        test_file: str,
        traceback: str,
    ) -> tuple[str | None, int | None]:
        """
        Extract source file path and line number from test failure.

        Args:
            test_file: Test file path
            traceback: Test failure traceback/output

        Returns:
            Tuple of (source_file_path, line_number) or (None, None)
        """
        # Pattern to match file paths in traceback:
        # File "path/to/file.py", line 42, in function_name
        file_line_pattern = re.compile(
            r'File\s+"([^"]+)"\s*,\s*line\s+(\d+)',
            re.MULTILINE,
        )

        matches = file_line_pattern.findall(traceback)

        # Filter out test files and find first source file
        for file_path, line_str in matches:
            if (
                "test_" not in file_path
                and "/tests/" not in file_path
                and not file_path.endswith("conftest.py")
            ):
                try:
                    line_num = int(line_str)
                    return (file_path, line_num)
                except ValueError:
                    continue

        return (None, None)
