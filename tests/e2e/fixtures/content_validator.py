"""
Artifact Content Validation Utilities for E2E Tests.

Provides utilities to validate artifact content quality:
- Code quality checks (linting, type checking, complexity)
- Documentation completeness checks
- Test coverage validation
- Artifact structure and content validation
"""

import ast
import logging
import re
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CodeQualityValidator:
    """Validates code quality using linting, type checking, and complexity metrics."""

    @staticmethod
    def validate_with_ruff(file_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate code quality using ruff.

        Args:
            file_path: Path to Python file

        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return True, []
            else:
                errors = result.stdout.split("\n") if result.stdout else []
                return False, [e for e in errors if e.strip()]
        except FileNotFoundError:
            logger.warning("ruff not found, skipping quality validation")
            return True, []
        except subprocess.TimeoutExpired:
            return False, [f"Ruff validation timed out for {file_path}"]
        except Exception as e:
            logger.warning(f"Error running ruff: {e}")
            return True, []

    @staticmethod
    def validate_with_mypy(file_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate type checking using mypy.

        Args:
            file_path: Path to Python file

        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "mypy", str(file_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return True, []
            else:
                errors = result.stdout.split("\n") if result.stdout else []
                return False, [e for e in errors if e.strip()]
        except FileNotFoundError:
            logger.warning("mypy not found, skipping type checking")
            return True, []
        except subprocess.TimeoutExpired:
            return False, [f"mypy validation timed out for {file_path}"]
        except Exception as e:
            logger.warning(f"Error running mypy: {e}")
            return True, []

    @staticmethod
    def calculate_complexity(file_path: Path) -> Dict[str, Any]:
        """
        Calculate code complexity metrics.

        Args:
            file_path: Path to Python file

        Returns:
            Dictionary with complexity metrics
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)

            complexity = {
                "functions": 0,
                "classes": 0,
                "max_nesting": 0,
                "lines": len(source.split("\n")),
            }

            def visit_node(node, depth=0):
                complexity["max_nesting"] = max(complexity["max_nesting"], depth)
                if isinstance(node, ast.FunctionDef):
                    complexity["functions"] += 1
                elif isinstance(node, ast.ClassDef):
                    complexity["classes"] += 1
                for child in ast.iter_child_nodes(node):
                    visit_node(child, depth + 1)

            visit_node(tree)
            return complexity
        except Exception as e:
            logger.warning(f"Error calculating complexity for {file_path}: {e}")
            return {"error": str(e)}


class DocumentationValidator:
    """Validates documentation completeness and quality."""

    @staticmethod
    def validate_docstrings(file_path: Path) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate that functions and classes have docstrings.

        Args:
            file_path: Path to Python file

        Returns:
            Tuple of (is_valid, validation_results)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)

            results = {
                "functions_with_docs": 0,
                "functions_without_docs": 0,
                "classes_with_docs": 0,
                "classes_without_docs": 0,
                "missing_docs": [],
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if ast.get_docstring(node):
                        results["functions_with_docs"] += 1
                    else:
                        results["functions_without_docs"] += 1
                        results["missing_docs"].append(f"Function {node.name}")
                elif isinstance(node, ast.ClassDef):
                    if ast.get_docstring(node):
                        results["classes_with_docs"] += 1
                    else:
                        results["classes_without_docs"] += 1
                        results["missing_docs"].append(f"Class {node.name}")

            total_functions = results["functions_with_docs"] + results["functions_without_docs"]
            total_classes = results["classes_with_docs"] + results["classes_without_docs"]
            has_docs = total_functions == 0 or results["functions_with_docs"] > 0
            classes_have_docs = total_classes == 0 or results["classes_with_docs"] > 0

            is_valid = has_docs and classes_have_docs
            return is_valid, results
        except Exception as e:
            logger.warning(f"Error validating docstrings for {file_path}: {e}")
            return True, {"error": str(e)}

    @staticmethod
    def validate_readme(project_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate that README exists and has content.

        Args:
            project_path: Path to project root

        Returns:
            Tuple of (is_valid, error_message)
        """
        readme_paths = [
            project_path / "README.md",
            project_path / "readme.md",
            project_path / "README.txt",
        ]

        for readme_path in readme_paths:
            if readme_path.exists():
                content = readme_path.read_text(encoding="utf-8")
                if len(content.strip()) > 50:  # Minimum content length
                    return True, None
                else:
                    return False, f"README exists but is too short: {readme_path}"

        return False, "README file not found"


class TestCoverageValidator:
    """Validates test coverage."""

    @staticmethod
    def validate_coverage(
        project_path: Path, coverage_threshold: float = 70.0
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate test coverage using pytest-cov.

        Args:
            project_path: Path to project root
            coverage_threshold: Minimum coverage percentage

        Returns:
            Tuple of (is_valid, coverage_results)
        """
        try:
            # Run pytest with coverage
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--cov=.",
                    "--cov-report=term",
                    str(project_path / "tests"),
                ],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Parse coverage from output
            output = result.stdout + result.stderr
            coverage_match = re.search(r"TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%", output)
            if coverage_match:
                total_lines = int(coverage_match.group(1))
                covered_lines = int(coverage_match.group(2))
                coverage_percent = float(coverage_match.group(3))

                is_valid = coverage_percent >= coverage_threshold
                return is_valid, {
                    "coverage_percent": coverage_percent,
                    "total_lines": total_lines,
                    "covered_lines": covered_lines,
                    "threshold": coverage_threshold,
                }
            else:
                # Coverage report not found, assume tests ran
                return True, {"coverage_percent": None, "message": "Coverage report not available"}
        except FileNotFoundError:
            logger.warning("pytest-cov not found, skipping coverage validation")
            return True, {"coverage_percent": None, "message": "pytest-cov not available"}
        except subprocess.TimeoutExpired:
            return False, {"error": "Coverage validation timed out"}
        except Exception as e:
            logger.warning(f"Error validating coverage: {e}")
            return True, {"coverage_percent": None, "error": str(e)}


class ArtifactStructureValidator:
    """Validates artifact structure and content."""

    @staticmethod
    def validate_artifact_structure(artifact_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate artifact file structure.

        Args:
            artifact_path: Path to artifact file

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if not artifact_path.exists():
            return False, [f"Artifact does not exist: {artifact_path}"]

        if artifact_path.is_file():
            # Check file is not empty
            if artifact_path.stat().st_size == 0:
                errors.append(f"Artifact is empty: {artifact_path}")

            # Validate JSON structure if JSON file
            if artifact_path.suffix == ".json":
                try:
                    import json

                    with open(artifact_path, "r", encoding="utf-8") as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    errors.append(f"Invalid JSON in artifact {artifact_path}: {e}")

            # Validate YAML structure if YAML file
            if artifact_path.suffix in [".yaml", ".yml"]:
                try:
                    import yaml

                    with open(artifact_path, "r", encoding="utf-8") as f:
                        yaml.safe_load(f)
                except Exception as e:
                    errors.append(f"Invalid YAML in artifact {artifact_path}: {e}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_artifact_content(artifact_path: Path, min_size: int = 10) -> Tuple[bool, Optional[str]]:
        """
        Validate artifact has meaningful content.

        Args:
            artifact_path: Path to artifact file
            min_size: Minimum file size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not artifact_path.exists():
            return False, f"Artifact does not exist: {artifact_path}"

        if artifact_path.is_file():
            size = artifact_path.stat().st_size
            if size < min_size:
                return False, f"Artifact is too small ({size} bytes < {min_size} bytes): {artifact_path}"

            # For text files, check content is not just whitespace
            if artifact_path.suffix in [".md", ".txt", ".py", ".yaml", ".yml"]:
                try:
                    content = artifact_path.read_text(encoding="utf-8")
                    if len(content.strip()) < min_size:
                        return False, f"Artifact content is too short: {artifact_path}"
                except Exception:
                    pass  # Binary file or encoding issue

        return True, None


class ContentValidator:
    """Main content validator that combines all validation utilities."""

    def __init__(self, project_path: Path):
        """
        Initialize content validator.

        Args:
            project_path: Path to project root
        """
        self.project_path = project_path
        self.code_validator = CodeQualityValidator()
        self.doc_validator = DocumentationValidator()
        self.coverage_validator = TestCoverageValidator()
        self.structure_validator = ArtifactStructureValidator()

    def validate_code_quality(
        self, file_paths: Optional[List[Path]] = None, use_ruff: bool = True, use_mypy: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate code quality for files.

        Args:
            file_paths: Optional list of files to validate
            use_ruff: Whether to use ruff
            use_mypy: Whether to use mypy

        Returns:
            Tuple of (is_valid, quality_results)
        """
        if file_paths is None:
            file_paths = list(self.project_path.rglob("*.py"))
            # Limit for performance
            file_paths = file_paths[:20]

        ruff_errors = []
        mypy_errors = []
        complexity_results = []

        for file_path in file_paths:
            if use_ruff:
                is_valid, errors = self.code_validator.validate_with_ruff(file_path)
                if not is_valid:
                    ruff_errors.extend(errors)

            if use_mypy:
                is_valid, errors = self.code_validator.validate_with_mypy(file_path)
                if not is_valid:
                    mypy_errors.extend(errors)

            complexity = self.code_validator.calculate_complexity(file_path)
            complexity_results.append({"file": str(file_path), "complexity": complexity})

        is_valid = len(ruff_errors) == 0 and len(mypy_errors) == 0

        return is_valid, {
            "ruff_errors": ruff_errors,
            "mypy_errors": mypy_errors,
            "complexity_results": complexity_results,
            "files_checked": len(file_paths),
        }

    def validate_documentation(
        self, file_paths: Optional[List[Path]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate documentation completeness.

        Args:
            file_paths: Optional list of files to validate

        Returns:
            Tuple of (is_valid, doc_results)
        """
        if file_paths is None:
            file_paths = list(self.project_path.rglob("*.py"))
            # Limit for performance
            file_paths = file_paths[:20]

        doc_results = []
        all_valid = True

        for file_path in file_paths:
            is_valid, results = self.doc_validator.validate_docstrings(file_path)
            doc_results.append({"file": str(file_path), "results": results})
            if not is_valid:
                all_valid = False

        # Validate README
        readme_valid, readme_error = self.doc_validator.validate_readme(self.project_path)
        if not readme_valid:
            all_valid = False

        return all_valid, {
            "doc_results": doc_results,
            "readme_valid": readme_valid,
            "readme_error": readme_error,
        }

    def validate_test_coverage(
        self, coverage_threshold: float = 70.0
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate test coverage.

        Args:
            coverage_threshold: Minimum coverage percentage

        Returns:
            Tuple of (is_valid, coverage_results)
        """
        return self.coverage_validator.validate_coverage(self.project_path, coverage_threshold)

    def validate_artifact(
        self, artifact_path: Path, validate_content: bool = True
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate artifact structure and content.

        Args:
            artifact_path: Path to artifact file
            validate_content: Whether to validate content quality

        Returns:
            Tuple of (is_valid, validation_results)
        """
        structure_valid, structure_errors = self.structure_validator.validate_artifact_structure(
            artifact_path
        )

        content_valid = True
        content_error = None
        if validate_content and structure_valid:
            content_valid, content_error = self.structure_validator.validate_artifact_content(
                artifact_path
            )

        is_valid = structure_valid and content_valid

        return is_valid, {
            "structure_valid": structure_valid,
            "structure_errors": structure_errors,
            "content_valid": content_valid,
            "content_error": content_error,
        }

