#!/usr/bin/env python3
"""
TappsCodingAgents Interactive Demo Script

This script guides users through a hands-on demo of TappsCodingAgents.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_step(step_num: int, text: str):
    """Print a formatted step."""
    print(f"\n[Step {step_num}] {text}")
    print("-" * 70)


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def check_prerequisites() -> bool:
    """Check if prerequisites are met."""
    print_header("Checking Prerequisites")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 13):
        print("❌ Python 3.13+ required")
        print(f"   Current version: {python_version.major}.{python_version.minor}")
        return False
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check if tapps-agents is installed
    try:
        result = run_command(["tapps-agents", "--version"], check=False)
        if result.returncode == 0:
            print("✅ TappsCodingAgents installed")
        else:
            print("❌ TappsCodingAgents not found")
            print("   Install with: pip install -e .")
            return False
    except FileNotFoundError:
        print("❌ TappsCodingAgents CLI not found")
        print("   Install with: pip install -e .")
        return False
    
    return True


def create_demo_project(demo_dir: Path) -> Path:
    """Create a demo project directory."""
    if demo_dir.exists():
        response = input(f"\n{demo_dir} already exists. Remove it? (y/n): ")
        if response.lower() == 'y':
            shutil.rmtree(demo_dir)
        else:
            print("Using existing directory")
    
    demo_dir.mkdir(exist_ok=True)
    return demo_dir


def create_sample_code(demo_dir: Path):
    """Create sample code files for demo."""
    print_step(2, "Creating Sample Code Files")
    
    sample_code_dir = demo_dir / "src"
    sample_code_dir.mkdir(exist_ok=True)
    
    # Create calculator.py with intentional issues
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
    
    calculator_file = sample_code_dir / "calculator.py"
    calculator_file.write_text(calculator_code)
    print(f"✅ Created {calculator_file}")
    
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
    
    api_file = sample_code_dir / "api.py"
    api_file.write_text(api_code)
    print(f"✅ Created {api_file}")


def demo_code_scoring(demo_dir: Path):
    """Demonstrate code scoring."""
    print_step(3, "Code Scoring Demo")
    
    calculator_file = demo_dir / "src" / "calculator.py"
    
    print("\nRunning code scoring on calculator.py...")
    print("This shows objective quality metrics (5 dimensions).\n")
    
    result = run_command([
        "tapps-agents", "score", str(calculator_file)
    ], check=False)
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def demo_code_review(demo_dir: Path):
    """Demonstrate code review."""
    print_step(4, "Code Review Demo")
    
    calculator_file = demo_dir / "src" / "calculator.py"
    
    print("\nRunning full code review...")
    print("This provides detailed feedback with specific issues.\n")
    
    result = run_command([
        "tapps-agents", "reviewer", "review", str(calculator_file)
    ], check=False)
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def demo_quality_tools(demo_dir: Path):
    """Demonstrate quality tools."""
    print_step(5, "Quality Tools Demo")
    
    print("\nRunning linting (Ruff)...")
    result = run_command([
        "tapps-agents", "reviewer", "lint", str(demo_dir / "src")
    ], check=False)
    print(result.stdout)
    
    print("\nRunning type checking (mypy)...")
    result = run_command([
        "tapps-agents", "reviewer", "type-check", str(demo_dir / "src")
    ], check=False)
    print(result.stdout)


def demo_code_generation(demo_dir: Path):
    """Demonstrate code generation."""
    print_step(6, "Code Generation Demo")
    
    print("\nThis would demonstrate code generation using Simple Mode.")
    print("In a real demo, you would run:")
    print("  tapps-agents simple-mode build -p 'Create a REST API endpoint'")
    print("\nNote: This requires Cursor IDE with Skills configured.")


def main():
    """Main demo function."""
    print_header("TappsCodingAgents Interactive Demo")
    
    print("""
This demo will show you:
  1. Code scoring with objective metrics
  2. Code review with detailed feedback
  3. Quality tools (linting, type checking)
  4. Code generation (if Cursor IDE available)

Let's get started!
""")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install required components.")
        sys.exit(1)
    
    # Create demo project
    demo_dir = Path.cwd() / "demo_output"
    print_step(1, "Creating Demo Project")
    demo_dir = create_demo_project(demo_dir)
    os.chdir(demo_dir)
    print(f"✅ Demo project created at: {demo_dir}")
    
    # Initialize project
    print("\nInitializing TappsCodingAgents project...")
    run_command(["tapps-agents", "init"], check=False)
    
    # Create sample code
    create_sample_code(demo_dir)
    
    # Run demos
    demo_code_scoring(demo_dir)
    
    input("\nPress Enter to continue to code review demo...")
    demo_code_review(demo_dir)
    
    input("\nPress Enter to continue to quality tools demo...")
    demo_quality_tools(demo_dir)
    
    # Wrap up
    print_header("Demo Complete!")
    
    print(f"""
Demo project created at: {demo_dir}

Next steps:
  1. Explore the generated code in {demo_dir}/src/
  2. Try running more commands:
     - tapps-agents reviewer report . json markdown html
     - tapps-agents tester test src/calculator.py
     - tapps-agents workflow rapid --prompt "Add feature X"
  
  3. Read the full demo plan: docs/DEMO_PLAN.md
  4. Check out the documentation: docs/
  
Thank you for trying TappsCodingAgents!
""")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

