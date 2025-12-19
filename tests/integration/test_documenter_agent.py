"""
Integration tests for DocumenterAgent.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from tapps_agents.agents.documenter import DocumenterAgent


@pytest.mark.integration
class TestDocumenterAgent:
    """Integration tests for DocumenterAgent."""

    @pytest.fixture
    def mock_mal(self):
        """Create a mock MAL."""
        mal = MagicMock(spec=MAL)
        mal.generate = AsyncMock(
            return_value="# API Documentation\n\n## Functions\n\n### add\nAdds two numbers."
        )
        mal.close = AsyncMock()
        return mal

    @pytest.fixture
    def sample_code_file(self, tmp_path: Path):
        """Create a sample code file."""
        code_file = tmp_path / "calculator.py"
        code_file.write_text("def add(a, b):\n    return a + b")
        return code_file

    @pytest.mark.asyncio
    async def test_activate(self, mock_mal):
        """Test agent activation."""
        agent = DocumenterAgent(mal=mock_mal)
        await agent.activate()

        assert agent.config is not None
        assert agent.doc_generator is not None

    @pytest.mark.asyncio
    async def test_get_commands(self, mock_mal):
        """Test command list."""
        agent = DocumenterAgent(mal=mock_mal)
        await agent.activate()

        commands = agent.get_commands()
        command_names = [cmd["command"] for cmd in commands]

        assert "*help" in command_names
        assert "*document" in command_names
        assert "*generate-docs" in command_names
        assert "*update-readme" in command_names
        assert "*update-docstrings" in command_names

    @pytest.mark.asyncio
    async def test_document_command(self, mock_mal, sample_code_file, tmp_path: Path):
        """Test document command."""
        agent = DocumenterAgent(mal=mock_mal)
        agent.docs_dir = tmp_path / "docs"
        await agent.activate()

        result = await agent.document_command(file=str(sample_code_file))

        assert "type" in result
        assert result["type"] == "document"
        assert "output_file" in result
        assert "documentation" in result

    @pytest.mark.asyncio
    async def test_generate_docs_command(self, mock_mal, sample_code_file):
        """Test generate-docs command."""
        agent = DocumenterAgent(mal=mock_mal)
        await agent.activate()

        result = await agent.generate_docs_command(file=str(sample_code_file))

        assert "type" in result
        assert result["type"] == "api_docs"
        assert "documentation" in result

    @pytest.mark.asyncio
    async def test_update_readme_command(self, mock_mal, tmp_path: Path):
        """Test update-readme command."""
        agent = DocumenterAgent(mal=mock_mal)
        await agent.activate()

        result = await agent.update_readme_command(project_root=str(tmp_path))

        assert "type" in result
        assert result["type"] == "readme"
        assert "readme_file" in result
        assert (tmp_path / "README.md").exists()

    @pytest.mark.asyncio
    async def test_update_docstrings_command(self, mock_mal, sample_code_file):
        """Test update-docstrings command."""
        agent = DocumenterAgent(mal=mock_mal)
        await agent.activate()

        result = await agent.update_docstrings_command(
            file=str(sample_code_file), write_file=False
        )

        assert "type" in result
        assert result["type"] == "docstrings"
        assert "updated_code" in result
        assert result["written"] is False

    @pytest.mark.asyncio
    async def test_document_command_file_not_found(self, mock_mal):
        """Test document command with non-existent file."""
        agent = DocumenterAgent(mal=mock_mal)
        await agent.activate()

        result = await agent.document_command(file="nonexistent.py")

        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_help_command(self, mock_mal):
        """Test help command."""
        agent = DocumenterAgent(mal=mock_mal)
        await agent.activate()

        result = await agent.run("help")

        assert "type" in result
        assert result["type"] == "help"
        assert "content" in result
        assert "*document" in result["content"]

    @pytest.mark.asyncio
    async def test_unknown_command(self, mock_mal):
        """Test unknown command handling."""
        agent = DocumenterAgent(mal=mock_mal)
        await agent.activate()

        result = await agent.run("unknown_command")

        assert "error" in result

    @pytest.mark.asyncio
    async def test_close(self, mock_mal):
        """Test agent cleanup."""
        agent = DocumenterAgent(mal=mock_mal)
        await agent.activate()
        await agent.close()

        mock_mal.close.assert_called_once()
