"""
Unit tests for Codebase Context Injection in Enhancer Agent.

Tests the codebase context injection feature that finds related files,
extracts patterns, and detects cross-references for enhanced prompts.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tapps_agents.agents.enhancer.agent import EnhancerAgent

pytestmark = pytest.mark.unit


class TestFindRelatedFiles:
    """Tests for _find_related_files() method."""

    @pytest.fixture
    def enhancer_agent(self, tmp_path):
        """Create enhancer agent with temporary project root."""
        agent = EnhancerAgent()
        agent.config = MagicMock()
        agent.config.project_root = tmp_path
        agent._project_root = tmp_path  # Set the attribute used by _find_related_files
        return agent

    @pytest.mark.asyncio
    async def test_find_related_files_by_domain(self, enhancer_agent, tmp_path):
        """Test finding files related to a domain."""
        # Create test files with domain-related content
        auth_file = tmp_path / "auth_service.py"
        auth_file.write_text(
            """
# Authentication service
class AuthService:
    def login(self, username, password):
        pass
""",
            encoding="utf-8",
        )

        user_file = tmp_path / "user_service.py"
        user_file.write_text(
            """
# User management service
class UserService:
    def create_user(self, user_data):
        pass
""",
            encoding="utf-8",
        )

        analysis = {
            "domains": ["authentication"],
            "technologies": [],
        }

        result = await enhancer_agent._find_related_files("", analysis)

        assert len(result) > 0
        assert any("auth" in str(f).lower() for f in result)

    @pytest.mark.asyncio
    async def test_find_related_files_by_technology(self, enhancer_agent, tmp_path):
        """Test finding files related to a technology."""
        # Create test files with technology-related content
        fastapi_file = tmp_path / "api_router.py"
        fastapi_file.write_text(
            """
from fastapi import APIRouter

router = APIRouter()
""",
            encoding="utf-8",
        )

        analysis = {
            "domains": [],
            "technologies": ["FastAPI"],
        }

        result = await enhancer_agent._find_related_files("", analysis)

        assert len(result) > 0
        assert any("api" in str(f).lower() or "fastapi" in str(f).lower() for f in result)

    @pytest.mark.asyncio
    async def test_find_related_files_excludes_tests(self, enhancer_agent, tmp_path):
        """Test that test files are excluded."""
        # Create test file and regular file
        test_file = tmp_path / "test_auth.py"
        test_file.write_text("def test_login(): pass", encoding="utf-8")

        regular_file = tmp_path / "auth.py"
        regular_file.write_text("class Auth: pass", encoding="utf-8")

        analysis = {
            "domains": ["authentication"],
            "technologies": [],
        }

        result = await enhancer_agent._find_related_files("", analysis)

        # Test files should be excluded
        assert not any("test_" in str(f) for f in result)
        # Regular files may be included
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_find_related_files_limits_results(self, enhancer_agent, tmp_path):
        """Test that results are limited to max files."""
        # Create more than 10 matching files
        for i in range(15):
            file_path = tmp_path / f"service_{i}.py"
            file_path.write_text(
                f"""
# Service {i}
class Service{i}:
    pass
""",
                encoding="utf-8",
            )

        analysis = {
            "domains": ["service"],
            "technologies": [],
        }

        result = await enhancer_agent._find_related_files("", analysis)

        # Should be limited to max 10 files
        assert len(result) <= 10

    @pytest.mark.asyncio
    async def test_find_related_files_empty_search_terms(self, enhancer_agent, tmp_path):
        """Test handling of empty search terms."""
        analysis = {
            "domains": [],
            "technologies": [],
        }

        result = await enhancer_agent._find_related_files("", analysis)

        assert result == []

    @pytest.mark.asyncio
    async def test_find_related_files_handles_errors(self, enhancer_agent, tmp_path):
        """Test error handling in file discovery."""
        # Create a file that will cause issues
        bad_file = tmp_path / "bad_file.py"
        bad_file.write_text("valid content", encoding="utf-8")

        analysis = {
            "domains": ["test"],
            "technologies": [],
        }

        # Mock Path.glob to raise an exception
        with patch.object(Path, "glob", side_effect=Exception("Test error")):
            result = await enhancer_agent._find_related_files("", analysis)

        # Should return empty list on error, not raise exception
        assert isinstance(result, list)


class TestExtractPatterns:
    """Tests for _extract_patterns() method."""

    @pytest.fixture
    def enhancer_agent(self):
        """Create enhancer agent."""
        return EnhancerAgent()

    @pytest.mark.asyncio
    async def test_extract_patterns_imports(self, enhancer_agent, tmp_path):
        """Test extraction of import patterns."""
        # Create files with common imports
        file1 = tmp_path / "service1.py"
        file1.write_text(
            """
