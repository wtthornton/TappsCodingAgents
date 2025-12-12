"""
Pytest configuration and shared fixtures for TappsCodingAgents tests.
"""

# ruff: noqa: E402

# Add project root to path
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tapps_agents.core.agent_base import BaseAgent
from tapps_agents.core.mal import MAL

# ============================================================================
# Async Fixtures
# ============================================================================

# Removed event_loop fixture - using pytest-asyncio's default instead


# ============================================================================
# Mock MAL Fixtures
# ============================================================================


@pytest.fixture
def mock_mal() -> MagicMock:
    """
    Mock Model Abstraction Layer for testing without Ollama.

    Returns a mock MAL that can be configured to return specific responses.
    """
    mal = MagicMock(spec=MAL)
    mal.generate = AsyncMock(return_value="Mock LLM response")
    mal.close = AsyncMock()
    return mal


@pytest.fixture
def mock_mal_with_response() -> callable:
    """
    Factory fixture for creating a mock MAL with custom responses.

    Usage:
        mal = mock_mal_with_response("Custom response")
        result = await mal.generate("prompt")
    """

    def _create_mock(response: str = "Mock LLM response"):
        mal = MagicMock(spec=MAL)
        mal.generate = AsyncMock(return_value=response)
        mal.close = AsyncMock()
        return mal

    return _create_mock


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_python_code() -> str:
    """Sample Python code for testing."""
    return '''def calculate_sum(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

def complex_function(items: list) -> dict:
    """Process a list of items."""
    result = {}
    for item in items:
        if item > 10:
            result[item] = item * 2
    return result
'''


@pytest.fixture
def sample_python_file(tmp_path: Path) -> Path:
    """Create a temporary Python file for testing."""
    file_path = tmp_path / "test_code.py"
    file_path.write_text(
        """def hello():
    print("Hello, World!")
    return True
"""
    )
    return file_path


@pytest.fixture
def sample_python_file_complex(tmp_path: Path) -> Path:
    """Create a complex temporary Python file for testing."""
    file_path = tmp_path / "complex_code.py"
    file_path.write_text(
        '''def complex_nested_function(data):
    """Complex function with nested logic."""
    result = []
    for item in data:
        if item.get("active"):
            for value in item.get("values", []):
                if value > 0:
                    result.append(value * 2)
    return result

def insecure_function(user_input):
    """Insecure function with potential issues."""
    eval(user_input)  # Security issue
    exec("print('bad')")  # Security issue
    return True
'''
    )
    return file_path


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def test_config(tmp_path: Path) -> dict[str, Any]:
    """Create a test configuration dictionary."""
    return {
        "agents": {
            "reviewer": {"model": "qwen2.5-coder:7b", "quality_threshold": 70.0}
        },
        "scoring": {
            "weights": {
                "complexity": 0.20,
                "security": 0.30,
                "maintainability": 0.25,
                "test_coverage": 0.15,
                "performance": 0.10,
            }
        },
        "mal": {
            "ollama_url": "http://localhost:11434",
            "default_model": "qwen2.5-coder:7b",
        },
    }


@pytest.fixture
def project_root_path() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory with .tapps-agents structure."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    config_dir = project_dir / ".tapps-agents"
    config_dir.mkdir()
    return project_dir


# ============================================================================
# Agent Fixtures
# ============================================================================


@pytest.fixture
def base_agent() -> BaseAgent:
    """Create a concrete BaseAgent instance for testing."""

    class TestAgent(BaseAgent):
        def __init__(self):
            super().__init__(agent_id="test-agent", agent_name="Test Agent")

        async def run(self, command: str, **kwargs) -> dict[str, Any]:
            if command == "test":
                return {"status": "success", "command": command}
            return {"error": "Unknown command"}

    return TestAgent()


# ============================================================================
# Utility Fixtures
# ============================================================================


@pytest.fixture
def mock_file_read(tmp_path: Path):
    """
    Mock file reading operations.

    Usage:
        with mock_file_read("content") as mock:
            # code that reads files
    """

    def _mock_read(content: str = "file content"):
        file_path = tmp_path / "test_file.py"
        file_path.write_text(content)
        return file_path

    return _mock_read


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks before each test."""
    yield
    # Cleanup happens automatically via pytest's fixture system
