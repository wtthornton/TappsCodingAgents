"""
Dependency validation utilities for E2E tests.

Provides pre-flight dependency validation that fails tests immediately
when required dependencies are missing, instead of skipping tests.
"""

import inspect
from pathlib import Path
from typing import Any

import pytest

from .error_helpers import build_error_context, format_dependency_error
from .validation_modes import ValidationMode, get_validation_mode


def validate_workflow_file(workflow_path: Path, mode: ValidationMode | None = None) -> None:
    """
    Validate that a workflow file exists.
    
    Args:
        workflow_path: Path to workflow file
        mode: Validation mode (defaults to STRICT)
        
    Raises:
        pytest.fail: If workflow file doesn't exist (in strict mode)
        FileNotFoundError: If workflow file doesn't exist (in strict mode)
    """
    mode = get_validation_mode(mode)
    
    if not workflow_path.exists():
        context = build_error_context()
        error_msg = format_dependency_error(
            dependency_type="workflow_file",
            dependency_name=workflow_path.name,
            expected_path=workflow_path,
            context=context,
        )
        
        if mode == ValidationMode.STRICT:
            pytest.fail(error_msg)
        else:
            raise FileNotFoundError(error_msg)


def validate_scenario_template(template_path: Path, mode: ValidationMode | None = None) -> None:
    """
    Validate that a scenario template exists.
    
    Args:
        template_path: Path to scenario template
        mode: Validation mode (defaults to STRICT)
        
    Raises:
        pytest.fail: If template doesn't exist (in strict mode)
        FileNotFoundError: If template doesn't exist (in strict mode)
    """
    mode = get_validation_mode(mode)
    
    if not template_path.exists():
        context = build_error_context()
        error_msg = format_dependency_error(
            dependency_type="template",
            dependency_name=template_path.name,
            expected_path=template_path,
            context=context,
        )
        
        if mode == ValidationMode.STRICT:
            pytest.fail(error_msg)
        else:
            raise FileNotFoundError(error_msg)


def validate_project_structure(
    project_path: Path,
    required_dirs: list[str] | None = None,
    required_files: list[str] | None = None,
    mode: ValidationMode | None = None,
) -> None:
    """
    Validate that project structure has required directories and files.
    
    Args:
        project_path: Path to project root
        required_dirs: List of required directory names (relative to project_path)
        required_files: List of required file names (relative to project_path)
        mode: Validation mode (defaults to STRICT)
        
    Raises:
        pytest.fail: If required structure is missing (in strict mode)
        FileNotFoundError: If required structure is missing (in strict mode)
    """
    mode = get_validation_mode(mode)
    missing_items = []
    
    if required_dirs:
        for dir_name in required_dirs:
            dir_path = project_path / dir_name
            if not dir_path.exists() or not dir_path.is_dir():
                missing_items.append(f"directory: {dir_name}")
    
    if required_files:
        for file_name in required_files:
            file_path = project_path / file_name
            if not file_path.exists() or not file_path.is_file():
                missing_items.append(f"file: {file_name}")
    
    if missing_items:
        context = build_error_context()
        error_msg = format_dependency_error(
            dependency_type="project_structure",
            dependency_name=", ".join(missing_items),
            expected_path=project_path,
            context=context,
        )
        
        if mode == ValidationMode.STRICT:
            pytest.fail(error_msg)
        else:
            raise FileNotFoundError(error_msg)


def validate_required_fixtures(fixture_names: list[str], request: Any | None = None) -> None:
    """
    Validate that required pytest fixtures are available.
    
    Args:
        fixture_names: List of required fixture names
        request: Pytest request object (optional, will try to get from stack)
        
    Raises:
        pytest.fail: If required fixtures are missing
    """
    if request is None:
        # Try to get request from call stack
        frame = inspect.currentframe()
        try:
            # Go up the stack to find request
            for _ in range(10):
                frame = frame.f_back
                if frame is None:
                    break
                if "request" in frame.f_locals:
                    request = frame.f_locals["request"]
                    break
        finally:
            del frame
    
    if request is None:
        # Can't validate without request, skip validation
        return
    
    missing_fixtures = []
    for fixture_name in fixture_names:
        try:
            request.getfixturevalue(fixture_name)
        except Exception:
            missing_fixtures.append(fixture_name)
    
    if missing_fixtures:
        context = build_error_context()
        error_msg = format_dependency_error(
            dependency_type="fixture",
            dependency_name=", ".join(missing_fixtures),
            expected_path=None,
            context=context,
        )
        pytest.fail(error_msg)


def validate_dependencies(
    workflow_path: Path | None = None,
    template_path: Path | None = None,
    project_path: Path | None = None,
    required_dirs: list[str] | None = None,
    required_files: list[str] | None = None,
    required_fixtures: list[str] | None = None,
    request: Any | None = None,
    mode: ValidationMode | None = None,
) -> None:
    """
    Validate all dependencies in one call.
    
    Args:
        workflow_path: Optional path to workflow file
        template_path: Optional path to scenario template
        project_path: Optional path to project root
        required_dirs: Optional list of required directories
        required_files: Optional list of required files
        required_fixtures: Optional list of required fixture names
        request: Optional pytest request object
        mode: Validation mode (defaults to STRICT)
        
    Raises:
        pytest.fail: If any dependency is missing (in strict mode)
        FileNotFoundError: If any dependency is missing (in strict mode)
    """
    if workflow_path:
        validate_workflow_file(workflow_path, mode)
    
    if template_path:
        validate_scenario_template(template_path, mode)
    
    if project_path and (required_dirs or required_files):
        validate_project_structure(project_path, required_dirs, required_files, mode)
    
    if required_fixtures:
        validate_required_fixtures(required_fixtures, request)

