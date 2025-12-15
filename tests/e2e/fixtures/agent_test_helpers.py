"""
Agent Test Helper Utilities for E2E Tests.

Provides utilities for testing agent behavior:
- Command parsing and validation
- Response validation
- Error scenario creation
- Agent-specific validation
"""

import ast
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from tapps_agents.core.agent_base import BaseAgent
from tapps_agents.core.mal import MAL


def create_test_agent(agent_type: str, mock_mal: MAL, config=None) -> BaseAgent:
    """
    Create a test agent instance with mocked MAL.

    Args:
        agent_type: Type of agent (planner, implementer, reviewer, tester)
        mock_mal: Mocked MAL instance
        config: Optional project config

    Returns:
        Agent instance
    """
    if agent_type == "planner":
        from tapps_agents.agents.planner.agent import PlannerAgent

        return PlannerAgent(mal=mock_mal, config=config)
    elif agent_type == "implementer":
        from tapps_agents.agents.implementer.agent import ImplementerAgent

        return ImplementerAgent(mal=mock_mal, config=config)
    elif agent_type == "reviewer":
        from tapps_agents.agents.reviewer.agent import ReviewerAgent

        return ReviewerAgent(mal=mock_mal, config=config)
    elif agent_type == "tester":
        from tapps_agents.agents.tester.agent import TesterAgent

        return TesterAgent(mal=mock_mal, config=config)
    else:
        raise ValueError(f"Unsupported agent type: {agent_type}")


async def execute_command(
    agent: BaseAgent, command: str, **kwargs
) -> Dict[str, Any]:
    """
    Execute a command on an agent and return the response.

    Args:
        agent: Agent instance
        command: Command to execute (with or without * prefix)
        **kwargs: Additional command arguments

    Returns:
        Agent response dictionary
    """
    # Parse command to get base command name
    parsed_command, parsed_args = agent.parse_command(command)
    # Merge parsed args with kwargs
    merged_kwargs = {**parsed_args, **kwargs}
    # Execute command
    return await agent.run(parsed_command, **merged_kwargs)


def assert_command_parsed(
    parsed_result: tuple[str, Dict[str, str]],
    expected_command: str,
    expected_args: Optional[Dict[str, str]] = None,
) -> None:
    """
    Assert that a command was parsed correctly.

    Args:
        parsed_result: Result from parse_command (command, args)
        expected_command: Expected command name
        expected_args: Expected arguments (optional)
    """
    command, args = parsed_result
    assert command == expected_command, f"Expected command '{expected_command}', got '{command}'"
    if expected_args is not None:
        assert args == expected_args, f"Expected args {expected_args}, got {args}"


def assert_error_message(
    error_response: Dict[str, Any], expected_keywords: List[str]
) -> None:
    """
    Assert that an error message contains expected keywords.

    Args:
        error_response: Agent response dictionary (should contain 'error' key)
        expected_keywords: List of keywords that should appear in error message
    """
    assert "error" in error_response, "Response should contain 'error' key"
    error_msg = str(error_response["error"]).lower()
    for keyword in expected_keywords:
        assert keyword.lower() in error_msg, f"Error message should contain '{keyword}'"


def validate_help_output(help_response: Dict[str, Any]) -> None:
    """
    Validate that help output has correct structure.

    Args:
        help_response: Agent help response
    """
    assert "type" in help_response, "Help response should have 'type' field"
    assert help_response["type"] == "help", "Help response type should be 'help'"
    assert "content" in help_response, "Help response should have 'content' field"
    content = help_response["content"]
    assert isinstance(content, str), "Help content should be a string"
    assert len(content) > 0, "Help content should not be empty"


def validate_response_structure(
    response: Dict[str, Any], required_fields: List[str]
) -> None:
    """
    Validate that response has required fields.

    Args:
        response: Agent response dictionary
        required_fields: List of required field names
    """
    for field in required_fields:
        assert field in response, f"Response should contain '{field}' field"


