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
