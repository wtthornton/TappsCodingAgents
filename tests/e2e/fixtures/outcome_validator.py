"""
Outcome Validation Framework for E2E Tests.

Provides utilities to validate:
- Code correctness (syntax, logic, style)
- Test execution and result validation
- Bug fix correctness validation
- Feature implementation correctness validation
- Code quality validation (linting, type checking)
"""

import ast
import logging
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CodeCorrectnessValidator:
    """Validates code correctness (syntax, logic, style)."""

    @staticmethod
    def validate_syntax(file_path: Path) -> tuple[bool, str | None]:
        """
        Validate Python syntax using AST parsing.

        Args:
            file_path: Path to Python file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()
            ast.parse(source)
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error in {file_path}: {e}"
        except Exception as e:
            return False, f"Error parsing {file_path}: {e}"

    @staticmethod
    def validate_multiple_files(file_paths: list[Path]) -> tuple[bool, list[str]]:
        """
        Validate syntax for multiple files.

        Args:
            file_paths: List of file paths to validate

        Returns:
            Tuple of (all_valid, error_messages)
        """
        errors = []
        for file_path in file_paths:
            is_valid, error = CodeCorrectnessValidator.validate_syntax(file_path)
            if not is_valid:
                errors.append(error)
        return len(errors) == 0, errors

    @staticmethod
    def validate_style(file_path: Path, use_ruff: bool = True) -> tuple[bool, str | None]:
        """
        Validate code style using ruff (if available).

        Args:
            file_path: Path to Python file
            use_ruff: Whether to use ruff for linting

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not use_ruff:
            return True, None

        try:
            # Check if ruff is available
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return True, None
            else:
                return False, f"Ruff linting errors in {file_path}:\n{result.stdout}\n{result.stderr}"
        except FileNotFoundError:
            logger.warning("ruff not found, skipping style validation")
            return True, None
        except subprocess.TimeoutExpired:
            return False, f"Ruff linting timed out for {file_path}"
        except Exception as e:
            logger.warning(f"Error running ruff: {e}")
            return True, None  # Don't fail if ruff is unavailable


