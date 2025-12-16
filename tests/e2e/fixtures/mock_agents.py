"""
Behavioral Mock System for E2E Tests.

Provides agent-specific behavioral mocks that simulate real agent behavior:
- Command parsing and validation
- Response generation based on input
- Error handling and edge cases
- Agent-specific behavior (planner plans, implementer implements, reviewer reviews)
"""

import re
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from tapps_agents.core.mal import MAL


class BehavioralMock:
    """Base class for behavioral mocks with command parsing utilities."""

    def __init__(self, agent_type: str):
        """Initialize behavioral mock."""
        self.agent_type = agent_type
        self.mal = MagicMock(spec=MAL)
        self.mal.close = AsyncMock()

    def parse_cursor_command(self, prompt: str) -> dict[str, Any]:
        """
        Parse Cursor command from prompt.

        Returns:
            Dictionary with command, args, and tool_calls
        """
        # Extract command (e.g., *plan, *implement, *review)
        command_match = re.search(r'\*(\w+)', prompt)
        command = command_match.group(1) if command_match else None

        # Extract tool calls (e.g., <tool_call>...</tool_call>)
        tool_calls = []
        tool_call_pattern = r'<tool_call[^>]*>(.*?)</tool_call>'
        for match in re.finditer(tool_call_pattern, prompt, re.DOTALL):
            tool_calls.append(match.group(1))

        # Extract file paths
        file_paths = re.findall(r'([a-zA-Z0-9_/\\-]+\.(?:py|md|yaml|yml|json|txt))', prompt)

        return {
            "command": command,
            "tool_calls": tool_calls,
            "file_paths": file_paths,
            "prompt": prompt,
        }

    def validate_command(self, parsed: dict[str, Any], valid_commands: list[str]) -> bool:
        """Validate that command is in list of valid commands."""
        if not parsed.get("command"):
            return False
        return parsed["command"] in valid_commands

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response based on prompt (to be overridden by subclasses)."""
        parsed = self.parse_cursor_command(prompt)
        return self._generate_response(parsed, **kwargs)

    def _generate_response(self, parsed: dict[str, Any], **kwargs) -> str:
        """Generate response (to be overridden by subclasses)."""
        return "Mock LLM response"


class MockPlanner(BehavioralMock):
    """Behavioral mock for Planner Agent."""

    def __init__(self):
        """Initialize planner mock."""
        super().__init__("planner")
        self.mal.generate = AsyncMock(side_effect=self.generate)

    def _generate_response(self, parsed: dict[str, Any], **kwargs) -> str:
        """Generate planning response."""
        command = parsed.get("command")
        prompt = parsed.get("prompt", "")

        if command == "plan":
            # Generate a plan with tasks and dependencies
            return f"""# Implementation Plan

## Overview
Based on the requirements: {prompt[:100]}

## Tasks
1. Task 1: Initial setup and configuration
2. Task 2: Core functionality implementation
3. Task 3: Testing and validation
4. Task 4: Documentation

## Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 3

## Estimated Effort
- Total: 8 hours
- Task 1: 1 hour
- Task 2: 4 hours
- Task 3: 2 hours
- Task 4: 1 hour
"""

        elif command == "create-story":
            # Generate a user story
            return f"""# User Story

**As a** developer
**I want** {prompt[:50]}
**So that** I can achieve the desired functionality

## Acceptance Criteria
1. Feature works as expected
2. Tests pass
3. Code quality meets standards

