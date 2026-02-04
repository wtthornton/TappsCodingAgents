"""
Demo helpers extracted from demo/run_demo.py for use in tests.

Provides reusable functions for creating test projects, sample code,
and running demo scenarios in test contexts.
"""

import sys
from pathlib import Path

from tests.e2e.fixtures.cli_harness import CLIHarness, CLIResult


def get_cli_command() -> list[str]:
    """
    Get the CLI command, using module invocation as fallback.
    
    Returns:
        Command list for running tapps-agents CLI
    """
    import subprocess
    
    # Try direct command first
    try:
        result = subprocess.run(
            ["tapps-agents", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return ["tapps-agents"]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Fallback to module invocation
    return [sys.executable, "-m", "tapps_agents.cli"]


def create_test_project(base_path: Path, project_name: str | None = None) -> Path:
    """
    Create a test project directory with sample code.
    
    Args:
        base_path: Base directory for project
        project_name: Optional project name
        
    Returns:
        Path to created project
    """
    if project_name is None:
        import uuid
        project_name = f"test_project_{uuid.uuid4().hex[:8]}"
    
    project_path = base_path / project_name
    project_path.mkdir(parents=True, exist_ok=True)
    
    # Create directory structure
    src_dir = project_path / "src"
    src_dir.mkdir(exist_ok=True)
    
    # Create sample calculator.py with intentional issues
    calculator_code = '''"""Simple calculator with intentional issues for demo."""

def add(a, b):
    """Add two numbers."""
    return a + b

def divide(a, b):
    """Divide two numbers."""
    return a / b  # Bug: No zero check

def calculate_total(items):
    """Calculate total price."""
    total = 0
    for item in items:
        total += item["price"]  # Bug: No error handling
    return total

def process_data(data):
    """Process user data."""
    # Security issue: No input validation
    result = eval(data)  # Dangerous!
    return result
'''
    
    calculator_file = src_dir / "calculator.py"
    calculator_file.write_text(calculator_code)
    
    # Create a simple API file
    api_code = '''"""Simple REST API example."""

from typing import List, Dict

class TaskAPI:
    """Task management API."""
    
    def __init__(self):
        self.tasks: List[Dict] = []
    
    def create_task(self, title: str, description: str) -> Dict:
        """Create a new task."""
        task = {
            "id": len(self.tasks) + 1,
            "title": title,
            "description": description,
            "completed": False
        }
        self.tasks.append(task)
        return task
    
    def get_task(self, task_id: int) -> Dict:
        """Get a task by ID."""
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None  # Bug: Should raise exception
    
    def complete_task(self, task_id: int) -> bool:
        """Mark task as completed."""
        task = self.get_task(task_id)
        if task:
            task["completed"] = True
            return True
        return False
'''
    
    api_file = src_dir / "api.py"
    api_file.write_text(api_code)
    
    return project_path


def create_test_code_files(project_path: Path) -> dict[str, Path]:
    """
    Create test code files in project.
    
    Args:
        project_path: Project root directory
        
    Returns:
        Dictionary mapping file names to paths
    """
    src_dir = project_path / "src"
    src_dir.mkdir(exist_ok=True)
    
    files: dict[str, Path] = {}
    
    # Calculator file
    calculator_file = src_dir / "calculator.py"
    calculator_file.write_text(
        '''"""Simple calculator with intentional issues for demo."""

def add(a, b):
    """Add two numbers."""
    return a + b

def divide(a, b):
    """Divide two numbers."""
    return a / b  # Bug: No zero check
'''
    )
    files["calculator"] = calculator_file
    
    # API file
    api_file = src_dir / "api.py"
    api_file.write_text(
        '''"""Simple REST API example."""

from typing import List, Dict

class TaskAPI:
    """Task management API."""
    
    def __init__(self):
        self.tasks: List[Dict] = []
'''
    )
    files["api"] = api_file
    
    return files


def run_code_scoring_demo(harness: CLIHarness, project_path: Path, test_file: Path) -> CLIResult:
    """
    Run code scoring demo scenario.
    
    Args:
        harness: CLI harness instance
        project_path: Project directory
        test_file: File to score
        
    Returns:
        CLI execution result
    """
    cli_cmd = get_cli_command()
    return harness.run_command(
        cli_cmd + ["score", str(test_file), "--format", "json"],
        cwd=project_path,
    )


def run_code_review_demo(harness: CLIHarness, project_path: Path, test_file: Path) -> CLIResult:
    """
    Run code review demo scenario.
    
    Args:
        harness: CLI harness instance
        project_path: Project directory
        test_file: File to review
        
    Returns:
        CLI execution result
    """
    cli_cmd = get_cli_command()
    return harness.run_command(
        cli_cmd + ["reviewer", "review", str(test_file), "--format", "json"],
        cwd=project_path,
    )


def run_quality_tools_demo(harness: CLIHarness, project_path: Path, src_dir: Path) -> list[CLIResult]:
    """
    Run quality tools demo (linting, type checking).
    
    Args:
        harness: CLI harness instance
        project_path: Project directory
        src_dir: Source directory
        
    Returns:
        List of CLI execution results
    """
    cli_cmd = get_cli_command()
    results: list[CLIResult] = []
    
    # Run linting
    lint_result = harness.run_command(
        cli_cmd + ["reviewer", "lint", str(src_dir), "--format", "json"],
        cwd=project_path,
    )
    results.append(lint_result)
    
    # Run type checking
    type_check_result = harness.run_command(
        cli_cmd + ["reviewer", "type-check", str(src_dir), "--format", "json"],
        cwd=project_path,
    )
    results.append(type_check_result)
    
    return results


def check_test_prerequisites() -> bool:
    """
    Check if prerequisites are met for testing.
    
    Returns:
        True if prerequisites are met
    """
    import subprocess
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 10):
        return False
    
    # Check if tapps-agents is available
    cli_cmd = get_cli_command()
    try:
        result = subprocess.run(
            cli_cmd + ["--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

