"""
Error message utilities for E2E tests.

Provides standardized error message formatting with context, expected/actual values,
and actionable suggestions for fixing issues.
"""

import inspect
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional


def build_error_context(
    test_name: Optional[str] = None,
    scenario_type: Optional[str] = None,
    workflow_id: Optional[str] = None,
    step_id: Optional[str] = None,
    operation: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build error context dictionary.
    
    Args:
        test_name: Name of the test
        scenario_type: Type of scenario (feature, bug_fix, refactor)
        workflow_id: ID of the workflow
        step_id: ID of the current step
        operation: Current operation being performed
        
    Returns:
        Dictionary with error context
    """
    context = {}
    
    if test_name:
        context["test_name"] = test_name
    if scenario_type:
        context["scenario_type"] = scenario_type
    if workflow_id:
        context["workflow_id"] = workflow_id
    if step_id:
        context["step_id"] = step_id
    if operation:
        context["operation"] = operation
    
    # Try to get test name from call stack if not provided
    if not test_name:
        frame = inspect.currentframe()
        try:
            # Go up the stack to find test function
            for _ in range(5):
                frame = frame.f_back
                if frame is None:
                    break
                func_name = frame.f_code.co_name
                if func_name.startswith("test_"):
                    context["test_name"] = func_name
                    break
        finally:
            del frame
    
    return context


def format_validation_error(
    error_type: str,
    message: str,
    expected: Optional[Any] = None,
    actual: Optional[Any] = None,
    context: Optional[Dict[str, Any]] = None,
    suggestion: Optional[str] = None,
) -> str:
    """
    Format a validation error message.
    
    Args:
        error_type: Type of validation error (e.g., "missing_artifact", "file_not_found")
        message: Base error message
        expected: Expected value
        actual: Actual value
        context: Error context dictionary
        suggestion: Suggested fix action
        
    Returns:
        Formatted error message
    """
    parts = []
    
    # Add context
    if context:
        context_parts = []
        if "test_name" in context:
            context_parts.append(f"test: {context['test_name']}")
        if "scenario_type" in context:
            context_parts.append(f"scenario: {context['scenario_type']}")
        if "workflow_id" in context:
            context_parts.append(f"workflow: {context['workflow_id']}")
        if "step_id" in context:
            context_parts.append(f"step: {context['step_id']}")
        if "operation" in context:
            context_parts.append(f"operation: {context['operation']}")
        
        if context_parts:
            parts.append(f"[{' | '.join(context_parts)}]")
    
    # Add error type and message
    parts.append(f"{error_type}: {message}")
    
    # Add expected vs actual
    if expected is not None or actual is not None:
        expected_str = str(expected) if expected is not None else "None"
        actual_str = str(actual) if actual is not None else "None"
        parts.append(f"Expected: {expected_str}")
        parts.append(f"Actual: {actual_str}")
    
    # Add suggestion
    if suggestion:
        parts.append(f"Suggestion: {suggestion}")
    
    return "\n".join(parts)


def format_dependency_error(
    dependency_type: str,
    dependency_name: str,
    expected_path: Optional[Path] = None,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Format a missing dependency error message.
    
    Args:
        dependency_type: Type of dependency (e.g., "workflow_file", "template", "fixture")
        dependency_name: Name of the dependency
        expected_path: Expected path to the dependency
        context: Error context dictionary
        
    Returns:
        Formatted error message
    """
    message = f"Missing {dependency_type}: {dependency_name}"
    
    suggestion_parts = []
    if expected_path:
        message += f"\nExpected location: {expected_path}"
        suggestion_parts.append(f"Ensure {dependency_type} exists at {expected_path}")
    else:
        suggestion_parts.append(f"Ensure {dependency_type} '{dependency_name}' is available")
    
    if dependency_type == "workflow_file":
        suggestion_parts.append("Check that workflow file exists in workflows/ or workflows/presets/")
    elif dependency_type == "template":
        suggestion_parts.append("Check that scenario template is properly configured")
    elif dependency_type == "fixture":
        suggestion_parts.append("Check that required pytest fixtures are available")
    
    suggestion = " | ".join(suggestion_parts)
    
    return format_validation_error(
        error_type="missing_dependency",
        message=message,
        expected=expected_path,
        context=context,
        suggestion=suggestion,
    )


def format_execution_error(
    operation: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    include_traceback: bool = True,
) -> str:
    """
    Format an execution error message.
    
    Args:
        operation: Operation that failed
        error: Exception that was raised
        context: Error context dictionary
        include_traceback: Whether to include stack trace
        
    Returns:
        Formatted error message
    """
    message = f"Execution failed during {operation}: {str(error)}"
    
    suggestion = f"Check that {operation} can execute successfully. Review error details below."
    
    error_msg = format_validation_error(
        error_type="execution_error",
        message=message,
        context=context,
        suggestion=suggestion,
    )
    
    if include_traceback:
        error_msg += f"\n\nStack trace:\n{traceback.format_exc()}"
    
    return error_msg


def format_artifact_error(
    artifact_type: str,
    artifact_name: str,
    expected_path: Path,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Format a missing artifact error message.
    
    Args:
        artifact_type: Type of artifact (planning, design, code, review, test, docs)
        artifact_name: Name of the artifact
        expected_path: Expected path to the artifact
        context: Error context dictionary
        
    Returns:
        Formatted error message
    """
    message = f"Expected {artifact_type} artifact not found: {artifact_name}"
    message += f"\nExpected location: {expected_path}"
    
    suggestion = (
        f"Ensure {artifact_type} artifact '{artifact_name}' exists at {expected_path}. "
        f"Artifacts should be created at: .tapps-agents/artifacts/{artifact_type}/{artifact_name}"
    )
    
    return format_validation_error(
        error_type="missing_artifact",
        message=message,
        expected=expected_path,
        context=context,
        suggestion=suggestion,
    )


def format_file_error(
    file_path: Path,
    file_type: str = "file",
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Format a missing file error message.
    
    Args:
        file_path: Path to the missing file
        file_type: Type of file (file, test_file, etc.)
        context: Error context dictionary
        
    Returns:
        Formatted error message
    """
    message = f"Expected {file_type} not found: {file_path}"
    
    suggestion = f"Ensure {file_type} exists at {file_path}"
    
    return format_validation_error(
        error_type="missing_file",
        message=message,
        expected=file_path,
        context=context,
        suggestion=suggestion,
    )

