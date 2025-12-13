"""
End-to-end integration tests with real LLM calls.

These tests verify complete workflows from start to finish using
actual LLM services. They test:
- Agent initialization
- Real LLM calls
- File operations
- Result processing

Tests are marked with @pytest.mark.requires_llm and will be skipped
if no LLM service is available.
"""

import os
from pathlib import Path

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
@pytest.mark.e2e
@pytest.mark.asyncio
class TestE2EWorkflowReal:
    """End-to-end workflow tests with real LLM."""

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
    def test_project(self, tmp_path):
        """Create a minimal test project structure."""
        project = tmp_path / "test_project"
        project.mkdir()
        
        # Minimal source file for faster processing
        src_file = project / "main.py"
        src_file.write_text("def hello(): return True\n")
        
        # Create config directory
        config_dir = project / ".tapps-agents"
        config_dir.mkdir()
        
        return project

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_full_score_workflow(self, real_mal_config, test_project):
        """Test complete score workflow - minimal (score is faster than review)."""
        config = ProjectConfig(mal=real_mal_config)
        reviewer = ReviewerAgent(config=config)
        
        source_file = test_project / "main.py"
        
        try:
            # Step 1: Activate agent
            await reviewer.activate(test_project)
            assert reviewer.config is not None
            
            # Step 2: Run score (faster than review, no LLM feedback)
            result = await reviewer.run("score", file=str(source_file))
            
            # Step 3: Verify results
            assert "file" in result
            assert "scoring" in result
            assert "overall_score" in result["scoring"]
            assert 0 <= result["scoring"]["overall_score"] <= 100
        finally:
            await reviewer.close()

