"""
Project templates for E2E testing.

Provides three tiers of project templates:
- minimal: Single file, basic structure
- small: Multiple files, basic test structure, minimal dependencies
- medium: Multi-file project, tests, dependencies, config files

All templates are deterministic and can be created in isolated temporary directories.
"""

from pathlib import Path
from typing import Literal

TemplateType = Literal["minimal", "small", "medium"]


def create_minimal_template(project_path: Path) -> Path:
    """
    Create a minimal project template (single file, basic structure).

    Args:
        project_path: Path where the project should be created

    Returns:
        Path to the created project directory
    """
    project_path.mkdir(parents=True, exist_ok=True)

    # Create minimal Python file
    main_file = project_path / "main.py"
    main_file.write_text(
        """def hello():
    \"\"\"Simple hello function.\"\"\"
    return "Hello, World!"

if __name__ == "__main__":
    print(hello())
"""
    )

    # Create .tapps-agents directory structure and config so workflow executor
    # does not require Beads (bd) in e2e tests
    config_dir = project_path / ".tapps-agents"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.yaml"
    config_file.write_text(
        "# E2E test project: disable Beads so tests run without bd init\nbeads:\n  enabled: false\n  required: false\n",
        encoding="utf-8",
    )

    return project_path


def create_small_template(project_path: Path) -> Path:
    """
    Create a small project template (multiple files, basic test structure, minimal dependencies).

    Args:
        project_path: Path where the project should be created

    Returns:
        Path to the created project directory
    """
    project_path.mkdir(parents=True, exist_ok=True)

    # Create source directory
    src_dir = project_path / "src"
    src_dir.mkdir(exist_ok=True)

    # Create main module
    main_module = src_dir / "calculator.py"
    main_module.write_text(
        """\"\"\"Simple calculator module.\"\"\"

def add(a: float, b: float) -> float:
    \"\"\"Add two numbers.\"\"\"
    return a + b

def subtract(a: float, b: float) -> float:
    \"\"\"Subtract two numbers.\"\"\"
    return a - b

def multiply(a: float, b: float) -> float:
    \"\"\"Multiply two numbers.\"\"\"
    return a * b

def divide(a: float, b: float) -> float:
    \"\"\"Divide two numbers.\"\"\"
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
"""
    )

    # Create tests directory
    tests_dir = project_path / "tests"
    tests_dir.mkdir(exist_ok=True)

    # Create test file
    test_file = tests_dir / "test_calculator.py"
    test_file.write_text(
        """\"\"\"Tests for calculator module.\"\"\"

import pytest
from src.calculator import add, subtract, multiply, divide

def test_add():
    assert add(2, 3) == 5

def test_subtract():
    assert subtract(5, 3) == 2

def test_multiply():
    assert multiply(2, 3) == 6

def test_divide():
    assert divide(6, 3) == 2

def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(1, 0)
"""
    )

    # Create .tapps-agents directory structure and config so workflow executor
    # does not require Beads (bd) in e2e tests
    config_dir = project_path / ".tapps-agents"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.yaml"
    config_file.write_text(
        "# E2E test project: disable Beads so tests run without bd init\nbeads:\n  enabled: false\n  required: false\n",
        encoding="utf-8",
    )

    # Create basic README
    readme = project_path / "README.md"
    readme.write_text(
        """# Test Project

A simple calculator project for testing.
"""
    )

    return project_path


