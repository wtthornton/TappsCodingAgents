"""
Unit tests for Implementer Agent.

Tests agent initialization, command handling, code generation, refactoring,
error handling, and expert integration.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapps_agents.agents.implementer.agent import ImplementerAgent

pytestmark = pytest.mark.unit


class TestImplementerAgentInitialization:
    """Tests for ImplementerAgent initialization."""

    @patch("tapps_agents.agents.implementer.agent.load_config")
    def test_implementer_agent_init(self, mock_load_config):
        """Test ImplementerAgent initialization."""
        mock_config = MagicMock()
        mock_config.agents = MagicMock()
        mock_config.agents.implementer = MagicMock()
        mock_config.agents.implementer.require_review = True
        mock_config.agents.implementer.auto_approve_threshold = 80.0
        mock_config.agents.implementer.backup_files = True
        mock_config.agents.implementer.max_file_size = 10 * 1024 * 1024
        mock_load_config.return_value = mock_config
        
        agent = ImplementerAgent()
        assert agent.agent_id == "implementer"
        assert agent.agent_name == "Implementer Agent"
        assert agent.config is not None
        assert agent.code_generator is not None
        assert agent.require_review is True

    @pytest.mark.asyncio
    async def test_implementer_agent_activate(self, temp_project_dir: Path):
        """Test ImplementerAgent activation."""
        agent = ImplementerAgent()
        await agent.activate(temp_project_dir)
        
        assert agent.config is not None

    @pytest.mark.asyncio
    async def test_implementer_agent_get_commands(self):
        """Test ImplementerAgent command list."""
        agent = ImplementerAgent()
        commands = agent.get_commands()
        
        assert isinstance(commands, list)
        assert len(commands) > 0
        command_names = [cmd["command"] for cmd in commands]
        assert "*implement" in command_names
        assert "*generate-code" in command_names
        assert "*refactor" in command_names


class TestImplementerAgentImplementCommand:
    """Tests for implement command."""

    @pytest.mark.asyncio
    async def test_implement_command_success(self, tmp_path: Path):
        """Test implement command with successful code generation."""
        agent = ImplementerAgent()
        await agent.activate()
        
        file_path = tmp_path / "test.py"
        result = await agent.run(
            "implement",
            specification="Create a hello function",
            file_path=str(file_path)
        )
        
        assert "type" in result
        assert result["type"] == "implement"
        assert "instruction" in result
        assert "skill_command" in result
        assert "file" in result
        assert result["file"] == str(file_path)

    @pytest.mark.asyncio
    async def test_implement_command_missing_specification(self):
        """Test implement command without specification."""
        agent = ImplementerAgent()
        await agent.activate()
        
        result = await agent.run("implement", file_path="test.py")
        
        assert "error" in result
        assert "specification required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_implement_command_missing_file_path(self):
        """Test implement command without file path."""
        agent = ImplementerAgent()
        await agent.activate()
        
        result = await agent.run("implement", specification="Create code")
        
        assert "error" in result
        assert "file path required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_implement_command_with_context(self, tmp_path: Path):
        """Test implement command with context."""
        agent = ImplementerAgent()
        await agent.activate()
        
        file_path = tmp_path / "test.py"
        result = await agent.run(
            "implement",
            specification="Create a function",
            file_path=str(file_path),
            context="Use FastAPI patterns"
        )
        
        assert "type" in result
        assert result["type"] == "implement"

    @pytest.mark.asyncio
    async def test_implement_command_with_language(self, tmp_path: Path):
        """Test implement command with language parameter."""
        agent = ImplementerAgent()
        await agent.activate()
        
        file_path = tmp_path / "test.js"
        result = await agent.run(
            "implement",
            specification="Create a function",
            file_path=str(file_path),
            language="javascript"
        )
        
        assert "type" in result
        assert result["type"] == "implement"

    @pytest.mark.asyncio
    async def test_implement_command_invalid_path(self):
        """Test implement command with invalid path."""
        agent = ImplementerAgent()
        await agent.activate()
        
        result = await agent.run(
            "implement",
            specification="Create code",
            file_path="../../../etc/passwd"
        )
        
        assert "error" in result
        assert "invalid" in result["error"].lower() or "unsafe" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_implement_method(self, tmp_path: Path):
        """Test implement method directly."""
        agent = ImplementerAgent()
        await agent.activate()
        
        file_path = tmp_path / "test.py"
        result = await agent.implement(
            specification="Create a function",
            file_path=str(file_path)
        )
        
        assert "type" in result
        assert result["type"] == "implement"
        assert "file" in result

    @pytest.mark.asyncio
    async def test_implement_method_with_expert_guidance(self, tmp_path: Path):
        """Test implement method with expert consultation."""
        agent = ImplementerAgent()
        await agent.activate()
        
        # Mock expert registry
        mock_registry = MagicMock()
        mock_consultation = MagicMock()
        mock_consultation.weighted_answer = "Security advice"
        mock_registry.consult = AsyncMock(return_value=mock_consultation)
        agent.expert_registry = mock_registry
        
        file_path = tmp_path / "test.py"
        result = await agent.implement(
            specification="Create secure code",
            file_path=str(file_path)
        )
        
        assert "type" in result
        assert mock_registry.consult.called


class TestImplementerAgentGenerateCodeCommand:
    """Tests for generate-code command."""

    @pytest.mark.asyncio
    async def test_generate_code_command_success(self):
        """Test generate-code command with successful code generation."""
        agent = ImplementerAgent()
        await agent.activate()
        
        result = await agent.run(
            "generate-code",
            specification="Create a hello function"
        )
        
        assert "type" in result
        assert result["type"] == "generate_code"
        assert "instruction" in result
        assert "skill_command" in result

    @pytest.mark.asyncio
    async def test_generate_code_command_missing_specification(self):
        """Test generate-code command without specification."""
        agent = ImplementerAgent()
        await agent.activate()
        
        result = await agent.run("generate-code")
        
        assert "error" in result
        assert "specification required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_generate_code_command_with_file_path(self, tmp_path: Path):
        """Test generate-code command with file path."""
        agent = ImplementerAgent()
        await agent.activate()
        
        file_path = tmp_path / "test.py"
        result = await agent.run(
            "generate-code",
            specification="Create a function",
            file_path=str(file_path)
        )
        
        assert "type" in result
        assert result["type"] == "generate_code"
        assert "file_path" in result

    @pytest.mark.asyncio
    async def test_generate_code_method(self):
        """Test generate_code method directly."""
        agent = ImplementerAgent()
        await agent.activate()
        
        result = await agent.generate_code(specification="Create a function")
        
        assert "type" in result
        assert result["type"] == "generate_code"
        assert "instruction" in result

    @pytest.mark.asyncio
    async def test_generate_code_method_with_expert_guidance(self):
        """Test generate_code method with expert consultation."""
        agent = ImplementerAgent()
        await agent.activate()
        
        # Mock expert registry
        mock_registry = MagicMock()
        mock_consultation = MagicMock()
        mock_consultation.weighted_answer = "Performance advice"
        mock_registry.consult = AsyncMock(return_value=mock_consultation)
        agent.expert_registry = mock_registry
        
        result = await agent.generate_code(specification="Create optimized code")
        
        assert "type" in result
        assert mock_registry.consult.called


class TestImplementerAgentRefactorCommand:
    """Tests for refactor command."""

    @pytest.mark.asyncio
    async def test_refactor_command_success(self, tmp_path: Path):
        """Test refactor command with successful refactoring."""
        agent = ImplementerAgent()
        await agent.activate()
        
        file_path = tmp_path / "test.py"
        file_path.write_text("def add(a, b): return a + b")
        
        result = await agent.run(
            "refactor",
            file_path=str(file_path),
            instruction="Add type hints"
        )
        
        assert "type" in result
        assert result["type"] == "refactor"
        assert "file" in result
        assert "instruction" in result
        assert "skill_command" in result
        assert "original_code" in result

    @pytest.mark.asyncio
    async def test_refactor_command_file_not_found(self):
        """Test refactor command with non-existent file."""
        agent = ImplementerAgent()
        await agent.activate()
        
        result = await agent.run(
            "refactor",
            file_path="nonexistent.py",
            instruction="Refactor"
        )
        
        assert "error" in result
        error_msg = result["error"]["message"] if isinstance(result["error"], dict) else result["error"]
        assert "not found" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_refactor_command_missing_file_path(self):
        """Test refactor command without file path."""
        agent = ImplementerAgent()
        await agent.activate()
        
        result = await agent.run("refactor", instruction="Refactor")
        
        assert "error" in result
        assert "file path required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_refactor_command_missing_instruction(self, tmp_path: Path):
        """Test refactor command without instruction."""
        agent = ImplementerAgent()
        await agent.activate()
        
        file_path = tmp_path / "test.py"
        file_path.write_text("def x(): pass")
        
        result = await agent.run("refactor", file_path=str(file_path))
        
        assert "error" in result
        assert "instruction required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_refactor_command_invalid_path(self):
        """Test refactor command with invalid path."""
        agent = ImplementerAgent()
        await agent.activate()
        
        result = await agent.run(
            "refactor",
            file_path="../../../etc/passwd",
            instruction="Refactor"
        )
        
        assert "error" in result

    @pytest.mark.asyncio
    async def test_refactor_method(self, tmp_path: Path):
        """Test refactor method directly."""
        agent = ImplementerAgent()
        await agent.activate()
        
        file_path = tmp_path / "test.py"
        file_path.write_text("def add(a, b): return a + b")
        
        result = await agent.refactor(
            file_path=str(file_path),
            instruction="Add type hints"
        )
        
        assert "type" in result
        assert result["type"] == "refactor"
        assert "file" in result
        assert "original_code" in result

    @pytest.mark.asyncio
    async def test_refactor_method_read_error(self, tmp_path: Path):
        """Test refactor method with file read error."""
        agent = ImplementerAgent()
        await agent.activate()
        
        file_path = tmp_path / "test.py"
        # Create a directory with the same name to cause read error
        file_path.mkdir()
        
        result = await agent.refactor(
            file_path=str(file_path),
            instruction="Refactor"
        )
        
        assert "error" in result


class TestImplementerAgentHelperMethods:
    """Tests for helper methods."""

    def test_is_valid_path_valid(self, tmp_path: Path):
        """Test _is_valid_path with valid path."""
        agent = ImplementerAgent()
        file_path = tmp_path / "test.py"
        file_path.write_text("code")
        
        assert agent._is_valid_path(file_path) is True

    def test_is_valid_path_invalid_traversal(self):
        """Test _is_valid_path with path traversal."""
        agent = ImplementerAgent()
        invalid_path = Path("../../../etc/passwd")
        
        assert agent._is_valid_path(invalid_path) is False

    def test_is_valid_path_suspicious_pattern(self):
        """Test _is_valid_path with suspicious pattern."""
        agent = ImplementerAgent()
        suspicious_path = Path("file%00.py")
        
        assert agent._is_valid_path(suspicious_path) is False

    def test_is_valid_path_too_large(self, tmp_path: Path):
        """Test _is_valid_path with file too large."""
        agent = ImplementerAgent()
        agent.max_file_size = 100  # Small limit
        
        large_file = tmp_path / "large.py"
        large_file.write_text("x" * 200)  # Larger than limit
        
        assert agent._is_valid_path(large_file) is False

    def test_detect_language_python(self, tmp_path: Path):
        """Test _detect_language with Python file."""
        agent = ImplementerAgent()
        file_path = tmp_path / "test.py"
        
        assert agent._detect_language(file_path) == "python"

    def test_detect_language_javascript(self, tmp_path: Path):
        """Test _detect_language with JavaScript file."""
        agent = ImplementerAgent()
        file_path = tmp_path / "test.js"
        
        assert agent._detect_language(file_path) == "javascript"

    def test_detect_language_typescript(self, tmp_path: Path):
        """Test _detect_language with TypeScript file."""
        agent = ImplementerAgent()
        file_path = tmp_path / "test.ts"
        
        assert agent._detect_language(file_path) == "typescript"

    def test_detect_language_unknown(self, tmp_path: Path):
        """Test _detect_language with unknown extension."""
        agent = ImplementerAgent()
        file_path = tmp_path / "test.unknown"
        
        assert agent._detect_language(file_path) == "python"  # Default

    def test_create_backup(self, tmp_path: Path):
        """Test _create_backup creates backup file."""
        agent = ImplementerAgent()
        file_path = tmp_path / "test.py"
        file_path.write_text("original code")
        
        backup_path = agent._create_backup(file_path)
        
        assert backup_path is not None
        assert backup_path.exists()
        assert "backup" in backup_path.name
        assert backup_path.read_text() == "original code"

    def test_create_backup_nonexistent_file(self, tmp_path: Path):
        """Test _create_backup with non-existent file."""
        agent = ImplementerAgent()
        file_path = tmp_path / "nonexistent.py"
        
        backup_path = agent._create_backup(file_path)
        
        assert backup_path is None


class TestImplementerAgentErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_unknown_command(self):
        """Test unknown command handling."""
        agent = ImplementerAgent()
        await agent.activate()
        
        result = await agent.run("unknown-command")
        
        assert "error" in result
        assert "unknown command" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Test help command."""
        agent = ImplementerAgent()
        await agent.activate()
        
        result = await agent.run("help")
        
        assert "type" in result
        assert result["type"] == "help"
        assert "content" in result
        assert "*implement" in result["content"]

    @pytest.mark.asyncio
    async def test_implement_code_generation_error(self, tmp_path: Path):
        """Test implement handles code generation errors."""
        agent = ImplementerAgent()
        await agent.activate()
        
        # Mock code generator to raise error
        agent.code_generator.prepare_code_generation = MagicMock(
            side_effect=Exception("Generation failed")
        )
        
        file_path = tmp_path / "test.py"
        result = await agent.implement(
            specification="Create code",
            file_path=str(file_path)
        )
        
        assert "error" in result
        assert "failed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_refactor_preparation_error(self, tmp_path: Path):
        """Test refactor handles preparation errors."""
        agent = ImplementerAgent()
        await agent.activate()
        
        file_path = tmp_path / "test.py"
        file_path.write_text("code")
        
        # Mock code generator to raise error
        agent.code_generator.prepare_refactoring = MagicMock(
            side_effect=Exception("Preparation failed")
        )
        
        result = await agent.refactor(
            file_path=str(file_path),
            instruction="Refactor"
        )
        
        assert "error" in result
        error_msg = result["error"]["message"] if isinstance(result["error"], dict) else result["error"]
        assert "failed" in error_msg.lower()


