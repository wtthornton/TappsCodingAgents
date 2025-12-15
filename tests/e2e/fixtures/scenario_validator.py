"""
Scenario validation utilities for E2E scenario tests.

Provides utilities to validate scenario outcomes against expected outputs:
- File changes validation
- Artifact validation
- Test outcome validation (actually runs tests)
- Quality signal validation
- Code correctness validation
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from .e2e_harness import assert_artifact_exists
from .error_helpers import (
    build_error_context,
    format_artifact_error,
    format_execution_error,
    format_file_error,
    format_validation_error,
)
from .outcome_validator import OutcomeValidator
from .scenario_templates import ScenarioType, TemplateType, get_expected_outputs
from .validation_modes import ValidationMode, get_validation_mode, is_strict_mode

# Configure logging
logger = logging.getLogger(__name__)


class ScenarioValidator:
    """Validator for scenario test outcomes."""

    def __init__(
        self,
        project_path: Path,
        scenario_type: ScenarioType,
        template_size: TemplateType,
        run_tests: bool = True,
        mode: Optional[ValidationMode] = None,
    ):
        """
        Initialize scenario validator.

        Args:
            project_path: Path to the test project
            scenario_type: Type of scenario (feature, bug_fix, refactor)
            template_size: Size of template (small, medium)
            run_tests: Whether to actually run tests (default: True)
            mode: Validation mode (STRICT or RELAXED, defaults to STRICT)
        """
        self.project_path = project_path
        self.scenario_type = scenario_type
        self.template_size = template_size
        self.expected_outputs = get_expected_outputs(scenario_type, template_size)
        self.validation_errors: List[str] = []
        self.run_tests = run_tests and os.getenv("E2E_SKIP_TEST_EXECUTION") != "true"
        self.outcome_validator = OutcomeValidator(project_path)
        self.mode = get_validation_mode(mode)

    def validate_all(self) -> bool:
        """
        Validate all scenario outcomes.

        In STRICT mode: Fails immediately on first error by raising exception.
        In RELAXED mode: Collects all errors and fails at end if any errors found.

        Returns:
            True if all validations pass, False otherwise (only in RELAXED mode)
            
        Raises:
            AssertionError: If validation fails in STRICT mode
        """
        self.validation_errors.clear()
        context = build_error_context(
            scenario_type=self.scenario_type,
            operation="validate_all",
        )

        try:
            # Validate file changes
            self._validate_file_changes()

            # Validate artifacts
            self._validate_artifacts()

            # Validate test outcomes (actually runs tests if enabled)
            self._validate_test_outcomes()

            # Validate quality signals (including code quality)
            self._validate_quality_signals()

            # Scenario-specific validation
            if self.scenario_type == "bug_fix":
                self._validate_bug_fix()
            elif self.scenario_type == "feature":
                self._validate_feature()
            elif self.scenario_type == "refactor":
                self._validate_refactor()
        except Exception as e:
            # In strict mode, propagate exception immediately
            if is_strict_mode(self.mode):
                raise
            # In relaxed mode, collect error and continue
            error_msg = format_execution_error("validation", e, context, include_traceback=False)
            self.validation_errors.append(error_msg)

        # Check if any errors were collected
        if len(self.validation_errors) > 0:
            if is_strict_mode(self.mode):
                # Should not reach here in strict mode (exceptions should have been raised)
                # But if we do, fail immediately
                error_msg = "\n".join(self.validation_errors)
                pytest.fail(f"Validation failed:\n{error_msg}")
            else:
                # In relaxed mode, fail with all errors
                error_msg = "\n".join(self.validation_errors)
                pytest.fail(f"Validation failed with {len(self.validation_errors)} error(s):\n{error_msg}")

        return len(self.validation_errors) == 0

    def _validate_bug_fix(self) -> None:
        """Validate bug fix scenario - verify bug is actually fixed."""
        context = build_error_context(
            scenario_type=self.scenario_type,
            operation="validate_bug_fix",
        )
        
        # Get bug description from BUG_REPORT.md if it exists
        bug_report = self.project_path / "BUG_REPORT.md"
        bug_description = "Bug fix validation"
        if bug_report.exists():
            bug_description = bug_report.read_text(encoding="utf-8")[:200]

        # Validate bug fix using outcome validator
        is_valid, results = self.outcome_validator.validate_bug_fix(
            bug_description=bug_description
        )
        if not is_valid:
            if not results.get("tests_passed", False):
                error_msg = "Bug fix validation failed: tests did not pass"
                if is_strict_mode(self.mode):
                    pytest.fail(format_validation_error("bug_fix_validation", error_msg, context=context))
                else:
                    self.validation_errors.append(error_msg)
            if not results.get("syntax_valid", True):
                syntax_errors = results.get("syntax_errors", [])
                if is_strict_mode(self.mode):
                    error_msg = f"Bug fix validation failed: syntax errors found: {', '.join(syntax_errors)}"
                    pytest.fail(format_validation_error("bug_fix_validation", error_msg, context=context))
                else:
                    self.validation_errors.extend(syntax_errors)

    def _validate_feature(self) -> None:
        """Validate feature scenario - verify feature works correctly."""
        context = build_error_context(
            scenario_type=self.scenario_type,
            operation="validate_feature",
        )
        
        # Get feature description if available
        feature_description = "Feature implementation validation"

        # Validate feature using outcome validator
        is_valid, results = self.outcome_validator.validate_feature(
            feature_description=feature_description
        )
        if not is_valid:
            if not results.get("tests_passed", False):
                error_msg = "Feature validation failed: tests did not pass"
                if is_strict_mode(self.mode):
                    pytest.fail(format_validation_error("feature_validation", error_msg, context=context))
                else:
                    self.validation_errors.append(error_msg)
            if not results.get("syntax_valid", True):
                syntax_errors = results.get("syntax_errors", [])
                if is_strict_mode(self.mode):
                    error_msg = f"Feature validation failed: syntax errors found: {', '.join(syntax_errors)}"
                    pytest.fail(format_validation_error("feature_validation", error_msg, context=context))
                else:
                    self.validation_errors.extend(syntax_errors)
            style_errors = results.get("style_errors", [])
            if style_errors:
                error_msg = f"Feature validation: {len(style_errors)} files with style issues"
                if is_strict_mode(self.mode):
                    pytest.fail(format_validation_error("feature_validation", error_msg, context=context))
                else:
                    self.validation_errors.append(error_msg)

    def _validate_refactor(self) -> None:
        """Validate refactor scenario - verify code quality improved."""
        context = build_error_context(
            scenario_type=self.scenario_type,
            operation="validate_refactor",
        )
        
        # Validate code quality
        quality_valid, quality_results = self.outcome_validator.validate_quality(
            use_ruff=True, use_mypy=False
        )
        if not quality_valid:
            ruff_errors = quality_results.get("ruff_errors", [])
            if ruff_errors:
                error_msg = f"Refactor validation: {len(ruff_errors)} files with quality issues"
                if is_strict_mode(self.mode):
                    pytest.fail(format_validation_error("refactor_validation", error_msg, context=context))
                else:
                    self.validation_errors.append(error_msg)

        # Validate syntax
        syntax_valid, syntax_errors = self.outcome_validator.validate_code_correctness()
        if not syntax_valid:
            if is_strict_mode(self.mode):
                error_msg = f"Refactor validation failed: syntax errors found: {', '.join(syntax_errors)}"
                pytest.fail(format_validation_error("refactor_validation", error_msg, context=context))
            else:
                self.validation_errors.extend(syntax_errors)

    def _validate_file_changes(self) -> None:
        """Validate expected file changes."""
        expected = self.expected_outputs.get("file_changes", {})
        new_files = expected.get("new_files", [])
        modified_files = expected.get("modified_files", [])
        
        context = build_error_context(
            scenario_type=self.scenario_type,
            operation="validate_file_changes",
        )

        # Check new files exist - fail immediately in strict mode
        for file_path in new_files:
            full_path = self.project_path / file_path
            if not full_path.exists():
                error_msg = format_file_error(full_path, file_type="new file", context=context)
                if is_strict_mode(self.mode):
                    pytest.fail(error_msg)
                else:
                    self.validation_errors.append(error_msg)

        # Check modified files exist (they should exist in base template) - fail immediately in strict mode
        for file_path in modified_files:
            full_path = self.project_path / file_path
            if not full_path.exists():
                error_msg = format_file_error(full_path, file_type="modified file", context=context)
                if is_strict_mode(self.mode):
                    pytest.fail(error_msg)
                else:
                    self.validation_errors.append(error_msg)

    def _validate_artifacts(self) -> None:
        """Validate expected artifacts - no fallback paths, fail immediately if missing."""
        expected = self.expected_outputs.get("artifacts", {})
        artifacts_dir = self.project_path / ".tapps-agents" / "artifacts"
        
        context = build_error_context(
            scenario_type=self.scenario_type,
            operation="validate_artifacts",
        )

        # Validate artifacts by type - use explicit path, no fallback
        artifact_types = ["planning", "design", "code", "review", "test", "docs"]
        for artifact_type in artifact_types:
            for artifact in expected.get(artifact_type, []):
                # Use explicit path: artifacts_dir / artifact_type / artifact_name
                # No fallback to project root
                artifact_path = artifacts_dir / artifact_type / artifact
                
                if not artifact_path.exists():
                    error_msg = format_artifact_error(
                        artifact_type=artifact_type,
                        artifact_name=artifact,
                        expected_path=artifact_path,
                        context=context,
                    )
                    if is_strict_mode(self.mode):
                        pytest.fail(error_msg)
                    else:
                        self.validation_errors.append(error_msg)

    def _validate_test_outcomes(self) -> None:
        """Validate test outcomes by actually running tests."""
        expected = self.expected_outputs.get("test_outcomes", {})
        
        context = build_error_context(
            scenario_type=self.scenario_type,
            operation="validate_test_outcomes",
        )

        if expected.get("all_tests_pass", False):
            # Check that test files exist - fail immediately in strict mode
            test_dir = self.project_path / "tests"
            if not test_dir.exists():
                error_msg = format_file_error(test_dir, file_type="tests directory", context=context)
                if is_strict_mode(self.mode):
                    pytest.fail(error_msg)
                else:
                    self.validation_errors.append(error_msg)
                    return

            test_files = list(test_dir.glob("test_*.py"))
            if len(test_files) == 0:
                error_msg = format_validation_error(
                    "missing_test_files",
                    "No test files found in tests directory",
                    expected="test_*.py files",
                    actual="0 files",
                    context=context,
                    suggestion="Ensure test files exist in tests/ directory",
                )
                if is_strict_mode(self.mode):
                    pytest.fail(error_msg)
                else:
                    self.validation_errors.append(error_msg)
                    return

            # Actually run tests if enabled
            if self.run_tests:
                tests_passed, test_results = self.outcome_validator.validate_tests(
                    test_path=test_dir, timeout=300
                )
                if not tests_passed:
                    error_msg = f"Tests failed: {test_results.get('error', 'Unknown error')}"
                    if "stdout" in test_results:
                        error_msg += f"\nTest output:\n{test_results['stdout']}"
                    if "stderr" in test_results:
                        error_msg += f"\nTest errors:\n{test_results['stderr']}"
                    formatted_error = format_execution_error("test_execution", Exception(error_msg), context)
                    if is_strict_mode(self.mode):
                        pytest.fail(formatted_error)
                    else:
                        self.validation_errors.append(formatted_error)
                else:
                    # Validate test counts if available
                    test_counts = test_results.get("test_counts", {})
                    if test_counts.get("failed", 0) > 0:
                        error_msg = (
                            f"Tests failed: {test_counts['failed']} failed, "
                            f"{test_counts['passed']} passed"
                        )
                        formatted_error = format_execution_error("test_execution", Exception(error_msg), context)
                        if is_strict_mode(self.mode):
                            pytest.fail(formatted_error)
                        else:
                            self.validation_errors.append(formatted_error)

    def _validate_quality_signals(self) -> None:
        """Validate quality signals including code quality."""
        expected = self.expected_outputs.get("quality_signals", {})
        
        context = build_error_context(
            scenario_type=self.scenario_type,
            operation="validate_quality_signals",
        )

        # Check quality gate state (if workflow state exists)
        if expected.get("gates_pass", False):
            state_dir = self.project_path / ".tapps-agents" / "workflow-state"
            if state_dir.exists():
                # Check for workflow state files
                state_files = list(state_dir.glob("*.json"))
                if len(state_files) == 0:
                    # This is not an error - workflow might not have persisted state
                    logger.debug("No workflow state files found (this may be expected)")

        # Validate code quality if requested
        if expected.get("code_quality_valid", False):
            # Validate code syntax
            syntax_valid, syntax_errors = self.outcome_validator.validate_code_correctness()
            if not syntax_valid:
                if is_strict_mode(self.mode):
                    error_msg = f"Code quality validation failed: syntax errors found: {', '.join(syntax_errors)}"
                    pytest.fail(format_validation_error("quality_validation", error_msg, context=context))
                else:
                    self.validation_errors.extend(syntax_errors)

            # Validate code quality (linting)
            quality_valid, quality_results = self.outcome_validator.validate_quality(
                use_ruff=True, use_mypy=False
            )
            if not quality_valid:
                ruff_errors = quality_results.get("ruff_errors", [])
                if ruff_errors:
                    error_msg = f"Code quality issues found: {len(ruff_errors)} files with linting errors"
                    if is_strict_mode(self.mode):
                        pytest.fail(format_validation_error("quality_validation", error_msg, context=context))
                    else:
                        self.validation_errors.append(error_msg)

    def get_validation_errors(self) -> List[str]:
        """
        Get list of validation errors.

        Returns:
            List of validation error messages
        """
        return self.validation_errors.copy()

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get validation summary.

        Returns:
            Dictionary with validation summary
        """
        return {
            "scenario_type": self.scenario_type,
            "template_size": self.template_size,
            "valid": len(self.validation_errors) == 0,
            "error_count": len(self.validation_errors),
            "errors": self.validation_errors,
            "expected_outputs": self.expected_outputs,
        }