def create_medium_template(project_path: Path) -> Path:
    """
    Create a medium project template (multi-file project, tests, dependencies, config files).

    Args:
        project_path: Path where the project should be created

    Returns:
        Path to the created project directory
    """
    project_path.mkdir(parents=True, exist_ok=True)

    # Create source directory structure
    src_dir = project_path / "src"
    src_dir.mkdir(exist_ok=True)
    package_dir = src_dir / "mypackage"
    package_dir.mkdir(exist_ok=True)

    # Create __init__.py
    init_file = package_dir / "__init__.py"
    init_file.write_text(
        """\"\"\"MyPackage - A test package.\"\"\"

__version__ = "1.0.0"
"""
    )

    # Create main module
    main_module = package_dir / "core.py"
    main_module.write_text(
        """\"\"\"Core functionality.\"\"\"

from typing import List, Dict, Any

class DataProcessor:
    \"\"\"Process data items.\"\"\"

    def __init__(self):
        self.items: List[Dict[str, Any]] = []

    def add_item(self, item: Dict[str, Any]) -> None:
        \"\"\"Add an item to the processor.\"\"\"
        self.items.append(item)

    def process(self) -> List[Dict[str, Any]]:
        \"\"\"Process all items.\"\"\"
        return [{"id": i, **item} for i, item in enumerate(self.items)]

    def clear(self) -> None:
        \"\"\"Clear all items.\"\"\"
        self.items.clear()
"""
    )

    # Create utils module
    utils_module = package_dir / "utils.py"
    utils_module.write_text(
        """\"\"\"Utility functions.\"\"\"

import json
from pathlib import Path

def load_config(config_path: Path) -> dict:
    \"\"\"Load configuration from JSON file.\"\"\"
    if not config_path.exists():
        return {}
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)

def save_config(config: dict, config_path: Path) -> None:
    \"\"\"Save configuration to JSON file.\"\"\"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
"""
    )

    # Create tests directory
    tests_dir = project_path / "tests"
    tests_dir.mkdir(exist_ok=True)

    # Create test files
    test_core = tests_dir / "test_core.py"
    test_core.write_text(
        """\"\"\"Tests for core module.\"\"\"

import pytest
from src.mypackage.core import DataProcessor

def test_data_processor_init():
    processor = DataProcessor()
    assert len(processor.items) == 0

def test_data_processor_add_item():
    processor = DataProcessor()
    processor.add_item({"name": "test"})
    assert len(processor.items) == 1

def test_data_processor_process():
    processor = DataProcessor()
    processor.add_item({"name": "test"})
    result = processor.process()
    assert len(result) == 1
    assert result[0]["id"] == 0
    assert result[0]["name"] == "test"

def test_data_processor_clear():
    processor = DataProcessor()
    processor.add_item({"name": "test"})
    processor.clear()
    assert len(processor.items) == 0
"""
    )

    test_utils = tests_dir / "test_utils.py"
    test_utils.write_text(
        """\"\"\"Tests for utils module.\"\"\"

import json
from pathlib import Path
import tempfile

from src.mypackage.utils import load_config, save_config

def test_save_and_load_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config = {"key": "value", "number": 42}
        save_config(config, config_path)
        loaded = load_config(config_path)
        assert loaded == config

def test_load_nonexistent_config():
    config_path = Path("/nonexistent/config.json")
    result = load_config(config_path)
    assert result == {}
"""
    )

    # Create .tapps-agents directory structure and config so workflow executor
    # does not require Beads (bd) in e2e tests
    config_dir = project_path / ".tapps-agents"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.yaml"
    config_file.write_text(
        "# E2E test project: disable Beads so tests run without bd init\nbeads:\n  enabled: false\n  required: false\n",
        encoding="utf-8",
    )

    # Create workflow-state directory
    workflow_state_dir = config_dir / "workflow-state"
    workflow_state_dir.mkdir(exist_ok=True)

    # Create worktrees directory
    worktrees_dir = config_dir / "worktrees"
    worktrees_dir.mkdir(exist_ok=True)

    # Create requirements.txt
    requirements = project_path / "requirements.txt"
    requirements.write_text(
        """pytest>=7.0.0
"""
    )

    # Create pyproject.toml
    pyproject = project_path / "pyproject.toml"
    pyproject.write_text(
        """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "mypackage"
version = "1.0.0"
description = "A test package"
requires-python = ">=3.9"
dependencies = []

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
"""
    )

    # Create README
    readme = project_path / "README.md"
    readme.write_text(
        """# MyPackage

A medium-complexity test project with multiple modules, tests, and configuration files.

## Structure

- `src/mypackage/` - Source code
- `tests/` - Test files
- `.tapps-agents/` - TappsCodingAgents configuration
"""
    )

    return project_path


def create_template(template_type: TemplateType, project_path: Path) -> Path:
    """
    Create a project template of the specified type.

    Args:
        template_type: Type of template to create (minimal, small, medium)
        project_path: Path where the project should be created

    Returns:
        Path to the created project directory

    Raises:
        ValueError: If template_type is not recognized
    """
    if template_type == "minimal":
        return create_minimal_template(project_path)
    elif template_type == "small":
        return create_small_template(project_path)
    elif template_type == "medium":
        return create_medium_template(project_path)
    else:
        raise ValueError(f"Unknown template type: {template_type}")
