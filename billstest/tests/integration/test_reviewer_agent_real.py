"""
Real integration tests for Reviewer Agent with actual LLM calls.

These tests use ACTUAL LLM calls and require:
- Ollama running locally (http://localhost:11434)
- OR Anthropic API key in environment
- OR OpenAI API key in environment

Tests are marked with @pytest.mark.requires_llm and will be skipped
if no LLM service is available.
"""

import os

import pytest

from tapps_agents.agents.reviewer.agent import ReviewerAgent
from tapps_agents.core.config import MALConfig, ProjectConfig


def check_ollama_available():
    """Check if Ollama is available."""
    import httpx
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def check_anthropic_available():
    """Check if Anthropic API key is available."""
    return os.getenv("ANTHROPIC_API_KEY") is not None


def has_any_llm():
    """Check if any LLM service is available."""
    return check_ollama_available() or check_anthropic_available() or os.getenv("OPENAI_API_KEY") is not None


pytestmark = pytest.mark.integration


@pytest.mark.requires_llm
@pytest.mark.asyncio
class TestReviewerAgentReal:
    """Real integration tests for Reviewer Agent with actual LLM."""

    @pytest.fixture
    def real_mal_config(self):
        """Create real MAL config."""
        if not has_any_llm():
            pytest.skip("No LLM service available")
        
        if check_ollama_available():
            return MALConfig(
                ollama_url="http://localhost:11434",
                default_provider="ollama",
                default_model="qwen2.5-coder:7b",
            )
        elif check_anthropic_available():
            return MALConfig(
                default_provider="anthropic",
                default_model="claude-3-haiku-20240307",
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            )
        else:
            pytest.skip("No LLM service available")

    @pytest.fixture
    def sample_python_file(self, tmp_path):
        """Create a minimal Python file for testing."""
        file_path = tmp_path / "test_code.py"
        # Minimal code for faster LLM processing
        file_path.write_text("""def add(a, b):
    return a + b
""")
        return file_path

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_reviewer_agent_real_score(self, real_mal_config, sample_python_file):
        """Test reviewer agent scoring - minimal test (score is faster than review)."""
        config = ProjectConfig(mal=real_mal_config)
        reviewer = ReviewerAgent(config=config)
        
        try:
            await reviewer.activate()
            # Use score instead of review (faster, no LLM feedback needed)
            result = await reviewer.run("score", file=str(sample_python_file))
            
            assert "file" in result
            assert "scoring" in result
            assert "overall_score" in result["scoring"]
            assert 0 <= result["scoring"]["overall_score"] <= 100
        finally:
            await reviewer.close()

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)  # Should fail fast
    async def test_reviewer_agent_error_handling_real(self, real_mal_config, tmp_path):
        """Test reviewer error handling - fast failure test."""
        non_existent = tmp_path / "nonexistent.py"
        
        config = ProjectConfig(mal=real_mal_config)
        reviewer = ReviewerAgent(config=config)
        
        try:
            await reviewer.activate()
            # Should raise FileNotFoundError or return error dict
            try:
                result = await reviewer.run("score", file=str(non_existent))
                # If no exception, should have error in result
                assert "error" in result or "file" not in result
            except FileNotFoundError:
                # This is acceptable behavior
                pass
        finally:
            await reviewer.close()