class TestImplementerAgentReviewIntegration:
    """Tests for review integration."""

    @pytest.mark.asyncio
    async def test_review_code_method(self, tmp_path: Path):
        """Test _review_code method."""
        agent = ImplementerAgent()
        await agent.activate()
        
        # Mock reviewer
        mock_reviewer = MagicMock()
        mock_reviewer.review_file = AsyncMock(return_value={
            "file": "test.py",
            "scoring": {"overall_score": 85.0},
            "passed": True
        })
        agent.reviewer = mock_reviewer
        
        code = "def hello(): pass"
        file_path = tmp_path / "test.py"
        
        result = await agent._review_code(code, file_path)
        
        assert result is not None
        assert "scoring" in result

    @pytest.mark.asyncio
    async def test_review_code_lazy_initialization(self, tmp_path: Path):
        """Test _review_code lazy initializes reviewer."""
        agent = ImplementerAgent()
        await agent.activate()
        
        code = "def hello(): pass"
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        
        with patch("tapps_agents.agents.reviewer.agent.ReviewerAgent") as mock_reviewer_class:
            mock_reviewer = MagicMock()
            mock_reviewer.review_file = AsyncMock(return_value={
                "file": "test.py",
                "scoring": {"overall_score": 85.0}
            })
            mock_reviewer.activate = AsyncMock()
            mock_reviewer_class.return_value = mock_reviewer
            
            result = await agent._review_code(code, file_path)
            
            assert mock_reviewer_class.called
            assert agent.reviewer is not None

    @pytest.mark.asyncio
    async def test_review_code_error_handling(self, tmp_path: Path):
        """Test _review_code handles review errors."""
        agent = ImplementerAgent()
        await agent.activate()
        
        # Mock reviewer to raise error
        mock_reviewer = MagicMock()
        mock_reviewer.review_file = AsyncMock(side_effect=Exception("Review failed"))
        agent.reviewer = mock_reviewer
        
        code = "def hello(): pass"
        file_path = tmp_path / "test.py"
        
        result = await agent._review_code(code, file_path)
        
        assert result is not None
        assert "error" in result


class TestImplementerAgentContext7Integration:
    """Tests for Context7 integration."""

    @pytest.mark.asyncio
    async def test_context7_helper_initialization(self):
        """Test Context7 helper is initialized."""
        agent = ImplementerAgent()
        
        # Context7 helper may be None if not configured
        # Just verify it doesn't cause errors
        assert hasattr(agent, "context7")

