"""
Pytest configuration and shared fixtures for TappsCodingAgents tests.
"""

# ruff: noqa: E402

# Register pytest plugins (optional - plugin handles import errors gracefully)
try:
    pytest_plugins = ["tests.pytest_rich_progress"]
except ImportError:
    # Plugin not available - continue without it
    pytest_plugins = []

# Add project root to path
import sys
from pathlib import Path
from typing import Any

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tapps_agents.core.agent_base import BaseAgent

# ============================================================================
# Async Fixtures
# ============================================================================

# Removed event_loop fixture - using pytest-asyncio's default instead


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
            "reviewer": {"quality_threshold": 70.0}
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
    
    # Register rich progress plugin if available
    # Note: Plugin is already registered via pytest_plugins or -p flag
    # This is just a safety check - plugin handles its own import errors
    try:
        import tests.pytest_rich_progress
        # Plugin's pytest_configure hook will register itself if rich is available
    except (ImportError, AttributeError):
        pass  # Rich progress not available, use default output


def _check_ollama_availability() -> bool:
    """
    Check if Ollama service is available locally.
    
    Returns:
        True if Ollama is running and accessible, False otherwise.
        
    Note:
        This function must never raise exceptions or hang, as it runs during
        test collection and any failure would prevent all tests from being discovered.
    """
    try:
        import httpx
        # Use very short timeout to prevent hanging during collection
        # httpx timeout handles network hangs, so no additional timeout needed
        response = httpx.get("http://localhost:11434/api/tags", timeout=1.0)
        return response.status_code == 200
    except Exception:
        # Silently fail for ANY exception - Ollama not available, network error, timeout, etc.
        return False


def _check_api_keys_available() -> tuple[bool, bool]:
    """
    Check if LLM API keys are available in environment variables.
    
    Returns:
        Tuple of (anthropic_available, openai_available) boolean values.
        
    Note:
        This function safely checks environment variables and never raises exceptions.
    """
    import os
    
    try:
        anthropic_available = os.getenv("ANTHROPIC_API_KEY") is not None
        openai_available = os.getenv("OPENAI_API_KEY") is not None
        return anthropic_available, openai_available
    except Exception:
        # If environment variable access fails, assume not available
        return False, False


def _check_context7_availability() -> bool:
    """
    Check if Context7 is available via MCP Gateway or API key.
    
    This function checks for Context7 availability in two ways:
    1. Checks for CONTEXT7_API_KEY environment variable (fast, no dependencies)
    2. If API key not found, checks MCP Gateway for Context7 tools (slower, requires imports)
    
    Returns:
        True if Context7 is available (either via API key or MCP Gateway), False otherwise.
        
    Note:
        This function must never raise exceptions or hang, as it runs during
        test collection and any failure would prevent all tests from being discovered.
    """
    import os
    
    # Check API key first (fast, no dependencies)
    api_key_available = False
    try:
        api_key_available = os.getenv("CONTEXT7_API_KEY") is not None
    except Exception:
        api_key_available = False
    
    # If API key is available, no need to check MCP Gateway
    if api_key_available:
        return True
    
    # Only check MCP Gateway if API key not available (optimization)
    # This avoids unnecessary MCP Gateway initialization if API key is present
    try:
        from tapps_agents.mcp.gateway import MCPGateway
        
        # MCPGateway() should be fast (just creates a ToolRegistry)
        gateway = MCPGateway()
        
        # list_available_tools() should also be fast (just iterates registry)
        tools = gateway.list_available_tools()
        
        # Safely extract tool names with defensive programming
        tool_names = []
        if isinstance(tools, list):
            for tool in tools:
                try:
                    if isinstance(tool, dict):
                        name = tool.get("name", "")
                        if name and isinstance(name, str):
                            tool_names.append(name)
                except Exception:
                    # Skip invalid tool entries
                    continue
        
        # Check for required Context7 tools
        mcp_tools_available = (
            "mcp_Context7_resolve-library-id" in tool_names
            and "mcp_Context7_get-library-docs" in tool_names
        )
        return mcp_tools_available
    except Exception:
        # MCP Gateway not available, failed to initialize, or any other error
        # This is OK - we'll fall back to API key check (already checked above)
        return False


def _mark_tests_for_skipping(
    items: list[Any],
    has_llm: bool,
    context7_available: bool,
) -> None:
    """
    Mark tests for skipping based on service availability.
    
    Args:
        items: List of pytest test items to potentially mark for skipping.
        has_llm: True if any LLM service (Ollama, Anthropic, OpenAI) is available.
        context7_available: True if Context7 is available (via API key or MCP Gateway).
        
    Note:
        This function must never raise exceptions, as it runs during test collection.
        Individual marker operations are wrapped in try/except to prevent failures
        from blocking test discovery.
    """
    # Skip requires_llm tests if no LLM available
    try:
        skip_llm = pytest.mark.skip(reason="No LLM service available (Ollama, Anthropic, or OpenAI)")
        for item in items:
            try:
                if "requires_llm" in item.keywords and not has_llm:
                    item.add_marker(skip_llm)
            except Exception:
                # Skip individual item if marker addition fails
                continue
    except Exception:
        # If marker creation fails, continue without skipping
        pass
    
    # Skip requires_context7 tests if neither MCP tools nor API key available
    try:
        skip_context7 = pytest.mark.skip(
            reason="Context7 not available: "
            "MCP tools not found and CONTEXT7_API_KEY not set"
        )
        for item in items:
            try:
                if "requires_context7" in item.keywords and not context7_available:
                    item.add_marker(skip_context7)
            except Exception:
                # Skip individual item if marker addition fails
                continue
    except Exception:
        # If marker creation fails, continue without skipping
        pass


def pytest_collection_modifyitems(config: Any, items: list[Any]) -> None:
    """
    Automatically skip requires_llm and requires_context7 tests if services unavailable.
    
    This hook runs during test collection. All checks are wrapped in try/except
    to prevent crashes or hangs that would block test discovery.
    
    Args:
        config: Pytest configuration object (unused but required by pytest hook signature).
        items: List of pytest test items to potentially mark for skipping.
    
    NOTE: This function must never raise exceptions or hang, as it runs during
    test collection and any failure will prevent all tests from being discovered.
    """
    # Check LLM availability (Ollama, Anthropic, OpenAI)
    ollama_available = _check_ollama_availability()
    anthropic_available, openai_available = _check_api_keys_available()
    has_llm = ollama_available or anthropic_available or openai_available
    
    # Check Context7 availability (MCP Gateway or API key)
    context7_available = _check_context7_availability()
    
    # Mark tests for skipping based on service availability
    _mark_tests_for_skipping(items, has_llm, context7_available)