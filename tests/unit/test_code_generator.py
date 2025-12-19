"""
Unit tests for CodeGenerator.
"""

from pathlib import Path

import pytest

from tapps_agents.agents.implementer.code_generator import CodeGenerator
from tapps_agents.core.instructions import CodeGenerationInstruction


@pytest.mark.unit
class TestCodeGenerator:
    """Test cases for CodeGenerator."""

    @pytest.fixture
    def code_generator(self):
        """Create a CodeGenerator instance."""
        return CodeGenerator()

    def test_prepare_code_generation_basic(self, code_generator):
        """Test basic code generation instruction preparation."""
        specification = "Create a function that returns hello world"
        result = code_generator.prepare_code_generation(specification)

        assert isinstance(result, CodeGenerationInstruction)
        assert result.specification == specification
        assert result.language == "python"

    def test_prepare_code_generation_with_file_path(self, code_generator):
        """Test code generation instruction with file path context."""
        specification = "Create a user model"
        file_path = Path("models/user.py")
        result = code_generator.prepare_code_generation(
            specification, file_path=file_path
        )

        assert isinstance(result, CodeGenerationInstruction)
        assert result.file_path == file_path

    def test_prepare_code_generation_with_context(self, code_generator):
        """Test code generation instruction with context."""
        specification = "Add validation function"
        context = "Use FastAPI patterns"
        result = code_generator.prepare_code_generation(
            specification, context=context
        )

        assert isinstance(result, CodeGenerationInstruction)
        assert result.context == context

    def test_prepare_code_generation_with_language(self, code_generator):
        """Test code generation instruction with different language."""
        specification = "Create a function"
        result = code_generator.prepare_code_generation(
            specification, language="javascript"
        )

        assert isinstance(result, CodeGenerationInstruction)
        assert result.language == "javascript"

    def test_prepare_refactoring(self, code_generator):
        """Test refactoring instruction preparation."""
        existing_code = "def add(a, b): return a + b"
        instruction = "Add type hints"

        result = code_generator.prepare_refactoring(existing_code, instruction)

        assert isinstance(result, CodeGenerationInstruction)
        assert existing_code in result.specification
        assert instruction in result.specification
        assert result.context == existing_code