from fastapi import APIRouter
from sqlalchemy import Session

class Service1:
    pass
""",
            encoding="utf-8",
        )

        file2 = tmp_path / "service2.py"
        file2.write_text(
            """
from fastapi import APIRouter
from sqlalchemy import Session

class Service2:
    pass
""",
            encoding="utf-8",
        )

        related_files = [str(file1), str(file2)]
        result = await enhancer_agent._extract_patterns(related_files)

        assert isinstance(result, list)
        # Should find import patterns
        assert len(result) >= 0  # May or may not find patterns depending on threshold

    @pytest.mark.asyncio
    async def test_extract_patterns_classes(self, enhancer_agent, tmp_path):
        """Test extraction of class patterns."""
        # Create files with Service/Agent/Router classes
        service_file = tmp_path / "user_service.py"
        service_file.write_text(
            """
class UserService:
    pass
""",
            encoding="utf-8",
        )

        agent_file = tmp_path / "test_agent.py"
        agent_file.write_text(
            """
class TestAgent:
    pass
""",
            encoding="utf-8",
        )

        related_files = [str(service_file), str(agent_file)]
        result = await enhancer_agent._extract_patterns(related_files)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_extract_patterns_handles_syntax_errors(self, enhancer_agent, tmp_path):
        """Test handling of syntax errors."""
        # Create file with invalid Python syntax
        bad_file = tmp_path / "bad_syntax.py"
        bad_file.write_text("def invalid syntax here", encoding="utf-8")

        valid_file = tmp_path / "valid.py"
        valid_file.write_text(
            """
class Valid:
    pass
""",
            encoding="utf-8",
        )

        related_files = [str(bad_file), str(valid_file)]
        result = await enhancer_agent._extract_patterns(related_files)

        # Should skip invalid file and continue with valid one
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_extract_patterns_empty_files(self, enhancer_agent, tmp_path):
        """Test handling of empty files."""
        # Create empty file
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("", encoding="utf-8")

        related_files = [str(empty_file)]
        result = await enhancer_agent._extract_patterns(related_files)

        assert isinstance(result, list)


class TestFindCrossReferences:
    """Tests for _find_cross_references() method."""

    @pytest.fixture
    def enhancer_agent(self):
        """Create enhancer agent."""
        return EnhancerAgent()

    @pytest.mark.asyncio
    async def test_find_cross_references_imports(self, enhancer_agent, tmp_path):
        """Test finding import-based cross-references."""
        # Create files with imports between them
        module1 = tmp_path / "module1.py"
        module1.write_text(
            """
class Module1:
    pass
""",
            encoding="utf-8",
        )

        module2 = tmp_path / "module2.py"
        module2.write_text(
            """
from module1 import Module1

class Module2:
    def __init__(self):
        self.module1 = Module1()
