"""
Test data generators for CLI command testing.

Generates test files, arguments, and parameter combinations for testing.
"""

import random
import string
from pathlib import Path
from typing import Any


def generate_test_file_content(file_type: str = "python") -> str:
    """
    Generate test file content.
    
    Args:
        file_type: Type of file to generate (python, json, yaml, etc.)
        
    Returns:
        File content as string
    """
    if file_type == "python":
        return '''"""Test module for CLI testing."""
from typing import List, Dict

def process_data(items: List[Dict[str, Any]]) -> List[str]:
    """Process a list of items."""
    return [item.get("name", "") for item in items]

class TestClass:
    """Test class for CLI testing."""
    
    def __init__(self, value: int):
        self.value = value
    
    def get_value(self) -> int:
        """Get the value."""
        return self.value
'''
    elif file_type == "json":
        return '{"test": "data", "value": 42}'
    elif file_type == "yaml":
        return "test: data\nvalue: 42\n"
    else:
        return f"# Test {file_type} file\n"


def create_test_file(
    base_path: Path,
    filename: str | None = None,
    file_type: str = "python",
    content: str | None = None,
) -> Path:
    """
    Create a test file.
    
    Args:
        base_path: Base directory for file
        filename: Optional filename (generated if not provided)
        file_type: Type of file
        content: Optional content (generated if not provided)
        
    Returns:
        Path to created file
    """
    if filename is None:
        random_suffix = "".join(random.choices(string.ascii_lowercase, k=6))
        extension = {"python": ".py", "json": ".json", "yaml": ".yaml"}.get(file_type, ".txt")
        filename = f"test_{random_suffix}{extension}"
    
    file_path = base_path / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if content is None:
        content = generate_test_file_content(file_type)
    
    file_path.write_text(content)
    return file_path


def generate_file_paths(base_path: Path, count: int = 3) -> list[Path]:
    """
    Generate multiple test file paths.
    
    Args:
        base_path: Base directory
        count: Number of files to generate
        
    Returns:
        List of file paths
    """
    files = []
    for i in range(count):
        filename = f"test_file_{i}.py"
        file_path = create_test_file(base_path, filename)
        files.append(file_path)
    return files


def generate_command_args(
    command_type: str,
    include_optional: bool = False,
    format_type: str | None = None,
) -> dict[str, Any]:
    """
    Generate command arguments for testing.
    
    Args:
        command_type: Type of command (review, score, plan, etc.)
        include_optional: Whether to include optional parameters
        format_type: Optional format to use
        
    Returns:
        Dictionary of arguments
    """
    args: dict[str, Any] = {}
    
    # Common optional parameters
    if include_optional:
        if format_type:
            args["format"] = format_type
        else:
            # Default to json for most commands
            args["format"] = "json"
    
    # Command-specific arguments
    if command_type in ("review", "score", "lint", "type-check"):
        # File-based commands
        args["files"] = ["test_file.py"]  # Will be replaced with actual path
    elif command_type in ("plan", "gather-requirements"):
        # Description-based commands
        args["description"] = "Test feature description"
    elif command_type == "implement":
        args["specification"] = "Create a test function"
        args["file_path"] = "test_output.py"
    elif command_type == "test":
        args["file"] = "test_file.py"
    
    return args


def generate_parameter_combinations(
    base_params: dict[str, Any],
    optional_params: dict[str, list[Any]],
    max_combinations: int = 5,
) -> list[dict[str, Any]]:
    """
    Generate parameter combinations for testing.
    
    Args:
        base_params: Base required parameters
        optional_params: Optional parameters with their possible values
        max_combinations: Maximum combinations to generate
        
    Returns:
        List of parameter combinations
    """
    combinations: list[dict[str, Any]] = []
    
    # Start with base (minimal) combination
    combinations.append(base_params.copy())
    
    # Generate combinations with optional parameters
    optional_keys = list(optional_params.keys())
    
    # Single optional parameter combinations
    for key, values in optional_params.items():
        for value in values[:2]:  # Limit to first 2 values
            combo = base_params.copy()
            combo[key] = value
            combinations.append(combo)
            if len(combinations) >= max_combinations:
                break
        if len(combinations) >= max_combinations:
            break
    
    # Add a "full" combination with all optional params
    if len(combinations) < max_combinations:
        full_combo = base_params.copy()
        for key, values in optional_params.items():
            if values:
                full_combo[key] = values[0]
        combinations.append(full_combo)
    
    return combinations[:max_combinations]


def generate_test_project_structure(base_path: Path) -> dict[str, Path]:
    """
    Generate a test project structure.
    
    Args:
        base_path: Base directory for project
        
    Returns:
        Dictionary mapping file types to paths
    """
    project_files: dict[str, Path] = {}
    
    # Create directory structure
    (base_path / "src").mkdir(exist_ok=True)
    (base_path / "tests").mkdir(exist_ok=True)
    (base_path / "docs").mkdir(exist_ok=True)
    
    # Create files
    project_files["main"] = create_test_file(base_path / "src", "main.py")
    project_files["utils"] = create_test_file(base_path / "src", "utils.py")
    project_files["test_main"] = create_test_file(base_path / "tests", "test_main.py")
    project_files["readme"] = create_test_file(base_path, "README.md", file_type="markdown")
    
    return project_files


def generate_invalid_args() -> dict[str, Any]:
    """
    Generate invalid arguments for error testing.
    
    Returns:
        Dictionary of invalid arguments
    """
    return {
        "invalid_format": "invalid_format_value",
        "invalid_file": "/nonexistent/path/to/file.py",
        "invalid_number": "not_a_number",
        "invalid_choice": "invalid_choice_value",
    }


def generate_edge_case_args() -> dict[str, Any]:
    """
    Generate edge case arguments for testing.
    
    Returns:
        Dictionary of edge case arguments
    """
    return {
        "empty_string": "",
        "very_long_string": "x" * 1000,
        "special_chars": "test@#$%^&*()[]{}|\\:;\"'<>?,./",
        "unicode": "测试文件_тест_🎯",
        "whitespace": "   test   ",
    }

