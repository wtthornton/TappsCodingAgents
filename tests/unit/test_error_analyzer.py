"""
Unit tests for ErrorAnalyzer.
"""

from pathlib import Path

import pytest

from tapps_agents.agents.debugger.error_analyzer import ErrorAnalyzer
from tapps_agents.core.instructions import ErrorAnalysisInstruction


@pytest.mark.unit
class TestErrorAnalyzer:
    """Test cases for ErrorAnalyzer."""

    @pytest.fixture
    def error_analyzer(self):
        """Create an ErrorAnalyzer instance."""
        return ErrorAnalyzer()

    def test_prepare_error_analysis_basic(self, error_analyzer):
        """Test basic error analysis instruction preparation."""
        error_msg = "NameError: name 'x' is not defined"

        result = error_analyzer.prepare_error_analysis(error_msg)

        assert isinstance(result, ErrorAnalysisInstruction)
        assert result.error_message == error_msg
        assert result.context_lines == 50

    def test_prepare_error_analysis_with_stack_trace(self, error_analyzer):
        """Test error analysis instruction with stack trace."""
        error_msg = "ValueError: invalid literal"
        stack_trace = (
            'File "test.py", line 42, in function_name\n    result = int("abc")'
        )

        result = error_analyzer.prepare_error_analysis(
            error_msg, stack_trace=stack_trace
        )

        assert isinstance(result, ErrorAnalysisInstruction)
        assert result.error_message == error_msg
        assert result.stack_trace == stack_trace

    def test_prepare_error_analysis_with_code_context(self, error_analyzer):
        """Test error analysis instruction with code context."""
        error_msg = "IndexError: list index out of range"
        code_context = "def process(data):\n    return data[10]"

        result = error_analyzer.prepare_error_analysis(
            error_msg, code_context=code_context
        )

        assert isinstance(result, ErrorAnalysisInstruction)
        assert result.error_message == error_msg

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

    def test_prepare_code_trace(self, error_analyzer, tmp_path: Path):
        """Test code trace instruction preparation."""
        code_file = tmp_path / "test.py"
        code_file.write_text("def func1():\n    return func2()\ndef func2():\n    pass")

        result = error_analyzer.prepare_code_trace(code_file, function_name="func1")

        assert isinstance(result, ErrorAnalysisInstruction)
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_analyze_error_basic(self, error_analyzer):
        """Test basic error analysis."""
        error_msg = "NameError: name 'x' is not defined"

        result = await error_analyzer.analyze_error(error_msg)

        assert isinstance(result, dict)
        assert "error_type" in result
        assert "error_message" in result
        assert "root_cause" in result
        assert "suggestions" in result
        assert "fix_examples" in result
        assert "file_location" in result
        assert "line_number" in result
        assert result["error_message"] == error_msg
        assert result["error_type"] == "NameError"
        assert isinstance(result["suggestions"], list)
        assert len(result["suggestions"]) > 0
        assert isinstance(result["fix_examples"], list)

    @pytest.mark.asyncio
    async def test_analyze_error_attribute_error(self, error_analyzer):
        """Test AttributeError analysis."""
        error_msg = "AttributeError: 'ErrorAnalyzer' object has no attribute 'analyze_error'"

        result = await error_analyzer.analyze_error(error_msg)

        assert result["error_type"] == "AttributeError"
        assert len(result["suggestions"]) > 0
        assert any("attribute" in s.lower() for s in result["suggestions"])
        assert len(result["fix_examples"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_error_with_stack_trace(self, error_analyzer):
        """Test error analysis with stack trace."""
        error_msg = "ValueError: invalid literal for int() with base 10: 'abc'"
        stack_trace = 'File "test.py", line 42, in process_data\n    result = int("abc")'

        result = await error_analyzer.analyze_error(error_msg, stack_trace=stack_trace)

        assert result["error_type"] == "ValueError"
        assert result["file_location"] == "test.py"
        assert result["line_number"] == 42
        assert len(result["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_error_with_file_path(self, error_analyzer, tmp_path: Path):
        """Test error analysis with file path."""
        error_msg = "KeyError: 'missing_key'"
        file_path = tmp_path / "test.py"
        file_path.write_text("# test file")

        result = await error_analyzer.analyze_error(
            error_msg, file_path=file_path
        )

        assert result["error_type"] == "KeyError"
        assert result["file_location"] == str(file_path)
        assert len(result["suggestions"]) > 0
        assert any("dictionary" in s.lower() or ".get()" in s.lower() for s in result["suggestions"])

    @pytest.mark.asyncio
    async def test_analyze_error_type_error(self, error_analyzer):
        """Test TypeError analysis."""
        error_msg = "TypeError: unsupported operand type(s) for +: 'int' and 'str'"

        result = await error_analyzer.analyze_error(error_msg)

        assert result["error_type"] == "TypeError"
        assert len(result["suggestions"]) > 0
        assert any("type" in s.lower() for s in result["suggestions"])

    @pytest.mark.asyncio
    async def test_analyze_error_index_error(self, error_analyzer):
        """Test IndexError analysis."""
        error_msg = "IndexError: list index out of range"

        result = await error_analyzer.analyze_error(error_msg)

        assert result["error_type"] == "IndexError"
        assert len(result["suggestions"]) > 0
        assert any("index" in s.lower() or "bounds" in s.lower() for s in result["suggestions"])
        assert len(result["fix_examples"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_error_file_not_found(self, error_analyzer):
        """Test FileNotFoundError analysis."""
        error_msg = "FileNotFoundError: [Errno 2] No such file or directory: 'missing.txt'"

        result = await error_analyzer.analyze_error(error_msg)

        assert result["error_type"] == "FileNotFoundError"
        assert len(result["suggestions"]) > 0
        assert any("file" in s.lower() or "path" in s.lower() for s in result["suggestions"])

    @pytest.mark.asyncio
    async def test_analyze_error_unknown_error(self, error_analyzer):
        """Test analysis of unknown error type."""
        error_msg = "CustomError: something went wrong"

        result = await error_analyzer.analyze_error(error_msg)

        assert result["error_type"] == "CustomError"
        assert len(result["suggestions"]) > 0
        assert result["root_cause"] is not None

    @pytest.mark.asyncio
    async def test_analyze_error_with_code_context(self, error_analyzer):
        """Test error analysis with code context."""
        error_msg = "NameError: name 'undefined_var' is not defined"
        code_context = "def test():\n    return undefined_var"

        result = await error_analyzer.analyze_error(
            error_msg, code_context=code_context
        )

        assert result["error_type"] == "NameError"
        assert len(result["suggestions"]) > 0
        assert len(result["fix_examples"]) > 0