def validate_response_content(
    response: Dict[str, Any], expected_data: Dict[str, Any]
) -> None:
    """
    Validate that response contains expected data.

    Args:
        response: Agent response dictionary
        expected_data: Dictionary of expected field values
    """
    for key, expected_value in expected_data.items():
        assert key in response, f"Response should contain '{key}' field"
        actual_value = response[key]
        if isinstance(expected_value, str) and isinstance(actual_value, str):
            # For strings, check if expected is a substring
            assert expected_value.lower() in actual_value.lower(), (
                f"Response field '{key}' should contain '{expected_value}'"
            )
        else:
            assert actual_value == expected_value, (
                f"Response field '{key}' should be '{expected_value}', got '{actual_value}'"
            )


def validate_response_context(
    response: Dict[str, Any], command: str, agent_type: str
) -> None:
    """
    Validate that response is contextually appropriate for command and agent.

    Args:
        response: Agent response dictionary
        command: Command that was executed
        agent_type: Type of agent
    """
    # Basic validation - response should not be empty
    assert response, "Response should not be empty"
    # Response should not be a generic error for valid commands
    if "error" in response and command != "help":
        # Some commands may legitimately return errors, but they should be specific
        error_msg = str(response["error"]).lower()
        assert "unknown" not in error_msg or "help" in error_msg, (
            f"Response should not contain generic 'unknown' error for command '{command}'"
        )


def assert_response_quality(
    response: Dict[str, Any], metrics: Optional[Dict[str, Any]] = None
) -> None:
    """
    Assert response quality metrics.

    Args:
        response: Agent response dictionary
        metrics: Optional quality metrics to check
    """
    # Basic quality checks
    assert response, "Response should not be empty"
    assert isinstance(response, dict), "Response should be a dictionary"
    # If metrics provided, check them
    if metrics:
        for metric, expected_value in metrics.items():
            if metric == "has_content":
                assert bool(response.get("content") or response.get("plan") or response.get("code")), (
                    "Response should have content"
                )
            elif metric == "has_status":
                assert "status" in response or "type" in response, (
                    "Response should have status or type"
                )


def create_missing_file_scenario(file_path: Path) -> Path:
    """
    Create a scenario where a file doesn't exist.

    Args:
        file_path: Path to the non-existent file

    Returns:
        Path to the non-existent file
    """
    # Ensure file doesn't exist
    if file_path.exists():
        file_path.unlink()
    return file_path


def create_permission_error_scenario(path: Path) -> Path:
    """
    Create a permission error scenario (for testing).

    Note: On Windows, creating actual permission errors is difficult.
    This is a placeholder for test scenarios.

    Args:
        path: Path to use in scenario

    Returns:
        Path (actual permission errors would need OS-level mocking)
    """
    return path


def create_network_error_scenario(mock_mal: MAL, error_type: str = "connection") -> None:
    """
    Configure mock_mal to simulate network errors.

    Args:
        mock_mal: Mocked MAL instance
        error_type: Type of error (connection, timeout, rate_limit)
    """
    from unittest.mock import AsyncMock

    async def raise_error(*args, **kwargs):
        if error_type == "connection":
            raise ConnectionError("Connection failed to LLM service")
        elif error_type == "timeout":
            raise TimeoutError("Request timed out")
        elif error_type == "rate_limit":
            raise Exception("Rate limit exceeded")
        else:
            raise Exception(f"Network error: {error_type}")

    mock_mal.generate = AsyncMock(side_effect=raise_error)


def validate_error_response(
    response: Dict[str, Any], expected_error_type: Optional[str] = None
) -> None:
    """
    Validate that an error response is properly formatted.

    Args:
        response: Agent response dictionary
        expected_error_type: Optional expected error type
    """
    assert "error" in response, "Error response should contain 'error' field"
    error_msg = str(response["error"])
    assert len(error_msg) > 0, "Error message should not be empty"
    if expected_error_type:
        assert expected_error_type.lower() in error_msg.lower(), (
            f"Error message should indicate '{expected_error_type}' error"
        )


