#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

# Fix Windows encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_step(step_num: int, text: str):
    """Print a formatted step."""
    print(f"\n[Step {step_num}] {text}")
    print("-" * 70)


def get_cli_command() -> list[str]:
    """Get the CLI command, using module invocation as fallback."""
    # Try direct command first
    try:
        result = subprocess.run(["tapps-agents", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return ["tapps-agents"]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Fallback to module invocation
    return [sys.executable, "-m", "tapps_agents.cli"]


def run_command(cmd: list[str], check: bool = True, stream: bool = False) -> subprocess.CompletedProcess:
    """Run a shell command."""
    print(f"Running: {' '.join(cmd)}")
    if stream:
        # Stream output in real-time for workflows (shows progress indicators)
        # Use unbuffered output to see progress immediately
        env = os.environ.copy()
        if sys.platform == 'win32':
            # Windows: ensure UTF-8 encoding
            env['PYTHONIOENCODING'] = 'utf-8'
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                       text=True, bufsize=1, universal_newlines=True, env=env,
                                       encoding='utf-8', errors='replace')
        else:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                       text=True, bufsize=1, universal_newlines=True, env=env)
        output_lines = []
        try:
            for line in process.stdout:
                print(line, end='', flush=True)
                output_lines.append(line)
        except Exception as e:
            print(f"\n[WARNING] Error reading output: {e}")
        process.wait()
        return subprocess.CompletedProcess(cmd, process.returncode, ''.join(output_lines), '')
    else:
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
        print("[X] Python 3.13+ required")
        print(f"   Current version: {python_version.major}.{python_version.minor}")
        return False
    print(f"[OK] Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check if tapps-agents is installed (try both CLI and module)
    cli_cmd = get_cli_command()
    result = run_command(cli_cmd + ["--version"], check=False)
    if result.returncode == 0:
        print("[OK] TappsCodingAgents installed")
        if cli_cmd[0] != "tapps-agents":
            print("   (Using module invocation: python -m tapps_agents.cli)")
    else:
        print("[X] TappsCodingAgents not found")
        print("   Install with: pip install -e .")
        return False
    
    return True


def create_demo_project(demo_dir: Path) -> Path:
    """Create a demo project directory."""
    if demo_dir.exists():
        print(f"\n{demo_dir} already exists. Removing it for fresh demo...")
        shutil.rmtree(demo_dir)
    
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
    print(f"[OK] Created {calculator_file}")
    
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
    print(f"[OK] Created {api_file}")


def demo_code_scoring(demo_dir: Path):
    """Demonstrate code scoring."""
    print_step(3, "Code Scoring Demo")
    
    calculator_file = demo_dir / "src" / "calculator.py"
    
    print("\nRunning code scoring on calculator.py...")
    print("This shows objective quality metrics (5 dimensions).\n")
    
    cli_cmd = get_cli_command()
    result = run_command(
        cli_cmd + ["score", str(calculator_file)],
        check=False
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def demo_code_review(demo_dir: Path):
    """Demonstrate code review."""
    print_step(4, "Code Review Demo")
    
    calculator_file = demo_dir / "src" / "calculator.py"
    
    print("\nRunning full code review...")
    print("This provides detailed feedback with specific issues.\n")
    
    cli_cmd = get_cli_command()
    result = run_command(
        cli_cmd + ["reviewer", "review", str(calculator_file)],
        check=False
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def demo_quality_tools(demo_dir: Path):
    """Demonstrate quality tools."""
    print_step(5, "Quality Tools Demo")
    
    cli_cmd = get_cli_command()
    
    print("\nRunning linting (Ruff)...")
    result = run_command(
        cli_cmd + ["reviewer", "lint", str(demo_dir / "src")],
        check=False
    )
    print(result.stdout)
    
    print("\nRunning type checking (mypy)...")
    result = run_command(
        cli_cmd + ["reviewer", "type-check", str(demo_dir / "src")],
        check=False
    )
    print(result.stdout)


def demo_workflow_execution(demo_dir: Path):
    """Demonstrate YAML workflow execution with progress indicators."""
    print_step(6, "YAML Workflow Execution Demo")
    
    print("\nRunning a YAML workflow (rapid-dev) to demonstrate:")
    print("  - Multi-agent orchestration")
    print("  - Step-by-step progress tracking")
    print("  - Quality gates and artifact generation")
    print("  - YAML workflow definition (workflows/presets/rapid-dev.yaml)")
    print("\nMode: Headless (direct execution with terminal progress indicators)")
    print("Note: To use Cursor Skills, set TAPPS_AGENTS_MODE=cursor or use --cursor-mode flag\n")
    
    cli_cmd = get_cli_command()
    
    # Run workflow with a simple prompt
    prompt = "Create a simple greeting function that takes a name and returns a personalized greeting"
    
    print(f"Workflow: rapid-dev")
    print(f"Prompt: {prompt}")
    print("\n[WORKFLOW STARTING]")
    print("=" * 70)
    
    # Stream output in real-time to show progress indicators
    result = run_command(
        cli_cmd + ["workflow", "rapid", "--prompt", prompt],
        check=False,
        stream=True  # Stream output to see progress indicators in real-time
    )
    
    print("\n[WORKFLOW COMPLETE]")
    print("=" * 70)
    
    # Check if workflow artifacts were created
    artifacts_dir = demo_dir / "stories"
    src_dir = demo_dir / "src"
    tests_dir = demo_dir / "tests"
    
    if artifacts_dir.exists():
        print(f"\n✓ User stories created: {artifacts_dir}")
    if src_dir.exists():
        print(f"✓ Source code created: {src_dir}")
    if tests_dir.exists():
        print(f"✓ Tests created: {tests_dir}")


def main():
    """Main demo function."""
    # Save original working directory
    original_cwd = Path.cwd()
    
    try:
        print_header("TappsCodingAgents Interactive Demo")
        
        print("""
This demo will show you:
  1. Code scoring with objective metrics
  2. Code review with detailed feedback
  3. Quality tools (linting, type checking)
  4. YAML workflow execution with progress indicators
  5. Multi-agent orchestration

Let's get started!
""")
        
        # Check prerequisites
        if not check_prerequisites():
            print("\n[X] Prerequisites not met. Please install required components.")
            sys.exit(1)
        
        # Create demo project
        demo_dir = original_cwd / "demo_output"
        print_step(1, "Creating Demo Project")
        demo_dir = create_demo_project(demo_dir)
        os.chdir(demo_dir)
        print(f"[OK] Demo project created at: {demo_dir}")
        
        # Initialize project
        print("\nInitializing TappsCodingAgents project...")
        cli_cmd = get_cli_command()
        run_command(cli_cmd + ["init"], check=False)
        
        # Create sample code
        create_sample_code(demo_dir)
        
        # Run demos
        demo_code_scoring(demo_dir)
        
        print("\nContinuing to code review demo...\n")
        demo_code_review(demo_dir)
        
        print("\nContinuing to quality tools demo...\n")
        demo_quality_tools(demo_dir)
        
        print("\nContinuing to YAML workflow execution demo...\n")
        demo_workflow_execution(demo_dir)
        
        # Wrap up
        print_header("Demo Complete!")
        
        cli_example = "tapps-agents" if get_cli_command()[0] == "tapps-agents" else "python -m tapps_agents.cli"
        
        print(f"""
Demo project created at: {demo_dir}

Next steps:
  1. Explore the generated code in {demo_dir}/src/
  2. Try running more commands:
     - {cli_example} reviewer report . json markdown html
     - {cli_example} tester test src/calculator.py
     - {cli_example} workflow rapid --prompt "Add feature X"
  
  3. Read the full demo plan: {original_cwd}/docs/DEMO_PLAN.md
  4. Check out the documentation: {original_cwd}/docs/
  
Thank you for trying TappsCodingAgents!
""")
    finally:
        # Restore original working directory
        os.chdir(original_cwd)


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

