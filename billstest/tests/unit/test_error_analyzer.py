"""
Unit tests for ErrorAnalyzer.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from tapps_agents.agents.debugger.error_analyzer import ErrorAnalyzer
from tapps_agents.core.mal import MAL


@pytest.mark.unit
class TestErrorAnalyzer:
    """Test cases for ErrorAnalyzer."""

    @pytest.fixture
    def mock_mal(self):
        """Create a mock MAL."""
        mal = MagicMock(spec=MAL)
        mal.generate = AsyncMock(
            return_value="""
ROOT_CAUSE: Missing import statement
ISSUE: NameError occurs because module is not imported
SUGGESTIONS:
1. Add import statement at the top of the file
2. Check if module name is correct
FIX_EXAMPLES:
```python
import module_name
```
"""
        )
        return mal

    @pytest.fixture
    def error_analyzer(self, mock_mal):
        """Create an ErrorAnalyzer instance."""
        return ErrorAnalyzer(mock_mal)

    @pytest.mark.asyncio
    async def test_analyze_error_basic(self, error_analyzer, mock_mal):
        """Test basic error analysis."""
        error_msg = "NameError: name 'x' is not defined"

        result = await error_analyzer.analyze_error(error_msg)

        assert "error_type" in result
        assert "error_message" in result
        assert "analysis" in result
        assert "suggestions" in result
        assert result["error_message"] == error_msg
        mock_mal.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_error_with_stack_trace(self, error_analyzer, mock_mal):
        """Test error analysis with stack trace."""
        error_msg = "ValueError: invalid literal"
        stack_trace = (
            'File "test.py", line 42, in function_name\n    result = int("abc")'
        )

        result = await error_analyzer.analyze_error(error_msg, stack_trace=stack_trace)

        assert result["error_type"] == "ValueError"
        assert result["file_location"] == "test.py"
        assert result["line_number"] == 42
        call_args = mock_mal.generate.call_args[0][0]
        assert 'File "test.py"' in call_args

    @pytest.mark.asyncio
    async def test_analyze_error_with_code_context(self, error_analyzer, mock_mal):
        """Test error analysis with code context."""
        error_msg = "IndexError: list index out of range"
        code_context = "def process(data):\n    return data[10]"

        result = await error_analyzer.analyze_error(
            error_msg, code_context=code_context
        )

        assert "suggestions" in result
        call_args = mock_mal.generate.call_args[0][0]
        assert "process(data)" in call_args

    def test_parse_error_basic(self, error_analyzer):
        """Test error parsing."""
        error_msg = "ValueError: invalid input"
        result = error_analyzer._parse_error(error_msg)

        assert result["type"] == "ValueError"
        assert result["message"] == error_msg

    def test_parse_error_with_stack_trace(self, error_analyzer):
        """Test error parsing with stack trace."""
        error_msg = "NameError: name 'x' is not defined"
        stack_trace = 'File "code.py", line 5, in test\n    print(x)'

        result = error_analyzer._parse_error(error_msg, stack_trace)

        assert result["type"] == "NameError"
        assert result["file"] == "code.py"
        assert result["line"] == 5

    def test_analyze_code_structure(self, error_analyzer, tmp_path: Path):
        """Test code structure analysis."""
        code_file = tmp_path / "test.py"
        code_file.write_text(
            """
def func1():
    pass

class MyClass:
    def method(self):
        pass
"""
        )

        code = code_file.read_text()
        structure = error_analyzer._analyze_code_structure(code)

        assert "functions" in structure
        assert "classes" in structure
        assert len(structure["functions"]) > 0
        assert len(structure["classes"]) > 0

    def test_parse_llm_analysis(self, error_analyzer):
        """Test LLM analysis parsing."""
        analysis_text = """
ROOT_CAUSE: Missing import
ISSUE: Module not found
SUGGESTIONS:
1. Add import
2. Check module name
FIX_EXAMPLES:
```python
import module
```
"""
        result = error_analyzer._parse_llm_analysis(analysis_text)

        assert "root_cause" in result
        assert "issue" in result
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_trace_code_path(self, error_analyzer, tmp_path: Path, mock_mal):
        """Test code path tracing."""
        code_file = tmp_path / "test.py"
        code_file.write_text("def func1():\n    return func2()\ndef func2():\n    pass")

        result = await error_analyzer.trace_code_path(code_file, function_name="func1")

        assert "file" in result
        assert "function" in result
        assert "trace_analysis" in result
        assert result["function"] == "func1"
