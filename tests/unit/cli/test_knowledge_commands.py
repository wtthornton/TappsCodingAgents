"""
Tests for Knowledge CLI commands.
"""

import tempfile
from pathlib import Path

import pytest

from tapps_agents.cli.commands.knowledge import KnowledgeCommand

pytestmark = pytest.mark.unit


class TestKnowledgeCommand:
    """Test knowledge base CLI commands."""

    @pytest.fixture
    def temp_knowledge_dir(self):
        """Create temporary knowledge directory."""
        import shutil

        temp_dir = Path(tempfile.mkdtemp())
        knowledge_dir = temp_dir / "knowledge"
        knowledge_dir.mkdir()

        # Create test files
        (knowledge_dir / "test1.md").write_text("# Test 1\nContent", encoding="utf-8")
        (knowledge_dir / "test2.md").write_text("# Test 2\nContent", encoding="utf-8")

        yield knowledge_dir

        shutil.rmtree(temp_dir)

    def test_validate_command(self, temp_knowledge_dir):
        """Test validate command."""
        cmd = KnowledgeCommand()

        result = cmd.validate(knowledge_dir=temp_knowledge_dir)

        assert "summary" in result
        assert "results" in result
        assert result["summary"]["total_files"] >= 2

    def test_metrics_command(self):
        """Test metrics command."""
        cmd = KnowledgeCommand()

        result = cmd.metrics()

        assert "metrics" in result
        assert "recent_queries" in result
        assert "total_queries" in result["metrics"]

    def test_freshness_command(self, temp_knowledge_dir):
        """Test freshness command."""
        cmd = KnowledgeCommand()

        result = cmd.freshness(knowledge_dir=temp_knowledge_dir, scan=True)

        assert "summary" in result
        assert "scan_results" in result
        assert result["scan_results"]["scanned"] >= 2

    def test_freshness_without_scan(self, temp_knowledge_dir):
        """Test freshness command without scanning."""
        cmd = KnowledgeCommand()

        result = cmd.freshness(knowledge_dir=temp_knowledge_dir, scan=False)

        assert "summary" in result
        assert result.get("scan_results") is None
