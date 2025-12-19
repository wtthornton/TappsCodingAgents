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


# ============================================================================
# LLM Availability Checks for Real Integration Tests
# ============================================================================


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "requires_llm: mark test as requiring LLM service (Ollama, Anthropic, or OpenAI)"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically skip requires_llm and requires_context7 tests if services unavailable."""
    import os

    import httpx
    
    # Check LLM availability
    ollama_available = False
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        ollama_available = response.status_code == 200
    except Exception:
        pass
    
    anthropic_available = os.getenv("ANTHROPIC_API_KEY") is not None
    openai_available = os.getenv("OPENAI_API_KEY") is not None
    has_llm = ollama_available or anthropic_available or openai_available
    
    # Check Context7 availability (prefers MCP Gateway, falls back to API key)
    from tapps_agents.mcp.gateway import MCPGateway
    
    gateway = MCPGateway()
    tools = gateway.list_available_tools()
    tool_names = [tool.get("name", "") for tool in tools]
    mcp_tools_available = (
        "mcp_Context7_resolve-library-id" in tool_names
        and "mcp_Context7_get-library-docs" in tool_names
    )
    api_key_available = os.getenv("CONTEXT7_API_KEY") is not None
    context7_available = mcp_tools_available or api_key_available
    
    # Skip requires_llm tests if no LLM available
    skip_llm = pytest.mark.skip(reason="No LLM service available (Ollama, Anthropic, or OpenAI)")
    for item in items:
        if "requires_llm" in item.keywords and not has_llm:
            item.add_marker(skip_llm)
    
    # Skip requires_context7 tests if neither MCP tools nor API key available
    skip_context7 = pytest.mark.skip(
        reason="Context7 not available: "
        "MCP tools not found and CONTEXT7_API_KEY not set"
    )
    for item in items:
        if "requires_context7" in item.keywords and not context7_available:
            item.add_marker(skip_context7)