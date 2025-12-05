"""
Unit tests for CodeGenerator.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

from tapps_agents.agents.implementer.code_generator import CodeGenerator
from tapps_agents.core.mal import MAL


@pytest.mark.unit
class TestCodeGenerator:
    """Test cases for CodeGenerator."""
    
    @pytest.fixture
    def mock_mal(self):
        """Create a mock MAL."""
        mal = MagicMock(spec=MAL)
        mal.generate = AsyncMock(return_value="def hello():\n    return 'world'")
        return mal
    
    @pytest.fixture
    def code_generator(self, mock_mal):
        """Create a CodeGenerator instance."""
        return CodeGenerator(mock_mal)
    
    @pytest.mark.asyncio
    async def test_generate_code_basic(self, code_generator, mock_mal):
        """Test basic code generation."""
        specification = "Create a function that returns hello world"
        result = await code_generator.generate_code(specification)
        
        assert isinstance(result, str)
        assert "def" in result.lower() or "function" in result.lower()
        mock_mal.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_code_with_file_path(self, code_generator, mock_mal):
        """Test code generation with file path context."""
        specification = "Create a user model"
        file_path = Path("models/user.py")
        result = await code_generator.generate_code(specification, file_path=file_path)
        
        assert isinstance(result, str)
        # Check that file_path was included in prompt
        call_args = mock_mal.generate.call_args[0][0]
        assert "models/user.py" in call_args or "user.py" in call_args
    
    @pytest.mark.asyncio
    async def test_generate_code_with_context(self, code_generator, mock_mal):
        """Test code generation with context."""
        specification = "Add validation function"
        context = "Use FastAPI patterns"
        result = await code_generator.generate_code(specification, context=context)
        
        assert isinstance(result, str)
        # Check that context was included in prompt
        call_args = mock_mal.generate.call_args[0][0]
        assert "FastAPI" in call_args
    
    @pytest.mark.asyncio
    async def test_generate_code_with_language(self, code_generator, mock_mal):
        """Test code generation with different language."""
        specification = "Create a function"
        result = await code_generator.generate_code(specification, language="javascript")
        
        assert isinstance(result, str)
        # Check that language was included in prompt
        call_args = mock_mal.generate.call_args[0][0]
        assert "javascript" in call_args.lower()
    
    @pytest.mark.asyncio
    async def test_generate_code_extracts_from_code_block(self, code_generator, mock_mal):
        """Test that code is extracted from markdown code blocks."""
        mock_mal.generate = AsyncMock(return_value="```python\ndef hello():\n    return 'world'\n```")
        result = await code_generator.generate_code("Create a function")
        
        assert "def hello()" in result
        assert "```" not in result  # Code blocks should be removed
    
    @pytest.mark.asyncio
    async def test_refactor_code(self, code_generator, mock_mal):
        """Test code refactoring."""
        existing_code = "def add(a, b): return a + b"
        instruction = "Add type hints"
        
        result = await code_generator.refactor_code(existing_code, instruction)
        
        assert isinstance(result, str)
        mock_mal.generate.assert_called_once()
        # Check that original code and instruction were in prompt
        call_args = mock_mal.generate.call_args[0][0]
        assert existing_code in call_args
        assert instruction in call_args
    
    @pytest.mark.asyncio
    async def test_generate_code_handles_errors(self, code_generator, mock_mal):
        """Test error handling in code generation."""
        mock_mal.generate = AsyncMock(side_effect=Exception("LLM error"))
        
        with pytest.raises(RuntimeError) as exc_info:
            await code_generator.generate_code("Create a function")
        
        assert "Code generation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_refactor_code_handles_errors(self, code_generator, mock_mal):
        """Test error handling in code refactoring."""
        mock_mal.generate = AsyncMock(side_effect=Exception("LLM error"))
        
        with pytest.raises(RuntimeError) as exc_info:
            await code_generator.refactor_code("def x(): pass", "Refactor")
        
        assert "Code refactoring failed" in str(exc_info.value)