## Priority: Medium
## Status: Draft
"""

        else:
            return "Planner mock response"

    def validate_command(self, parsed: dict[str, Any]) -> bool:
        """Validate planner commands."""
        valid_commands = ["plan", "create-story", "list-stories", "help"]
        return super().validate_command(parsed, valid_commands)


class MockImplementer(BehavioralMock):
    """Behavioral mock for Implementer Agent."""

    def __init__(self):
        """Initialize implementer mock."""
        super().__init__("implementer")
        self.mal.generate = AsyncMock(side_effect=self.generate)

    def _generate_response(self, parsed: dict[str, Any], **kwargs) -> str:
        """Generate code implementation response."""
        command = parsed.get("command")
        prompt = parsed.get("prompt", "")
        file_paths = parsed.get("file_paths", [])

        if command in ["implement", "generate-code"]:
            # Generate code based on prompt
            target_file = file_paths[0] if file_paths else "generated_code.py"
            
            # Extract function/class name from prompt
            func_match = re.search(r'(?:function|def|class)\s+(\w+)', prompt, re.IGNORECASE)
            func_name = func_match.group(1) if func_match else "example_function"

            return f'''def {func_name}():
    """
    Generated function based on requirements.
    """
    # Implementation based on: {prompt[:50]}
    result = None
    return result

# Additional code
if __name__ == "__main__":
    {func_name}()
'''

        elif command == "fix":
            # Generate bug fix
            return f'''# Bug Fix

Fixed issue: {prompt[:100]}

## Changes Made
1. Fixed the bug
2. Added error handling
3. Updated tests

## Code Changes
```python
# Fixed code
def fixed_function():
    # Corrected implementation
    pass
```
'''

        else:
            return "Implementer mock response"

    def validate_command(self, parsed: dict[str, Any]) -> bool:
        """Validate implementer commands."""
        valid_commands = ["implement", "generate-code", "fix", "refactor", "help"]
        return super().validate_command(parsed, valid_commands)


class MockReviewer(BehavioralMock):
    """Behavioral mock for Reviewer Agent."""

    def __init__(self, quality_score: float = 75.0):
        """Initialize reviewer mock."""
        super().__init__("reviewer")
        self.quality_score = quality_score
        self.mal.generate = AsyncMock(side_effect=self.generate)

    def _generate_response(self, parsed: dict[str, Any], **kwargs) -> str:
        """Generate review response."""
        command = parsed.get("command")
        prompt = parsed.get("prompt", "")

        if command in ["review", "score"]:
            # Generate review with score
            score = self.quality_score
            status = "approved" if score >= 70.0 else "needs_improvement"
            
            return f"""# Code Review

## Overall Score: {score:.1f}/100
## Status: {status}

## Quality Metrics
- Complexity: 3.5/10
- Security: 8.0/10
- Maintainability: 7.5/10
- Test Coverage: 75%

## Feedback
- Code quality is {'good' if score >= 70 else 'needs improvement'}
- {'No major issues found' if score >= 70 else 'Several issues need attention'}

## Recommendations
1. Add more tests
2. Improve documentation
3. Reduce complexity
"""

        else:
            return "Reviewer mock response"

    def validate_command(self, parsed: dict[str, Any]) -> bool:
        """Validate reviewer commands."""
        valid_commands = ["review", "score", "help"]
        return super().validate_command(parsed, valid_commands)


class MockTester(BehavioralMock):
    """Behavioral mock for Tester Agent."""

    def __init__(self, test_results: str = "pass"):
        """Initialize tester mock."""
        super().__init__("tester")
        self.test_results = test_results
        self.mal.generate = AsyncMock(side_effect=self.generate)

    def _generate_response(self, parsed: dict[str, Any], **kwargs) -> str:
        """Generate test code and results."""
        command = parsed.get("command")
        prompt = parsed.get("prompt", "")

        if command in ["generate-test", "test"]:
            # Generate test code
            return '''import pytest

def test_example():
    """Test generated based on requirements."""
    # Test implementation
    assert True

def test_functionality():
    """Test the functionality."""
    # Test code
    result = None
    assert result is not None
'''

        elif command == "run-tests":
            # Generate test results
            if self.test_results == "pass":
                return """Test Results: PASSED
Tests run: 5
Passed: 5
Failed: 0
Coverage: 85%
"""
            else:
                return """Test Results: FAILED
Tests run: 5
Passed: 3
Failed: 2
Coverage: 60%

Failures:
- test_example: AssertionError
- test_functionality: ValueError
"""

        else:
            return "Tester mock response"

    def validate_command(self, parsed: dict[str, Any]) -> bool:
        """Validate tester commands."""
        valid_commands = ["generate-test", "test", "run-tests", "help"]
        return super().validate_command(parsed, valid_commands)


class MockDebugger(BehavioralMock):
    """Behavioral mock for Debugger Agent."""

    def __init__(self):
        """Initialize debugger mock."""
        super().__init__("debugger")
        self.mal.generate = AsyncMock(side_effect=self.generate)

    def _generate_response(self, parsed: dict[str, Any], **kwargs) -> str:
        """Generate debug analysis."""
        command = parsed.get("command")
        prompt = parsed.get("prompt", "")

        if command == "debug":
            return f"""# Debug Analysis

## Error Analysis
Error type: ValueError
Location: line 42 in example.py

## Root Cause
The issue is caused by: {prompt[:100]}

## Solution
1. Fix the error handling
2. Add validation
3. Update error messages

