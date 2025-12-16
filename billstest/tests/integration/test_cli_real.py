"""
Real integration tests for CLI with actual agents and LLM calls - optimized for speed.

These tests use ACTUAL LLM calls but are optimized to be faster:
- Use 'score' instead of 'review' (faster, no LLM feedback)
- Minimal test files
- Reduced timeouts
"""

import json
import os
import subprocess
import sys

import pytest


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
class TestCLIReal:
    """Real integration tests for CLI - optimized for speed."""

    @pytest.fixture
    def sample_python_file(self, tmp_path):
        """Create a minimal Python file for testing."""
        file_path = tmp_path / "test_code.py"
        file_path.write_text("def add(a, b): return a + b\n")
        return file_path

    @pytest.mark.timeout(30)
    def test_cli_score_command_real(self, sample_python_file):
        """Test CLI score command - minimal test (score is faster than review)."""
        if not has_any_llm():
            pytest.skip("No LLM service available")
        
        # Use score instead of review (faster, no LLM feedback)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tapps_agents.cli",
                "reviewer",
                "score",
                str(sample_python_file),
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=25,  # Reduced timeout
        )
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        output = result.stdout.strip()
        try:
            data = json.loads(output)
            assert "scoring" in data or "file" in data
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON: {output}")

    @pytest.mark.timeout(10)  # Should fail fast
    def test_cli_error_handling_file_not_found(self, tmp_path):
        """Test CLI error handling for non-existent file."""
        non_existent = tmp_path / "nonexistent.py"
        
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tapps_agents.cli",
                "reviewer",
                "score",  # Use score (faster)
                str(non_existent),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        # Should fail with error
        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()
