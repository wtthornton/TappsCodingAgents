"""
Unit tests for TestGenerator.
"""

from pathlib import Path

import pytest

from tapps_agents.agents.tester.test_generator import TestGenerator
from tapps_agents.core.instructions import TestGenerationInstruction


@pytest.mark.unit
class TestTestGenerator:
    """Test cases for TestGenerator."""

    @pytest.fixture
    def test_generator(self):
        """Create a TestGenerator instance."""
        return TestGenerator()

    @pytest.fixture
    def sample_code_file(self, tmp_path: Path):
        """Create a sample code file."""
        code_file = tmp_path / "sample.py"
        code_file.write_text(
            """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

class Calculator:
    def multiply(self, a, b):
        return a * b
"""
        )
        return code_file

    def test_prepare_unit_tests_basic(
        self, test_generator, sample_code_file
    ):
        """Test basic unit test instruction preparation."""
        result = test_generator.prepare_unit_tests(sample_code_file)

        assert isinstance(result, TestGenerationInstruction)
        assert result.target_file == str(sample_code_file)
        assert result.test_framework in ["pytest", "unittest", "nose"]

    def test_prepare_unit_tests_with_test_path(
        self, test_generator, sample_code_file
    ):
        """Test unit test instruction with test file path."""
        test_path = Path("tests/test_sample.py")
        result = test_generator.prepare_unit_tests(
            sample_code_file, test_path=test_path
        )

        assert isinstance(result, TestGenerationInstruction)
        assert result.target_file == str(test_path)

    def test_prepare_unit_tests_with_context(
        self, test_generator, sample_code_file
    ):
        """Test unit test instruction with context."""
        context = "Use pytest fixtures for setup"
        result = test_generator.prepare_unit_tests(
            sample_code_file, context=context
        )

        assert isinstance(result, TestGenerationInstruction)
        assert result.coverage_requirements["context"] == context

    def test_prepare_integration_tests(
        self, test_generator, tmp_path: Path
    ):
        """Test integration test instruction preparation."""
        file1 = tmp_path / "module1.py"
        file1.write_text("def func1(): return 1")

        file2 = tmp_path / "module2.py"
        file2.write_text("def func2(): return 2")

        result = test_generator.prepare_integration_tests([file1, file2])

        assert isinstance(result, TestGenerationInstruction)
        assert result.test_framework == "pytest"
        assert "module1.py" in result.coverage_requirements.get("file_paths", []) or "module2.py" in result.coverage_requirements.get("file_paths", [])

    def test_analyze_code(self, test_generator, sample_code_file):
        """Test code analysis."""
        code = sample_code_file.read_text()
        analysis = test_generator._analyze_code(code, sample_code_file)

        assert "functions" in analysis
        assert "classes" in analysis
        assert "imports" in analysis
        assert "test_framework" in analysis

        # Check functions are detected
        func_names = [f["name"] for f in analysis["functions"]]
        assert "add" in func_names
        assert "subtract" in func_names

        # Check classes are detected
        class_names = [c["name"] for c in analysis["classes"]]
        assert "Calculator" in class_names

    def test_detect_test_framework_pytest(self, test_generator):
        """Test pytest framework detection."""
        code = "import pytest\ndef test_something(): pass"
        framework = test_generator._detect_test_framework(code)
        assert framework == "pytest"

    def test_detect_test_framework_unittest(self, test_generator):
        """Test unittest framework detection."""
        code = "import unittest\nclass TestCase(unittest.TestCase): pass"
        framework = test_generator._detect_test_framework(code)
        assert framework == "unittest"

    def test_detect_test_framework_default(self, test_generator):
        """Test default framework detection."""
        code = "def some_function(): pass"
        framework = test_generator._detect_test_framework(code)
        assert framework == "pytest"  # Default

    def test_build_unit_test_prompt(self, test_generator, sample_code_file):
        """Test unit test prompt building."""
        code = sample_code_file.read_text()
        analysis = test_generator._analyze_code(code, sample_code_file)

        prompt = test_generator._build_unit_test_prompt(code, analysis, None, None)

        assert "unit tests" in prompt.lower()
        assert "sample.py" in prompt
        assert "add" in prompt or "Calculator" in prompt
        assert "pytest" in prompt.lower() or "framework" in prompt.lower()

    def test_build_integration_test_prompt(self, test_generator):
        """Test integration test prompt building."""
        code = "def func1(): pass\ndef func2(): pass"
        prompt = test_generator._build_integration_test_prompt(code, None, None)

        assert "integration tests" in prompt.lower()
        assert "modules" in prompt.lower() or "workflows" in prompt.lower()