## Fixed Code
```python
# Fixed implementation
try:
    # Corrected code
    pass
except ValueError as e:
    # Proper error handling
    pass
```
"""

        else:
            return "Debugger mock response"

    def validate_command(self, parsed: dict[str, Any]) -> bool:
        """Validate debugger commands."""
        valid_commands = ["debug", "analyze-error", "help"]
        return super().validate_command(parsed, valid_commands)


class MockAnalyst(BehavioralMock):
    """Behavioral mock for Analyst Agent."""

    def __init__(self):
        """Initialize analyst mock."""
        super().__init__("analyst")
        self.mal.generate = AsyncMock(side_effect=self.generate)

    def _generate_response(self, parsed: dict[str, Any], **kwargs) -> str:
        """Generate analysis response."""
        command = parsed.get("command")
        prompt = parsed.get("prompt", "")

        if command == "gather-requirements":
            return f"""# Requirements Analysis

## Requirements
1. {prompt[:50]}
2. Additional requirement
3. Quality requirements

## Stakeholders
- Developer
- End user

## Effort Estimate
- Low complexity
- Estimated time: 4 hours
"""

        else:
            return "Analyst mock response"

    def validate_command(self, parsed: dict[str, Any]) -> bool:
        """Validate analyst commands."""
        valid_commands = ["gather-requirements", "analyze-stakeholders", "research-technology", "help"]
        return super().validate_command(parsed, valid_commands)


class MockArchitect(BehavioralMock):
    """Behavioral mock for Architect Agent."""

    def __init__(self):
        """Initialize architect mock."""
        super().__init__("architect")
        self.mal.generate = AsyncMock(side_effect=self.generate)

    def _generate_response(self, parsed: dict[str, Any], **kwargs) -> str:
        """Generate architecture design."""
        command = parsed.get("command")
        prompt = parsed.get("prompt", "")

        if command == "design":
            return f"""# Architecture Design

## System Architecture
Based on requirements: {prompt[:100]}

## Components
1. Core module
2. API layer
3. Data layer

## Design Patterns
- MVC pattern
- Repository pattern

## Technology Stack
- Python 3.11+
- FastAPI
- SQLite
"""

        else:
            return "Architect mock response"

    def validate_command(self, parsed: dict[str, Any]) -> bool:
        """Validate architect commands."""
        valid_commands = ["design", "analyze-architecture", "help"]
        return super().validate_command(parsed, valid_commands)


class MockDocumenter(BehavioralMock):
    """Behavioral mock for Documenter Agent."""

    def __init__(self):
        """Initialize documenter mock."""
        super().__init__("documenter")
        self.mal.generate = AsyncMock(side_effect=self.generate)

    def _generate_response(self, parsed: dict[str, Any], **kwargs) -> str:
        """Generate documentation."""
        command = parsed.get("command")
        prompt = parsed.get("prompt", "")

        if command == "document":
            return f"""# Documentation

## Overview
{prompt[:100]}

## API Documentation
### Function: example_function
```python
def example_function():
    \"\"\"Example function documentation.\"\"\"
    pass
```

## Usage Examples
```python
# Example usage
result = example_function()
```
"""

        else:
            return "Documenter mock response"

    def validate_command(self, parsed: dict[str, Any]) -> bool:
        """Validate documenter commands."""
        valid_commands = ["document", "generate-docs", "help"]
        return super().validate_command(parsed, valid_commands)


# Mock factory function
def create_behavioral_mock(agent_type: str, **kwargs) -> BehavioralMock:
    """
    Create a behavioral mock for the specified agent type.

    Args:
        agent_type: Type of agent (planner, implementer, reviewer, tester, etc.)
        **kwargs: Additional configuration for the mock

    Returns:
        BehavioralMock instance

    Raises:
        ValueError: If agent_type is not supported
    """
    agent_type_lower = agent_type.lower()

    if agent_type_lower == "planner":
        return MockPlanner()
    elif agent_type_lower == "implementer":
        return MockImplementer()
    elif agent_type_lower == "reviewer":
        quality_score = kwargs.get("quality_score", 75.0)
        return MockReviewer(quality_score=quality_score)
    elif agent_type_lower == "tester":
        test_results = kwargs.get("test_results", "pass")
        return MockTester(test_results=test_results)
    elif agent_type_lower == "debugger":
        return MockDebugger()
    elif agent_type_lower == "analyst":
        return MockAnalyst()
    elif agent_type_lower == "architect":
        return MockArchitect()
    elif agent_type_lower == "documenter":
        return MockDocumenter()
    else:
        raise ValueError(f"Unsupported agent type: {agent_type}")


# Pytest fixtures for behavioral mocks
def pytest_configure(config):
    """Register pytest markers for behavioral mocks."""
    config.addinivalue_line(
        "markers", "behavioral_mock: mark test to use behavioral mocks instead of generic mocks"
    )

