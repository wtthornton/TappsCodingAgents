"""
Unit tests for ASTParser.
"""

from pathlib import Path

import pytest

from tapps_agents.core.ast_parser import ASTParser, ModuleInfo


@pytest.mark.unit
class TestASTParser:
    """Test cases for ASTParser."""

    @pytest.fixture
    def parser(self):
        """Create an ASTParser instance."""
        return ASTParser()

    @pytest.fixture
    def sample_python_file(self, tmp_path: Path):
        """Create a sample Python file."""
        code_file = tmp_path / "test_module.py"
        code_file.write_text(
            """
\"\"\"Module docstring.\"\"\"

import os
from typing import List, Dict

CONSTANT = 42

def func1(param1: str, param2: int) -> str:
    \"\"\"Function docstring.\"\"\"
    return f"{param1}: {param2}"

class MyClass:
    \"\"\"Class docstring.\"\"\"
    
    def method1(self):
        pass
    
    def method2(self, arg: str):
        return arg
"""
        )
        return code_file

    def test_parse_file_basic(self, parser, sample_python_file):
        """Test basic file parsing."""
        module_info = parser.parse_file(sample_python_file)

        assert isinstance(module_info, ModuleInfo)
        assert len(module_info.imports) > 0
        assert len(module_info.functions) > 0
        assert len(module_info.classes) > 0

    def test_parse_file_imports(self, parser, sample_python_file):
        """Test import extraction."""
        module_info = parser.parse_file(sample_python_file)

        assert "os" in module_info.imports
        assert any("List" in imp or "Dict" in imp for imp in module_info.imports)

    def test_parse_file_functions(self, parser, sample_python_file):
        """Test function extraction."""
        module_info = parser.parse_file(sample_python_file)

        func_names = [f.name for f in module_info.functions]
        assert "func1" in func_names

        func1 = next(f for f in module_info.functions if f.name == "func1")
        assert "param1" in func1.args
        assert "param2" in func1.args
        assert func1.docstring is not None

    def test_parse_file_classes(self, parser, sample_python_file):
        """Test class extraction."""
        module_info = parser.parse_file(sample_python_file)

        class_names = [c.name for c in module_info.classes]
        assert "MyClass" in class_names

        my_class = next(c for c in module_info.classes if c.name == "MyClass")
        assert "method1" in my_class.methods
        assert "method2" in my_class.methods
        assert my_class.docstring is not None

    def test_parse_file_cache(self, parser, sample_python_file):
        """Test parsing cache."""
        module_info1 = parser.parse_file(sample_python_file, use_cache=True)
        module_info2 = parser.parse_file(sample_python_file, use_cache=True)

        # Should return same object from cache
        assert module_info1 is module_info2

    def test_parse_file_no_cache(self, parser, sample_python_file):
        """Test parsing without cache."""
        module_info1 = parser.parse_file(sample_python_file, use_cache=False)
        module_info2 = parser.parse_file(sample_python_file, use_cache=False)

        # Should be different objects
        assert module_info1 is not module_info2
        # But same content
        assert module_info1.functions[0].name == module_info2.functions[0].name

    def test_get_file_structure(self, parser, sample_python_file):
        """Test file structure extraction."""
        structure = parser.get_file_structure(sample_python_file)

        assert "file" in structure
        assert "imports" in structure
        assert "classes" in structure
        assert "functions" in structure
        assert len(structure["functions"]) > 0

    def test_clear_cache(self, parser, sample_python_file):
        """Test cache clearing."""
        parser.parse_file(sample_python_file, use_cache=True)
        assert len(parser._cache) > 0

        parser.clear_cache()
        assert len(parser._cache) == 0
