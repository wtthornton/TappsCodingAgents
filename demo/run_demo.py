#!/usr/bin/env python3
"""
TappsCodingAgents Interactive Demo Script

This script guides users through a hands-on demo of TappsCodingAgents.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

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


def create_html_demo_page(demo_dir: Path):
    """Create a modern dark-themed feature-rich HTML page."""
    print_step(6, "Creating Modern HTML Demo Page")
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TappsCodingAgents Demo - Modern Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg-primary: #0a0e27;
            --bg-secondary: #151932;
            --bg-tertiary: #1e2447;
            --accent-primary: #6366f1;
            --accent-secondary: #8b5cf6;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --border: #2d3748;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        header {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
            padding: 2rem 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }

        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }

        .badge {
            display: inline-block;
            padding: 0.5rem 1rem;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        .badge.success {
            background: rgba(16, 185, 129, 0.1);
            border-color: var(--success);
            color: var(--success);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.5rem;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(99, 102, 241, 0.2);
            border-color: var(--accent-primary);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
        }

        .card-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            border-radius: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }

        .stat {
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-primary);
            margin: 0.5rem 0;
        }

        .stat-label {
            color: var(--text-secondary);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 1rem;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        .feature-list {
            list-style: none;
        }

        .feature-list li {
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .feature-list li:last-child {
            border-bottom: none;
        }

        .feature-list li::before {
            content: "✓";
            color: var(--success);
            font-weight: bold;
            font-size: 1.25rem;
        }

        .code-block {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            padding: 1rem;
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
            overflow-x: auto;
            margin-top: 1rem;
        }

        .code-block code {
            color: var(--text-primary);
        }

        .button {
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            color: white;
            border: none;
            border-radius: 0.5rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            text-decoration: none;
        }

        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        }

        .button-secondary {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
        }

        .button-secondary:hover {
            background: var(--bg-secondary);
        }

        .tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid var(--border);
        }

        .tab {
            padding: 0.75rem 1.5rem;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s ease;
        }

        .tab.active {
            color: var(--accent-primary);
            border-bottom-color: var(--accent-primary);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .chart-container {
            height: 200px;
            display: flex;
            align-items: flex-end;
            gap: 0.5rem;
            margin-top: 1rem;
        }

        .chart-bar {
            flex: 1;
            background: linear-gradient(180deg, var(--accent-primary), var(--accent-secondary));
            border-radius: 4px 4px 0 0;
            min-height: 20px;
            transition: height 0.3s ease;
            position: relative;
        }

        .chart-bar:hover {
            opacity: 0.8;
        }

        .chart-bar::after {
            content: attr(data-value);
            position: absolute;
            top: -20px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.75rem;
            color: var(--text-secondary);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .chart-bar:hover::after {
            opacity: 1;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .pulse {
            animation: pulse 2s ease-in-out infinite;
        }

        footer {
            margin-top: 4rem;
            padding: 2rem 0;
            border-top: 1px solid var(--border);
            text-align: center;
            color: var(--text-muted);
        }

        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
            
            h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="header-content">
                <div>
                    <h1>🚀 TappsCodingAgents</h1>
                    <p style="color: var(--text-secondary); margin-top: 0.5rem;">Modern AI-Powered Development Framework</p>
                </div>
                <div>
                    <span class="badge success">Demo Mode</span>
                    <span class="badge">v2.0.7</span>
                </div>
            </div>
        </div>
    </header>

    <div class="container">
        <!-- Stats Overview -->
        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Code Quality Score</div>
                    <div class="card-icon">📊</div>
                </div>
                <div class="stat">86.2</div>
                <div class="stat-label">Overall Score</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 86.2%"></div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">Security</div>
                    <div class="card-icon">🔒</div>
                </div>
                <div class="stat">9.3</div>
                <div class="stat-label">Security Score</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 93%"></div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">Maintainability</div>
                    <div class="card-icon">🛠️</div>
                </div>
                <div class="stat">9.0</div>
                <div class="stat-label">Maintainability Score</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 90%"></div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">Test Coverage</div>
                    <div class="card-icon">✅</div>
                </div>
                <div class="stat">5.0</div>
                <div class="stat-label">Coverage Score</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 50%"></div>
                </div>
            </div>
        </div>

        <!-- Features Section -->
        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Key Features</div>
                    <div class="card-icon">⭐</div>
                </div>
                <ul class="feature-list">
                    <li>YAML Workflow Definitions</li>
                    <li>Cursor Skills Integration</li>
                    <li>13 Specialized Agents</li>
                    <li>Auto-generated Artifacts</li>
                    <li>Quality Gates & Scoring</li>
                    <li>Multi-agent Orchestration</li>
                </ul>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">Workflow Metrics</div>
                    <div class="card-icon">📈</div>
                </div>
                <div class="chart-container">
                    <div class="chart-bar" style="height: 86%" data-value="86%"></div>
                    <div class="chart-bar" style="height: 93%" data-value="93%"></div>
                    <div class="chart-bar" style="height: 90%" data-value="90%"></div>
                    <div class="chart-bar" style="height: 50%" data-value="50%"></div>
                    <div class="chart-bar" style="height: 100%" data-value="100%"></div>
                </div>
                <p style="color: var(--text-secondary); margin-top: 1rem; font-size: 0.875rem;">
                    Quality metrics across different dimensions
                </p>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">Quick Actions</div>
                    <div class="card-icon">⚡</div>
                </div>
                <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                    <a href="#" class="button" onclick="alert('Run: tapps-agents workflow rapid --prompt \\'Your feature\\'')">Run Workflow</a>
                    <a href="#" class="button button-secondary" onclick="alert('Run: tapps-agents reviewer review src/')">Review Code</a>
                    <a href="#" class="button button-secondary" onclick="alert('Run: tapps-agents tester test src/')">Generate Tests</a>
                </div>
            </div>
        </div>

        <!-- Code Example -->
        <div class="card" style="margin-bottom: 2rem;">
            <div class="card-header">
                <div class="card-title">YAML Workflow Example</div>
                <div class="card-icon">📝</div>
            </div>
            <div class="tabs">
                <button class="tab active" onclick="switchTab(event, 'yaml')">YAML</button>
                <button class="tab" onclick="switchTab(event, 'cursor')">Cursor Skills</button>
                <button class="tab" onclick="switchTab(event, 'cli')">CLI</button>
            </div>
            <div id="yaml" class="tab-content active">
                <div class="code-block">
<code>workflow:
  id: rapid-dev
  name: "Rapid Development"
  steps:
    - id: planning
      agent: planner
      action: create_stories
      requires: []
      creates:
        - stories/
    - id: implementation
      agent: implementer
      action: write_code
      requires:
        - stories/
      creates:
        - src/</code>
                </div>
            </div>
            <div id="cursor" class="tab-content">
                <div class="code-block">
<code># In Cursor IDE chat:
@orchestrator *workflow rapid --prompt "Add feature X"
@reviewer *review src/calculator.py
@implementer *implement "Add feature" src/feature.py</code>
                </div>
            </div>
            <div id="cli" class="tab-content">
                <div class="code-block">
<code># Command line:
tapps-agents workflow rapid --prompt "Add feature X"
tapps-agents reviewer review src/calculator.py
tapps-agents tester test src/calculator.py</code>
                </div>
            </div>
        </div>
    </div>

    <footer>
        <p>Generated by TappsCodingAgents Demo | <a href="#" style="color: var(--accent-primary);">View Documentation</a></p>
    </footer>

    <script>
        function switchTab(event, tabId) {
            // Remove active class from all tabs and contents
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            event.target.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        }

        // Animate progress bars on load
        window.addEventListener('load', () => {
            document.querySelectorAll('.progress-fill').forEach(bar => {
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = width;
                }, 100);
            });

            // Animate chart bars
            document.querySelectorAll('.chart-bar').forEach((bar, index) => {
                const height = bar.style.height;
                bar.style.height = '0%';
                setTimeout(() => {
                    bar.style.height = height;
                }, 200 + (index * 100));
            });
        });

        // Add pulse animation to stats
        setInterval(() => {
            document.querySelectorAll('.stat').forEach(stat => {
                stat.classList.add('pulse');
                setTimeout(() => stat.classList.remove('pulse'), 2000);
            });
        }, 5000);
    </script>
</body>
</html>'''
    
    html_file = demo_dir / "demo-dashboard.html"
    html_file.write_text(html_content, encoding='utf-8')
    print(f"[OK] Created modern HTML dashboard: {html_file}")
    print(f"     Open in browser: file://{html_file.absolute()}")
    
    return html_file


def demo_workflow_execution(demo_dir: Path):
    """Demonstrate YAML workflow execution with Cursor Skills."""
    print_step(6, "YAML Workflow Execution Demo (Cursor + YAML)")
    
    print("\n" + "=" * 70)
    print("YAML WORKFLOWS: Single Source of Truth")
    print("=" * 70)
    print("\nTappsCodingAgents uses YAML files to define workflows.")
    print("Each workflow is a YAML file in workflows/presets/")
    print("Steps execute via Cursor Skills (@planner, @implementer, @reviewer, etc.)")
    print("\n" + "-" * 70)
    
    # Show YAML workflow file
    workflow_file = Path("workflows/presets/rapid-dev.yaml")
    if workflow_file.exists():
        print(f"\n📄 YAML Workflow File: {workflow_file}")
        print("\nShowing first 30 lines of the YAML workflow:")
        print("-" * 70)
        with open(workflow_file, encoding='utf-8') as f:
            lines = f.readlines()[:30]
            for line in lines:
                print(line.rstrip())
        print("... (truncated)")
        print("-" * 70)
    
    print("\nRunning YAML workflow (rapid-dev) to demonstrate:")
    print("  ✅ YAML workflow definition (workflows/presets/rapid-dev.yaml)")
    print("  ✅ Cursor Skills integration (@planner, @implementer, @reviewer)")
    print("  ✅ Multi-agent orchestration")
    print("  ✅ Step-by-step progress tracking")
    print("  ✅ Quality gates and artifact generation")
    print("  ✅ Auto-generated task manifests from YAML state")
    
    print("\n" + "=" * 70)
    print("EXECUTION MODES")
    print("=" * 70)
    print("\n1. Cursor Mode (Recommended):")
    print("   - Uses Cursor Skills for LLM operations")
    print("   - Set TAPPS_AGENTS_MODE=cursor or use --cursor-mode flag")
    print("   - Or use in Cursor IDE: @orchestrator *workflow rapid --prompt '...'")
    print("\n2. Headless Mode (CLI only):")
    print("   - Direct execution with terminal progress indicators")
    print("   - Uses framework's LLM (if configured)")
    print("\n" + "-" * 70)
    
    cli_cmd = get_cli_command()
    
    # Run workflow with a simple prompt
    prompt = "Create a simple greeting function that takes a name and returns a personalized greeting"
    
    print("\n🚀 Executing YAML Workflow:")
    print("   Workflow: rapid-dev (from workflows/presets/rapid-dev.yaml)")
    print(f"   Prompt: {prompt}")
    print("   Mode: Headless (use --cursor-mode for Cursor Skills)")
    print("\n[WORKFLOW STARTING]")
    print("=" * 70)
    
    # Stream output in real-time to show progress indicators
    run_command(
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
    workflow_state_dir = demo_dir / ".tapps-agents" / "workflow-state"
    
    print("\n📦 Generated Artifacts (from YAML workflow):")
    if artifacts_dir.exists():
        print(f"  ✓ User stories: {artifacts_dir}")
    if src_dir.exists():
        print(f"  ✓ Source code: {src_dir}")
    if tests_dir.exists():
        print(f"  ✓ Tests: {tests_dir}")
    if workflow_state_dir.exists():
        print(f"  ✓ Workflow state: {workflow_state_dir}")
        # Check for task manifest
        for state_dir in workflow_state_dir.iterdir():
            manifest_file = state_dir / "task-manifest.md"
            if manifest_file.exists():
                print(f"  ✓ Task manifest (auto-generated from YAML): {manifest_file}")
    
    print("\n💡 To use with Cursor Skills:")
    print("   1. Open Cursor IDE")
    print("   2. Use: @orchestrator *workflow rapid --prompt 'Your prompt'")
    print("   3. Or: tapps-agents workflow rapid --prompt 'Your prompt' --cursor-mode")


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
  4. Modern HTML dashboard generation
  5. YAML workflow execution (Cursor + YAML)
  6. Multi-agent orchestration via Cursor Skills

Key Concepts:
  ✅ YAML workflows are the single source of truth
  ✅ Cursor Skills execute workflow steps (@planner, @implementer, etc.)
  ✅ Framework reads YAML, Cursor handles LLM operations
  ✅ All artifacts auto-generated from YAML workflow state

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
        
        print("\nContinuing to HTML dashboard generation...\n")
        html_file = create_html_demo_page(demo_dir)
        
        print("\nContinuing to YAML workflow execution demo...\n")
        demo_workflow_execution(demo_dir)
        
        # Wrap up
        print_header("Demo Complete!")
        
        cli_example = "tapps-agents" if get_cli_command()[0] == "tapps-agents" else "python -m tapps_agents.cli"
        
        print(f"""
Demo project created at: {demo_dir}

Next steps:
  1. 🌐 Open the HTML dashboard: {html_file}
     (Double-click the file or open in your browser)
  
  2. Explore the generated code in {demo_dir}/src/
     - calculator.py - Sample calculator with intentional issues
     - api.py - Task API example
  
  3. View YAML workflows: cat workflows/presets/*.yaml
  
  4. Try running more commands:
     - {cli_example} reviewer report . json markdown html
     - {cli_example} tester test src/calculator.py
     - {cli_example} workflow rapid --prompt "Add feature X" --cursor-mode
     - {cli_example} workflow full --prompt "Build microservice" --cursor-mode
  
  5. Use Cursor Skills (if in Cursor IDE):
     - @orchestrator *workflow rapid --prompt "Add feature X"
     - @reviewer *review src/calculator.py
     - @implementer *implement "Add feature" src/feature.py
  
  6. Read the full demo plan: {original_cwd}/docs/DEMO_PLAN.md
  7. Check out YAML workflow architecture: {original_cwd}/docs/YAML_WORKFLOW_ARCHITECTURE_DESIGN.md
  8. Explore Cursor Skills: {original_cwd}/docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md
  
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