def assert_error_message_quality(
    error_message: str, criteria: Dict[str, Any]
) -> None:
    """
    Assert error message quality based on criteria.

    Args:
        error_message: Error message string
        criteria: Dictionary of quality criteria
    """
    if criteria.get("clear", False):
        assert len(error_message) > 10, "Error message should be clear and descriptive"
    if criteria.get("actionable", False):
        # Check for actionable words
        actionable_words = ["try", "check", "ensure", "verify", "use", "provide"]
        assert any(word in error_message.lower() for word in actionable_words), (
            "Error message should provide actionable guidance"
        )
    if criteria.get("context", False):
        # Check for context (file paths, command names, etc.)
        assert any(char in error_message for char in [":", "(", "[", "/"]), (
            "Error message should include context"
        )


def validate_plan_structure(plan: Any, required_components: List[str]) -> None:
    """
    Validate that a plan has required components.

    Args:
        plan: Plan data (dict or string)
        required_components: List of required component names
    """
    if isinstance(plan, str):
        # For string plans, check if components are mentioned
        plan_lower = plan.lower()
        for component in required_components:
            assert component.lower() in plan_lower, (
                f"Plan should contain '{component}' component"
            )
    elif isinstance(plan, dict):
        # For dict plans, check for keys
        for component in required_components:
            assert component in plan, f"Plan should contain '{component}' key"


def validate_plan_completeness(plan: Any, criteria: Dict[str, Any]) -> None:
    """
    Validate plan completeness based on criteria.

    Args:
        plan: Plan data
        criteria: Completeness criteria
    """
    if isinstance(plan, str):
        # Check for minimum length
        min_length = criteria.get("min_length", 100)
        assert len(plan) >= min_length, f"Plan should be at least {min_length} characters"
        # Check for task indicators
        if criteria.get("has_tasks", False):
            task_indicators = ["task", "step", "1.", "2.", "-"]
            assert any(indicator in plan.lower() for indicator in task_indicators), (
                "Plan should contain task indicators"
            )


def validate_code_quality(code: str, standards: Optional[Dict[str, Any]] = None) -> None:
    """
    Validate code quality (syntax, basic structure).

    Args:
        code: Code string to validate
        standards: Optional code quality standards
    """
    # Basic syntax validation for Python
    try:
        ast.parse(code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax errors: {e}")

    # Check for basic structure
    if standards:
        if standards.get("has_docstrings", False):
            # Check for docstrings
            assert '"""' in code or "'''" in code, "Code should have docstrings"
        if standards.get("has_functions", False):
            # Check for function definitions
            assert "def " in code, "Code should contain function definitions"


def validate_review_feedback(review: Dict[str, Any], criteria: Dict[str, Any]) -> None:
    """
    Validate review feedback quality.

    Args:
        review: Review response dictionary
        criteria: Validation criteria
    """
    if criteria.get("has_score", False):
        assert "score" in review or "quality_score" in review, (
            "Review should contain score"
        )
    if criteria.get("has_feedback", False):
        feedback_fields = ["feedback", "recommendations", "issues", "content"]
        assert any(field in review for field in feedback_fields), (
            "Review should contain feedback"
        )
    if criteria.get("has_status", False):
        assert "status" in review or "approved" in str(review).lower(), (
            "Review should contain status or approval indication"
        )


def validate_test_results(results: Dict[str, Any], criteria: Dict[str, Any]) -> None:
    """
    Validate test results.

    Args:
        results: Test results dictionary
        criteria: Validation criteria
    """
    if criteria.get("has_status", False):
        assert "status" in results or "passed" in str(results).lower() or "failed" in str(results).lower(), (
            "Test results should contain status"
        )
    if criteria.get("has_count", False):
        count_fields = ["tests_run", "passed", "failed", "count"]
        assert any(field in results for field in count_fields), (
            "Test results should contain test counts"
        )