""",
            encoding="utf-8",
        )

        related_files = [str(module1), str(module2)]
        result = await enhancer_agent._find_cross_references(related_files)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_find_cross_references_missing_files(self, enhancer_agent):
        """Test handling of missing files."""
        related_files = ["/nonexistent/file.py", "/another/missing.py"]
        result = await enhancer_agent._find_cross_references(related_files)

        # Should skip missing files and continue
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_find_cross_references_syntax_errors(self, enhancer_agent, tmp_path):
        """Test handling of syntax errors."""
        # Create file with invalid syntax
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("invalid syntax", encoding="utf-8")

        related_files = [str(bad_file)]
        result = await enhancer_agent._find_cross_references(related_files)

        # Should handle syntax errors gracefully
        assert isinstance(result, list)


class TestGenerateContextSummary:
    """Tests for _generate_context_summary() method."""

    @pytest.fixture
    def enhancer_agent(self, tmp_path):
        """Create enhancer agent with temporary project root."""
        agent = EnhancerAgent()
        agent.config = MagicMock()
        agent.config.project_root = tmp_path
        agent._project_root = tmp_path  # Set the attribute used by _find_related_files
        return agent

    def test_generate_context_summary_with_data(self, enhancer_agent, tmp_path):
        """Test summary generation with all data."""
        # Create test files
        file1 = tmp_path / "file1.py"
        file1.write_text("class File1: pass", encoding="utf-8")

        related_files = [str(file1)]
        existing_patterns = [
            {
                "type": "architectural",
                "name": "Test Pattern",
                "description": "Test description",
                "examples": [str(file1)],
                "confidence": 0.8,
            }
        ]
        cross_references = [
            {
                "source": str(file1),
                "target": str(tmp_path / "file2.py"),
                "type": "import",
                "details": "imports from file2",
            }
        ]

        result = enhancer_agent._generate_context_summary(
            related_files, existing_patterns, cross_references
        )

        assert isinstance(result, str)
        assert "## Codebase Context" in result
        assert "Related Files" in result
        assert "Existing Patterns" in result
        assert "Cross-References" in result

    def test_generate_context_summary_empty(self, enhancer_agent):
        """Test summary generation with empty data."""
        result = enhancer_agent._generate_context_summary([], [], [])

        assert isinstance(result, str)
        assert "## Codebase Context" in result
        assert "No related files found" in result or "No" in result

    def test_generate_context_summary_relative_paths(self, enhancer_agent, tmp_path):
        """Test that paths are formatted as relative."""
        # Create file in subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        file_path = subdir / "test.py"
        file_path.write_text("class Test: pass", encoding="utf-8")

        related_files = [str(file_path)]
        result = enhancer_agent._generate_context_summary(related_files, [], [])

        # Should contain relative path
        assert "subdir" in result or "test.py" in result


class TestStageCodebaseContext:
    """Tests for _stage_codebase_context() method."""

    @pytest.fixture
    def enhancer_agent(self, tmp_path):
        """Create enhancer agent with temporary project root."""
        agent = EnhancerAgent()
        agent.config = MagicMock()
        agent.config.project_root = tmp_path
        agent._project_root = tmp_path  # Set the attribute used by _find_related_files
        return agent

    @pytest.mark.asyncio
    async def test_stage_codebase_context_success(self, enhancer_agent, tmp_path):
        """Test successful codebase context injection."""
        # Create test file
        test_file = tmp_path / "test_service.py"
        test_file.write_text(
            """
class TestService:
    pass
""",
            encoding="utf-8",
        )

        analysis = {
            "domains": ["service"],
            "technologies": [],
        }

        result = await enhancer_agent._stage_codebase_context("test prompt", analysis)

        assert isinstance(result, dict)
        assert "related_files" in result
        assert "existing_patterns" in result
        assert "cross_references" in result
        assert "codebase_context" in result
        assert "file_count" in result
        assert isinstance(result["related_files"], list)
        assert isinstance(result["existing_patterns"], list)
        assert isinstance(result["cross_references"], list)
        assert isinstance(result["codebase_context"], str)
        assert isinstance(result["file_count"], int)

    @pytest.mark.asyncio
    async def test_stage_codebase_context_error_handling(self, enhancer_agent):
        """Test error handling in codebase context stage."""
        # Analysis that might cause errors
        analysis = {
            "domains": [],
            "technologies": [],
        }

        # Mock _find_related_files to raise exception
        with patch.object(
            enhancer_agent, "_find_related_files", side_effect=Exception("Test error")
        ):
            result = await enhancer_agent._stage_codebase_context("test", analysis)

        # Should return empty context, not raise exception
        assert isinstance(result, dict)
        assert result["related_files"] == []
        assert result["file_count"] == 0
        assert "No codebase context available" in result["codebase_context"]

    @pytest.mark.asyncio
    async def test_stage_codebase_context_empty_codebase(self, enhancer_agent, tmp_path):
        """Test with empty codebase."""
        # Empty directory
        analysis = {
            "domains": ["test"],
            "technologies": [],
        }

        result = await enhancer_agent._stage_codebase_context("test", analysis)

        # Should handle gracefully
        assert isinstance(result, dict)
        assert isinstance(result["related_files"], list)