class TestExecutionValidator:
    """Validates test execution and results."""

    @staticmethod
    def run_tests(
        project_path: Path,
        test_path: Path | None = None,
        timeout: int = 300,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Run pytest tests and validate results.

        Args:
            project_path: Path to project root
            test_path: Optional specific test path (defaults to tests/ directory)
            timeout: Timeout in seconds

        Returns:
            Tuple of (all_passed, test_results)
        """
        if test_path is None:
            test_path = project_path / "tests"
            if not test_path.exists():
                return False, {"error": "Tests directory not found"}

        try:
            # Run pytest
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(test_path),
                "-v",
                "--tb=short",
                "--no-header",
            ]
            result = subprocess.run(
                cmd,
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            # Parse pytest output
            output = result.stdout + result.stderr
            passed = result.returncode == 0

            # Extract test counts
            test_counts = TestExecutionValidator._parse_pytest_output(output)

            return passed, {
                "passed": passed,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_counts": test_counts,
            }
        except subprocess.TimeoutExpired:
            return False, {"error": f"Test execution timed out after {timeout} seconds"}
        except Exception as e:
            return False, {"error": f"Error running tests: {e}"}

    @staticmethod
    def _parse_pytest_output(output: str) -> dict[str, int]:
        """Parse pytest output to extract test counts."""
        counts = {"passed": 0, "failed": 0, "skipped": 0, "total": 0}

        # Try to parse pytest summary line
        import re

        # Match patterns like "5 passed, 2 failed, 1 skipped"
        pattern = r"(\d+)\s+passed|(\d+)\s+failed|(\d+)\s+skipped"
        matches = re.findall(pattern, output)
        for match in matches:
            if match[0]:
                counts["passed"] = int(match[0])
            if match[1]:
                counts["failed"] = int(match[1])
            if match[2]:
                counts["skipped"] = int(match[2])

        counts["total"] = counts["passed"] + counts["failed"] + counts["skipped"]
        return counts


class BugFixValidator:
    """Validates bug fix correctness."""

    @staticmethod
    def validate_bug_fix(
        project_path: Path,
        bug_description: str,
        test_path: Path | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Validate that a bug fix is correct.

        Args:
            project_path: Path to project root
            bug_description: Description of the bug that was fixed
            test_path: Optional specific test path

        Returns:
            Tuple of (is_valid, validation_results)
        """
        # Run tests to verify bug is fixed
        tests_passed, test_results = TestExecutionValidator.run_tests(project_path, test_path)

        # Check that code syntax is valid
        python_files = list(project_path.rglob("*.py"))
        syntax_valid, syntax_errors = CodeCorrectnessValidator.validate_multiple_files(python_files)

        return tests_passed and syntax_valid, {
            "tests_passed": tests_passed,
            "test_results": test_results,
            "syntax_valid": syntax_valid,
            "syntax_errors": syntax_errors,
            "bug_description": bug_description,
        }


class FeatureValidator:
    """Validates feature implementation correctness."""

    @staticmethod
    def validate_feature(
        project_path: Path,
        feature_description: str,
        test_path: Path | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Validate that a feature is correctly implemented.

        Args:
            project_path: Path to project root
            feature_description: Description of the feature
            test_path: Optional specific test path

        Returns:
            Tuple of (is_valid, validation_results)
        """
        # Run tests to verify feature works
        tests_passed, test_results = TestExecutionValidator.run_tests(project_path, test_path)

        # Validate code syntax
        python_files = list(project_path.rglob("*.py"))
        syntax_valid, syntax_errors = CodeCorrectnessValidator.validate_multiple_files(python_files)

        # Validate code style
        style_errors = []
        for file_path in python_files[:5]:  # Limit to first 5 files for performance
            style_valid, style_error = CodeCorrectnessValidator.validate_style(file_path)
            if not style_valid and style_error:
                style_errors.append(style_error)

        return tests_passed and syntax_valid and len(style_errors) == 0, {
            "tests_passed": tests_passed,
            "test_results": test_results,
            "syntax_valid": syntax_valid,
            "syntax_errors": syntax_errors,
            "style_errors": style_errors,
            "feature_description": feature_description,
        }


class CodeQualityValidator:
    """Validates code quality (linting, type checking)."""

    @staticmethod
    def validate_quality(
        project_path: Path,
        file_paths: list[Path] | None = None,
        use_ruff: bool = True,
        use_mypy: bool = False,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Validate code quality using linting and type checking.

        Args:
            project_path: Path to project root
            file_paths: Optional list of specific files to check
            use_ruff: Whether to use ruff for linting
            use_mypy: Whether to use mypy for type checking

        Returns:
            Tuple of (is_valid, quality_results)
        """
        if file_paths is None:
            file_paths = list(project_path.rglob("*.py"))
            # Limit to reasonable number for performance
            file_paths = file_paths[:20]

        ruff_errors = []
        mypy_errors = []

        # Run ruff
        if use_ruff:
            for file_path in file_paths:
                style_valid, style_error = CodeCorrectnessValidator.validate_style(file_path, use_ruff=True)
                if not style_valid and style_error:
                    ruff_errors.append(style_error)

        # Run mypy (if requested and available)
        if use_mypy:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "mypy", str(project_path)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if result.returncode != 0:
                    mypy_errors.append(result.stdout + result.stderr)
            except FileNotFoundError:
                logger.warning("mypy not found, skipping type checking")
            except subprocess.TimeoutExpired:
                mypy_errors.append("mypy type checking timed out")
            except Exception as e:
                logger.warning(f"Error running mypy: {e}")

        is_valid = len(ruff_errors) == 0 and len(mypy_errors) == 0

        return is_valid, {
            "ruff_errors": ruff_errors,
            "mypy_errors": mypy_errors,
            "files_checked": len(file_paths),
        }


class OutcomeValidator:
    """Main outcome validator that combines all validation utilities."""

    def __init__(self, project_path: Path):
        """
        Initialize outcome validator.

        Args:
            project_path: Path to project root
        """
        self.project_path = project_path
        self.code_validator = CodeCorrectnessValidator()
        self.test_validator = TestExecutionValidator()
        self.bug_fix_validator = BugFixValidator()
        self.feature_validator = FeatureValidator()
        self.quality_validator = CodeQualityValidator()

    def validate_code_correctness(
        self, file_paths: list[Path] | None = None
    ) -> tuple[bool, list[str]]:
        """
        Validate code correctness.

        Args:
            file_paths: Optional list of files to validate

        Returns:
            Tuple of (all_valid, error_messages)
        """
        if file_paths is None:
            file_paths = list(self.project_path.rglob("*.py"))

        return CodeCorrectnessValidator.validate_multiple_files(file_paths)

    def validate_tests(
        self, test_path: Path | None = None, timeout: int = 300
    ) -> tuple[bool, dict[str, Any]]:
        """
        Validate test execution.

        Args:
            test_path: Optional specific test path
            timeout: Timeout in seconds

        Returns:
            Tuple of (all_passed, test_results)
        """
        return TestExecutionValidator.run_tests(self.project_path, test_path, timeout)

    def validate_bug_fix(
        self, bug_description: str, test_path: Path | None = None
    ) -> tuple[bool, dict[str, Any]]:
        """
        Validate bug fix.

        Args:
            bug_description: Description of the bug
            test_path: Optional specific test path

        Returns:
            Tuple of (is_valid, validation_results)
        """
        return BugFixValidator.validate_bug_fix(self.project_path, bug_description, test_path)

    def validate_feature(
        self, feature_description: str, test_path: Path | None = None
    ) -> tuple[bool, dict[str, Any]]:
        """
        Validate feature implementation.

        Args:
            feature_description: Description of the feature
            test_path: Optional specific test path

        Returns:
            Tuple of (is_valid, validation_results)
        """
        return FeatureValidator.validate_feature(self.project_path, feature_description, test_path)

    def validate_quality(
        self,
        file_paths: list[Path] | None = None,
        use_ruff: bool = True,
        use_mypy: bool = False,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Validate code quality.

        Args:
            file_paths: Optional list of files to check
            use_ruff: Whether to use ruff
            use_mypy: Whether to use mypy

        Returns:
            Tuple of (is_valid, quality_results)
        """
        return CodeQualityValidator.validate_quality(
            self.project_path, file_paths, use_ruff, use_mypy
        )

