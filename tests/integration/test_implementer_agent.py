"""
Integration tests for ImplementerAgent.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.implementer import ImplementerAgent
from tapps_agents.core.instructions import CodeGenerationInstruction


@pytest.mark.integration
class TestImplementerAgent:
    """Integration tests for ImplementerAgent."""

    # MAL fixture removed - agents now return instruction objects

    @pytest.fixture
    def mock_reviewer(self):
        """Create a mock ReviewerAgent."""
        reviewer = MagicMock()
        reviewer.review_file = AsyncMock(
            return_value={
                "file": "test.py",
                "scoring": {"overall_score": 85.0},
                "passed": True,
            }
        )
        reviewer.activate = AsyncMock()
        reviewer.close = AsyncMock()
        return reviewer

    @pytest.mark.asyncio
    async def test_implementer_initialization(self):
        """Test that ImplementerAgent initializes correctly."""
        implementer = ImplementerAgent()
        assert implementer.agent_id == "implementer"
        assert implementer.agent_name == "Implementer Agent"

    @pytest.mark.asyncio
    async def test_implementer_help_command(self):
        """Test help command returns help information."""
        implementer = ImplementerAgent()
        await implementer.activate()

        result = await implementer.run("help")

        assert result["type"] == "help"
        assert "content" in result
        assert "*implement" in result["content"]
        assert "*generate-code" in result["content"]
        assert "*refactor" in result["content"]

    @pytest.mark.asyncio
    async def test_generate_code_command(self):
        """Test generate-code command returns instruction object."""
        implementer = ImplementerAgent()
        await implementer.activate()

        result = await implementer.run(
            "generate-code", specification="Create a hello function"
        )

        assert result["type"] == "generate_code"
        assert "instruction" in result
        assert "skill_command" in result
        # Verify instruction object structure
        instruction = result["instruction"]
        assert "specification" in instruction
        assert instruction["specification"] == "Create a hello function"
        # Verify skill command is generated
        assert isinstance(result["skill_command"], str)
        assert "@implementer" in result["skill_command"]

    @pytest.mark.asyncio
    async def test_generate_code_command_missing_specification(self):
        """Test generate-code command with missing specification."""
        implementer = ImplementerAgent()
        await implementer.activate()

        result = await implementer.run("generate-code")

        assert "error" in result
        assert "specification" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_implement_command_without_review(self, tmp_path: Path):
        """Test implement command without review requirement."""
        implementer = ImplementerAgent()
        implementer.require_review = False
        await implementer.activate()

        file_path = tmp_path / "test.py"
        result = await implementer.run(
            "implement",
            specification="Create a hello function",
            file_path=str(file_path),
        )

        assert result["type"] == "implement"
        assert result["file"] == str(file_path)
        assert result["approved"] is True
        assert file_path.exists()

    @pytest.mark.asyncio
    async def test_implement_command_missing_specification(self):
        """Test implement command with missing specification."""
        implementer = ImplementerAgent()
        await implementer.activate()

        result = await implementer.run("implement", file_path="test.py")

        assert "error" in result
        assert "specification" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_implement_command_missing_file_path(self):
        """Test implement command with missing file path."""
        implementer = ImplementerAgent()
        await implementer.activate()

        result = await implementer.run("implement", specification="Create a function")

        assert "error" in result
        assert (
            "file path" in result["error"].lower()
            or "file_path" in result["error"].lower()
        )

    @pytest.mark.asyncio
    @patch("tapps_agents.agents.reviewer.agent.ReviewerAgent")
    async def test_implement_command_with_review_pass(
        self, mock_reviewer_class, tmp_path: Path
    ):
        """Test implement command with review that passes."""
        # Setup mock reviewer
        mock_reviewer_instance = MagicMock()
        mock_reviewer_instance.review_file = AsyncMock(
            return_value={
                "file": "test.py",
                "scoring": {"overall_score": 85.0},
                "passed": True,
            }
        )
        mock_reviewer_instance.activate = AsyncMock()
        mock_reviewer_instance.close = AsyncMock()
        mock_reviewer_class.return_value = mock_reviewer_instance

        implementer = ImplementerAgent()
        implementer.require_review = True
        implementer.auto_approve_threshold = 80.0
        await implementer.activate()

        file_path = tmp_path / "test.py"
        result = await implementer.run(
            "implement",
            specification="Create a hello function",
            file_path=str(file_path),
        )

        assert result["type"] == "implement"
        assert result["approved"] is True
        assert file_path.exists()

    @pytest.mark.asyncio
    @patch("tapps_agents.agents.reviewer.agent.ReviewerAgent")
    async def test_implement_command_with_review_fail(
        self, mock_reviewer_class, tmp_path: Path
    ):
        """Test implement command with review that fails."""
        # Setup mock reviewer
        mock_reviewer_instance = MagicMock()
        mock_reviewer_instance.review_file = AsyncMock(
            return_value={
                "file": "test.py",
                "scoring": {"overall_score": 70.0},
                "passed": False,
            }
        )
        mock_reviewer_instance.activate = AsyncMock()
        mock_reviewer_instance.close = AsyncMock()
        mock_reviewer_class.return_value = mock_reviewer_instance

        implementer = ImplementerAgent()
        implementer.require_review = True
        implementer.auto_approve_threshold = 80.0
        await implementer.activate()

        file_path = tmp_path / "test.py"
        result = await implementer.run(
            "implement",
            specification="Create a hello function",
            file_path=str(file_path),
        )

        assert "error" in result
        assert result["approved"] is False
        assert not file_path.exists()  # File should not be created

    @pytest.mark.asyncio
    async def test_refactor_command(self, tmp_path: Path):
        """Test refactor command returns instruction object."""
        # Create existing file
        file_path = tmp_path / "test.py"
        file_path.write_text("def add(a, b): return a + b")

        implementer = ImplementerAgent()
        implementer.require_review = False
        await implementer.activate()

        result = await implementer.run(
            "refactor", file_path=str(file_path), instruction="Add type hints"
        )

        assert result["type"] == "refactor"
        assert result["file"] == str(file_path)
        assert "instruction" in result
        assert "skill_command" in result

    @pytest.mark.asyncio
    async def test_refactor_command_file_not_found(self):
        """Test refactor command with non-existent file."""
        implementer = ImplementerAgent()
        await implementer.activate()

        result = await implementer.run(
            "refactor", file_path="nonexistent.py", instruction="Refactor"
        )

        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_refactor_command_missing_instruction(self, tmp_path: Path):
        """Test refactor command with missing instruction."""
        file_path = tmp_path / "test.py"
        file_path.write_text("def x(): pass")

        implementer = ImplementerAgent()
        await implementer.activate()

        result = await implementer.run("refactor", file_path=str(file_path))

        assert "error" in result
        assert "instruction" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_backup_creation_on_overwrite(self, tmp_path: Path):
        """Test that backup is created when overwriting existing file."""
        file_path = tmp_path / "test.py"
        file_path.write_text("original code")

        implementer = ImplementerAgent()
        implementer.require_review = False
        implementer.backup_files = True
        await implementer.activate()

        result = await implementer.run(
            "implement", specification="Create new code", file_path=str(file_path)
        )

        assert result["backup"] is not None
        backup_path = Path(result["backup"])
        assert backup_path.exists()
        assert "original code" in backup_path.read_text()

    @pytest.mark.asyncio
    async def test_unknown_command(self):
        """Test that unknown commands return error."""
        implementer = ImplementerAgent()
        await implementer.activate()

        result = await implementer.run("unknown_command")

        assert "error" in result
        assert (
            "unknown" in result["error"].lower() or "command" in result["error"].lower()
        )

    @pytest.mark.asyncio
    async def test_path_validation(self):
        """Test path validation prevents unsafe paths."""
        implementer = ImplementerAgent()
        await implementer.activate()

        result = await implementer.run(
            "implement", specification="Create code", file_path="../../../etc/passwd"
        )

        assert "error" in result
        assert (
            "invalid" in result["error"].lower() or "unsafe" in result["error"].lower()
        )

    @pytest.mark.asyncio
    async def test_detect_language_from_extension(self, tmp_path: Path):
        """Test language detection from file extension."""
        file_path = tmp_path / "test.js"
        file_path.write_text("function hello() { return 'world'; }")

        implementer = ImplementerAgent()
        implementer.require_review = False
        await implementer.activate()

        result = await implementer.run(
            "refactor", file_path=str(file_path), instruction="Add JSDoc comments"
        )

        # Verify the command succeeds and returns instruction object
        assert result["type"] == "refactor"
        assert "instruction" in result
