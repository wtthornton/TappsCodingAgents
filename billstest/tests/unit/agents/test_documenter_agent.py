"""
Unit tests for Documenter Agent.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.documenter.agent import DocumenterAgent


@pytest.mark.unit
class TestDocumenterAgent:
    """Test cases for DocumenterAgent."""

    @pytest.fixture
    def documenter(self):
        """Create a DocumenterAgent instance with mocked MAL."""
        with patch("tapps_agents.agents.documenter.agent.load_config"):
            with patch("tapps_agents.agents.documenter.agent.MAL") as mock_mal_class:
                mock_mal = MagicMock()
                mock_mal.generate = AsyncMock(return_value="Mocked documentation")
                mock_mal_class.return_value = mock_mal
                
                with patch("tapps_agents.agents.documenter.agent.DocGenerator"):
                    agent = DocumenterAgent()
                    agent.mal = mock_mal
                    agent.doc_generator = MagicMock()
                    agent.doc_generator.generate_docs = AsyncMock(return_value="Generated docs")
                    return agent

    @pytest.mark.asyncio
    async def test_document_success(self, documenter, tmp_path):
        """Test document command."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello(): pass")
        
        result = await documenter.run("document", file=str(test_file))

        assert "success" in result or "documentation" in result

    @pytest.mark.asyncio
    async def test_document_no_file(self, documenter):
        """Test document command without file."""
        result = await documenter.run("document", file="")

        assert "error" in result

    @pytest.mark.asyncio
    async def test_generate_docs(self, documenter):
        """Test generate docs command."""
        result = await documenter.run("generate-docs", target=".")

        assert "success" in result or "docs" in result

    @pytest.mark.asyncio
    async def test_update_readme(self, documenter, tmp_path):
        """Test update readme command."""
        result = await documenter.run("update-readme", project_root=str(tmp_path))

        assert "success" in result or "readme" in result

    @pytest.mark.asyncio
    async def test_update_docstrings(self, documenter, tmp_path):
        """Test update docstrings command."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello(): pass")
        
        result = await documenter.run("update-docstrings", file=str(test_file))

        assert "success" in result or "docstrings" in result

    @pytest.mark.asyncio
    async def test_help(self, documenter):
        """Test help command."""
        result = await documenter.run("help")

        assert "type" in result or "content" in result

    @pytest.mark.asyncio
    async def test_unknown_command(self, documenter):
        """Test unknown command."""
        result = await documenter.run("unknown-command")

        assert "error" in result
        assert "Unknown command" in result["error"]

