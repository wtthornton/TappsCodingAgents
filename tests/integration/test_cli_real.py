"""
Integration tests for CLI with actual agents.

These tests verify CLI commands work correctly with instruction-based agents.
"""

import json
import subprocess
import sys

import pytest


pytestmark = pytest.mark.integration


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
